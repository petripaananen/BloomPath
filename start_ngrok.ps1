# BloomPath - ngrok Tunnel Startup Script
# This script starts an ngrok tunnel for receiving Jira webhooks

Write-Host "🌱 BloomPath - Starting ngrok tunnel..." -ForegroundColor Green

# Check if ngrok is installed
$ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrokPath) {
    Write-Host "❌ ngrok is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "To install ngrok:" -ForegroundColor Yellow
    Write-Host "  1. Download from: https://ngrok.com/download"
    Write-Host "  2. Extract and add to PATH"
    Write-Host "  3. Run: ngrok config add-authtoken YOUR_TOKEN"
    Write-Host ""
    exit 1
}

$port = 5000
Write-Host "📡 Starting tunnel on port $port..." -ForegroundColor Cyan

# Start ngrok and capture output
Write-Host ""
Write-Host "================================================" -ForegroundColor Magenta
Write-Host " Copy the 'Forwarding' URL for Jira Webhook" -ForegroundColor White
Write-Host " Example: https://abc123.ngrok.io/webhook" -ForegroundColor Gray
Write-Host "================================================" -ForegroundColor Magenta
Write-Host ""

# Run ngrok (this will block and show the tunnel info)
ngrok http $port
