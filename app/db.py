from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "srcd_archive.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS manuscripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                year INTEGER,
                filename TEXT NOT NULL,
                topics TEXT,
                text_path TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS manuscript_search
            USING fts5(title, authors, year UNINDEXED, topics, body)
            """
        )


def add_manuscript(
    *,
    title: str,
    authors: str,
    year: int | None,
    filename: str,
    topics: str,
    text_path: str,
    body: str,
) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO manuscripts (title, authors, year, filename, topics, text_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, authors, year, filename, topics, text_path),
        )
        manuscript_id = cursor.lastrowid
        connection.execute(
            """
            INSERT INTO manuscript_search (rowid, title, authors, year, topics, body)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (manuscript_id, title, authors, year, topics, body),
        )
        return int(manuscript_id)


def list_manuscripts() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return list(
            connection.execute(
                """
                SELECT id, title, authors, year, filename, topics, text_path, created_at
                FROM manuscripts
                ORDER BY COALESCE(year, 9999), title
                """
            )
        )


def get_manuscript(manuscript_id: int) -> sqlite3.Row | None:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, title, authors, year, filename, topics, text_path, created_at
            FROM manuscripts
            WHERE id = ?
            """,
            (manuscript_id,),
        ).fetchone()


def search_manuscripts(query: str) -> list[sqlite3.Row]:
    normalized_query = query.strip()
    if not normalized_query:
        return list_manuscripts()

    with get_connection() as connection:
        try:
            return list(
                connection.execute(
                    """
                    SELECT m.id, m.title, m.authors, m.year, m.filename, m.topics, m.text_path,
                           snippet(manuscript_search, 4, '[', ']', '...', 24) AS snippet
                    FROM manuscript_search s
                    JOIN manuscripts m ON m.id = s.rowid
                    WHERE manuscript_search MATCH ?
                    ORDER BY bm25(manuscript_search)
                    """,
                    (normalized_query,),
                )
            )
        except sqlite3.OperationalError:
            like_query = f"%{normalized_query}%"
            return list(
                connection.execute(
                    """
                    SELECT id, title, authors, year, filename, topics, text_path, NULL AS snippet
                    FROM manuscripts
                    WHERE title LIKE ? OR authors LIKE ? OR topics LIKE ?
                    ORDER BY COALESCE(year, 9999), title
                    """,
                    (like_query, like_query, like_query),
                )
            )


def delete_manuscripts(ids: Iterable[int]) -> None:
    manuscript_ids = list(ids)
    if not manuscript_ids:
        return

    placeholders = ",".join("?" for _ in manuscript_ids)
    with get_connection() as connection:
        connection.execute(
            f"DELETE FROM manuscript_search WHERE rowid IN ({placeholders})",
            manuscript_ids,
        )
        connection.execute(
            f"DELETE FROM manuscripts WHERE id IN ({placeholders})",
            manuscript_ids,
        )
