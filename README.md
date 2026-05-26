# SRCD Time Machine

An MVP Streamlit app for building a local searchable archive of historical developmental science manuscripts.

The app can:

- Upload PDF manuscripts
- Extract embedded PDF text
- Optionally OCR scanned PDFs with Tesseract
- Save extracted text locally
- Store manuscript metadata in SQLite
- Search manuscripts by keyword
- View manuscript text
- Generate a short placeholder summary for future AI integration

## Project Structure

```text
.
├── app/
│   ├── db.py              # SQLite schema and queries
│   ├── pdf_processing.py  # PDF extraction and OCR helpers
│   └── streamlit_app.py   # Streamlit interface
├── data/
│   ├── srcd_archive.db    # Created automatically
│   ├── texts/             # Extracted manuscript text
│   └── uploads/           # Uploaded PDFs
├── packages.txt           # Linux OCR dependencies for Streamlit Cloud
├── requirements.txt
└── README.md
```

## Installation

Create a virtual environment and install Python dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For OCR of scanned PDFs, install system dependencies:

```bash
brew install tesseract poppler
```

OCR is optional. PDFs with embedded text can be processed without Tesseract.

## Run

```bash
streamlit run app/streamlit_app.py
```

On macOS, you can also double-click:

```text
run_srcd_time_machine.command
```

The first launch may take a minute because it creates the Python environment and installs dependencies.

The database and local storage folders are created automatically under `data/`.

## Deploy on Streamlit Community Cloud

This repository is ready to deploy as a Streamlit app.

1. Push this project to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Create a new app from the GitHub repository.
4. Set the main file path to:

```text
app/streamlit_app.py
```

5. Deploy the app.

`packages.txt` installs the Linux OCR dependencies needed by `pytesseract` and `pdf2image`.

Important: Streamlit Community Cloud does not guarantee permanent local file storage. This MVP is good for demos and early testing, but a production archive should move PDFs, extracted text, and metadata into durable cloud storage such as S3/R2/Supabase plus Postgres.

## Notes

The summary feature is currently a placeholder. It produces a simple extractive summary from the manuscript text so the app can be used immediately. Later, this function can be replaced with an LLM call for historical research summaries.
