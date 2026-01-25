# BloomPath - ngrok Tunnel Startup Script
# This script starts an ngrok tunnel for receiving webhooks

Write-Host "🌱 BloomPath - Starting ngrok tunnel..." -ForegroundColor Green

# Check if ngrok is installed
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Host "❌ ngrok is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

$port = 5000
Write-Host "📡 Starting tunnel on port $port..." -ForegroundColor Cyan
Write-Host "The tunnel URL will be available at http://localhost:4040/api/tunnels" -ForegroundColor Gray

# Run ngrok
ngrok http $port
