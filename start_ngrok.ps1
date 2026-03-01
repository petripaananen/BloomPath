# BloomPath - ngrok Tunnel Startup Script
# This script starts an ngrok tunnel for receiving webhooks

Write-Host "BloomPath - Starting ngrok tunnel..."
$port = 5005
Write-Host "Starting tunnel on port $port..."
Write-Host "The tunnel URL will be available at http://localhost:4040/api/tunnels"

# Run ngrok
& "C:\Users\petri\AppData\Local\Microsoft\WindowsApps\ngrok.exe" http $port
