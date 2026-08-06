#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export AXONLAB_API_URL="http://127.0.0.1:8000"

if [ ! -x ".venv/bin/python" ]; then
    echo "Creating project virtual environment in .venv..."
    if command -v python3 >/dev/null 2>&1; then
        python3 -m venv .venv
    else
        python -m venv .venv
    fi
fi
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

echo "Checking local Tkinter frontend dependencies..."
if "$VENV_PYTHON" -c "import requests"; then
    echo "Frontend dependencies are already installed."
else
    echo "Installing the requests package in .venv..."
    "$VENV_PYTHON" -m pip install requests
fi

docker compose up -d --build

"$VENV_PYTHON" -c "import time, requests
url = '$AXONLAB_API_URL/'
for attempt in range(30):
    try:
        response = requests.get(url, timeout=2)
        response.raise_for_status()
        break
    except requests.RequestException:
        if attempt == 29:
            raise SystemExit('FastAPI did not become ready within 60 seconds.')
        time.sleep(2)"

"$VENV_PYTHON" ./frontend/main_view.py