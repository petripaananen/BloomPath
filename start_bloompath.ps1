$env:PYTHONIOENCODING = 'utf-8'
$env:LINEAR_WEBHOOK_SECRET = 'lin_wh_959a1bcba7897e5c6f2a621ad2f42ee8a0da0c16fad0'
$env:LINEAR_API_KEY = 'lin_api_X43vEYPTCxCdLCYIlLlHyRe9TT514qEJCDAy4nsw'
$env:LINEAR_TEAM_ID = '309b158e-1d2e-4722-bddc-e8b1c7f8b1f9'
$env:DEFAULT_PROVIDER = 'linear'

Write-Host "Starting BloomPath Middleware..." -ForegroundColor Green
Write-Host "Ensure ngrok is running in a separate window: ngrok http 5005" -ForegroundColor Yellow

$env:PORT = "5005"
$env:DEBUG = "true"
python -m middleware.app
