$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot
$env:AXONLAB_API_URL = "http://127.0.0.1:8000"

Write-Host "Checking local Tkinter frontend dependencies..."
python -c "import requests"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing the requests package..."
    python -m pip install requests
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    Write-Host "Frontend dependencies are already installed."
}

docker compose up -d --build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Waiting for FastAPI..."
$apiReady = $false
for ($attempt = 1; $attempt -le 30; $attempt++) {
    try {
        $response = Invoke-RestMethod -Uri "$env:AXONLAB_API_URL/" -TimeoutSec 2
        if ($response.status -eq "ok") {
            $apiReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}
if (-not $apiReady) {
    throw "FastAPI did not become ready within 60 seconds. Run: docker compose logs api"
}

python .\frontend\main_view.py