from __future__ import annotations

import shutil
from pathlib import Path

import streamlit as st

from db import add_manuscript, get_manuscript, init_db, list_manuscripts, search_manuscripts
from pdf_processing import extract_or_ocr_pdf, make_summary_placeholder


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
TEXT_DIR = DATA_DIR / "texts"


def ensure_storage() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    TEXT_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(filename: str) -> str:
    keep = []
    for char in filename:
        if char.isalnum() or char in {".", "-", "_"}:
            keep.append(char)
        else:
            keep.append("_")
    return "".join(keep).strip("_") or "manuscript.pdf"


def infer_title_from_filename(filename: str) -> str:
    stem = Path(filename).stem.replace("_", " ").replace("-", " ")
    return " ".join(stem.split()).title() or "Untitled Manuscript"


def save_uploaded_file(uploaded_file) -> Path:
    target = UPLOAD_DIR / safe_filename(uploaded_file.name)
    counter = 1
    while target.exists():
        target = UPLOAD_DIR / f"{target.stem}_{counter}{target.suffix}"
        counter += 1

    with target.open("wb") as output:
        shutil.copyfileobj(uploaded_file, output)

    return target


def save_text_file(pdf_path: Path, text: str) -> Path:
    text_path = TEXT_DIR / f"{pdf_path.stem}.txt"
    counter = 1
    while text_path.exists():
        text_path = TEXT_DIR / f"{pdf_path.stem}_{counter}.txt"
        counter += 1

    text_path.write_text(text, encoding="utf-8")
    return text_path


def read_text(path: str) -> str:
    text_path = Path(path)
    if not text_path.is_absolute():
        text_path = BASE_DIR / text_path
    return text_path.read_text(encoding="utf-8")


def render_upload_tab() -> None:
    st.subheader("Upload Manuscript")
    uploaded_file = st.file_uploader("PDF manuscript", type=["pdf"])

    with st.form("metadata_form", clear_on_submit=False):
        title = st.text_input(
            "Title",
            value=infer_title_from_filename(uploaded_file.name) if uploaded_file else "",
        )
        authors = st.text_input("Authors", placeholder="e.g., John Bowlby; Mary Ainsworth")
        year = st.number_input("Year", min_value=1900, max_value=2100, value=1975)
        topics = st.text_input("Topics", placeholder="attachment, language, cognition")
        force_ocr = st.checkbox("Force OCR", help="Use this for scanned PDFs with little embedded text.")
        submitted = st.form_submit_button("Process and Save")

    if not submitted:
        return

    if uploaded_file is None:
        st.error("Upload a PDF before saving.")
        return

    if not title.strip():
        st.error("Title is required.")
        return

    pdf_path = save_uploaded_file(uploaded_file)
    with st.spinner("Extracting manuscript text..."):
        try:
            text, method = extract_or_ocr_pdf(pdf_path, use_ocr=force_ocr)
        except Exception as exc:
            st.error(f"Could not process PDF: {exc}")
            return

    if not text.strip():
        st.error("No text was extracted. Try enabling Force OCR.")
        return

    text_path = save_text_file(pdf_path, text)
    manuscript_id = add_manuscript(
        title=title.strip(),
        authors=authors.strip(),
        year=int(year) if year else None,
        filename=pdf_path.name,
        topics=topics.strip(),
        text_path=str(text_path.relative_to(BASE_DIR)),
        body=text,
    )

    st.success(f"Saved manuscript #{manuscript_id} using {method}.")
    st.caption(f"Text saved to `{text_path.relative_to(BASE_DIR)}`")


def render_search_tab() -> None:
    st.subheader("Search Archive")
    query = st.text_input("Keyword search", placeholder="e.g., attachment, temperament, Piaget")
    results = search_manuscripts(query)

    st.caption(f"{len(results)} manuscript(s) found")
    for row in results:
        with st.container(border=True):
            label_year = row["year"] if row["year"] else "Unknown year"
            st.markdown(f"**{row['title']}** ({label_year})")
            st.write(row["authors"] or "Unknown authors")
            if row["topics"]:
                st.caption(f"Topics: {row['topics']}")
            if "snippet" in row.keys() and row["snippet"]:
                st.write(row["snippet"])
            if st.button("View", key=f"view_{row['id']}"):
                st.session_state["selected_manuscript_id"] = row["id"]


def render_view_tab() -> None:
    st.subheader("View Manuscript")
    manuscripts = list_manuscripts()
    if not manuscripts:
        st.info("No manuscripts have been added yet.")
        return

    options = {f"{row['title']} ({row['year'] or 'Unknown year'})": row["id"] for row in manuscripts}
    selected_id = st.session_state.get("selected_manuscript_id", next(iter(options.values())))
    selected_label = next(
        (label for label, manuscript_id in options.items() if manuscript_id == selected_id),
        next(iter(options.keys())),
    )

    selected_label = st.selectbox("Manuscript", options.keys(), index=list(options.keys()).index(selected_label))
    manuscript = get_manuscript(options[selected_label])
    if manuscript is None:
        st.error("Selected manuscript was not found.")
        return

    text = read_text(manuscript["text_path"])

    st.markdown(f"### {manuscript['title']}")
    st.write(f"**Authors:** {manuscript['authors'] or 'Unknown'}")
    st.write(f"**Year:** {manuscript['year'] or 'Unknown'}")
    st.write(f"**Topics:** {manuscript['topics'] or 'None yet'}")
    st.write(f"**Filename:** {manuscript['filename']}")

    if st.button("Generate Placeholder Summary"):
        st.session_state[f"summary_{manuscript['id']}"] = make_summary_placeholder(text)

    summary = st.session_state.get(f"summary_{manuscript['id']}")
    if summary:
        st.info(summary)

    st.text_area("Extracted text", value=text, height=520)


def main() -> None:
    st.set_page_config(page_title="SRCD Time Machine", layout="wide")
    ensure_storage()
    init_db()

    st.title("SRCD Time Machine")
    st.caption("A local archive and AI research tool for historical developmental science manuscripts, 1968-2000.")

    upload_tab, search_tab, view_tab = st.tabs(["Upload", "Search", "View"])
    with upload_tab:
        render_upload_tab()
    with search_tab:
        render_search_tab()
    with view_tab:
        render_view_tab()


if __name__ == "__main__":
    main()
