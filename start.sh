#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export AXONLAB_API_URL="http://127.0.0.1:8000"

echo "Checking local Tkinter frontend dependencies..."
if python -c "import requests"; then
    echo "Frontend dependencies are already installed."
else
    echo "Installing the requests package..."
    python -m pip install requests
fi

docker compose up -d --build

python -c "import time, requests
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

python ./frontend/main_view.py