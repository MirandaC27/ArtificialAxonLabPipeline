$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot
$env:AXONLAB_API_URL = "http://127.0.0.1:8000"

Write-Host "Installing local analysis dependencies..."
python -m pip install -r requirements.txt
python -m pip install -r requirements-analysis.txt

docker compose up -d --build

Start-Sleep -Seconds 5

python -m frontend.tkinter_app