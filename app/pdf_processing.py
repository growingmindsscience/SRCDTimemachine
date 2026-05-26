from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    page_text: list[str] = []

    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            page_text.append(f"\n\n--- Page {index} ---\n{text.strip()}")

    return clean_text("\n".join(page_text))


def ocr_pdf_text(pdf_path: Path, dpi: int = 300) -> str:
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "OCR dependencies are missing. Install pytesseract and pdf2image."
        ) from exc

    pages = convert_from_path(str(pdf_path), dpi=dpi)
    page_text = []
    for index, image in enumerate(pages, start=1):
        text = pytesseract.image_to_string(image)
        if text.strip():
            page_text.append(f"\n\n--- Page {index} ---\n{text.strip()}")

    return clean_text("\n".join(page_text))


def extract_or_ocr_pdf(pdf_path: Path, use_ocr: bool = False) -> tuple[str, str]:
    if not use_ocr:
        extracted_text = extract_pdf_text(pdf_path)
        if len(extracted_text.strip()) >= 200:
            return extracted_text, "embedded text"

    ocr_text = ocr_pdf_text(pdf_path)
    return ocr_text, "OCR"


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def make_summary_placeholder(text: str, max_chars: int = 900) -> str:
    clean = clean_text(text)
    if not clean:
        return "No text is available to summarize yet."

    sentences = re.split(r"(?<=[.!?])\s+", clean)
    useful_sentences = [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) > 40 and not sentence.strip().startswith("--- Page")
    ]

    if not useful_sentences:
        return clean[:max_chars]

    summary = " ".join(useful_sentences[:4])
    if len(summary) > max_chars:
        summary = summary[:max_chars].rsplit(" ", 1)[0] + "..."

    return (
        "Placeholder summary: "
        + summary
        + "\n\nFuture version: replace this with an LLM-generated historical research summary."
    )


if __name__ == "__main__":
    from app.streamlit_app import main

    main()
