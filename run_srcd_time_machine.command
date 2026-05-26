#!/bin/zsh
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt

echo ""
echo "Starting SRCD Time Machine..."
echo "Open http://localhost:8501 if your browser does not open automatically."
echo ""

python -m streamlit run app/streamlit_app.py --server.port 8501
