#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export AXONLAB_API_URL="http://127.0.0.1:8000"

python -m pip install -r requirements.txt
python -m pip install -r requirements-analysis.txt

docker compose up -d --build

sleep 5

python -m frontend.tkinter_app