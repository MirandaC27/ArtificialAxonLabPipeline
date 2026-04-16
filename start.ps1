$ErrorActionPreference = "Stop"

$env:AXONLAB_API_URL = "http://127.0.0.1:8001"

docker compose up -d --build

Start-Sleep -Seconds 5

python -m frontend.tkinter_app
