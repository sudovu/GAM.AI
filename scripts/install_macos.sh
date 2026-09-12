#!/bin/bash
# GAM.AI macOS Installation & Launcher Script
set -e

echo "============================================================"
Echo "              GAM.AI macOS Installer & Setup                "
echo "==========================================================="

# Check for Python 3
if !command -v python3 &> /dev/null; then
  echo "[ERROR] Python 3 is required. Please install it via Homebrew: brew install python3"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_DIR"

echo "-> Creating Python virtual environment (.venv)..."
python3 -m venv .venv
source .venv/bin/activate

echo "-> Installing GAM.AI package..."
pip install --upgrade pip
pip install -e .

echo "-> Synching web and context assets..."
python3 scripts/run_tests.py

echo "\n[SUCCESS] GAM.AI successfully installed on macOS!"
echo "To launch the GAM.AI app at any time:"
echo "  source .venv/bin/activate && python3 scripts/run_app.py"
echo ""
