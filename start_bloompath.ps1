$env:PYTHONIOENCODING = 'utf-8'
$env:DEFAULT_PROVIDER = 'linear'

if (-not (Test-Path .env)) {
    Write-Host "⚠️  Warning: .env file not found. Ensure environment variables are set." -ForegroundColor Yellow
}

Write-Host "Starting BloomPath Middleware..." -ForegroundColor Green
Write-Host "Ensure ngrok is running in a separate window: ngrok http 5005" -ForegroundColor Yellow

$env:PORT = "5005"
$env:DEBUG = "true"
python -m middleware.app
