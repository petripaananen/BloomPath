# test_watering.ps1
# Tests the /complete_task endpoint to verify UE5 → Jira flow
# Run this AFTER starting the middleware: python middleware.py

param(
    [string]$IssueKey = "KAN-32",
    [string]$MiddlewareUrl = "http://localhost:5000"
)

Write-Host "=== BloomPath Watering Interaction Test ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "[1/3] Testing middleware health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$MiddlewareUrl/health" -Method GET -TimeoutSec 5
    Write-Host "  ✓ Middleware is running" -ForegroundColor Green
    Write-Host "    Status: $($health.status)"
    Write-Host "    Jira Configured: $($health.jira_configured)"
}
catch {
    Write-Host "  ✗ Middleware not responding!" -ForegroundColor Red
    Write-Host "    Make sure to run: python middleware.py" -ForegroundColor Gray
    exit 1
}
Write-Host ""

# Test 2: Complete Task (simulates watering a flower)
Write-Host "[2/3] Simulating watering flower for issue: $IssueKey" -ForegroundColor Yellow
$body = @{
    issue_key = $IssueKey
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "$MiddlewareUrl/complete_task" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 10
    
    if ($result.status -eq "success") {
        Write-Host "  ✓ Issue transitioned to Done!" -ForegroundColor Green
        Write-Host "    Issue: $($result.issue)"
    }
    else {
        Write-Host "  ⚠ Unexpected response:" -ForegroundColor Yellow
        Write-Host "    $($result | ConvertTo-Json)"
    }
}
catch {
    $errorResponse = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($errorResponse) {
        Write-Host "  ✗ Error: $($errorResponse.message)" -ForegroundColor Red
    }
    else {
        Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
    }
}
Write-Host ""

# Test 3: Sprint Status (for environmental dynamics)
Write-Host "[3/3] Checking sprint status (weather/time)..." -ForegroundColor Yellow
try {
    $sprint = Invoke-RestMethod -Uri "$MiddlewareUrl/sprint_status" -Method GET -TimeoutSec 5
    Write-Host "  ✓ Sprint status retrieved" -ForegroundColor Green
    Write-Host "    Weather: $($sprint.weather)"
    Write-Host "    Progress: $([math]::Round($sprint.progress * 100, 1))%"
    if ($sprint.sprint_name) {
        Write-Host "    Sprint: $($sprint.sprint_name) ($($sprint.issues_done)/$($sprint.issues_total) done)"
    }
}
catch {
    Write-Host "  ⚠ Could not get sprint status (JIRA_BOARD_ID may not be configured)" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Gray
Write-Host "  1. Create BP_WateringCan in UE5"
Write-Host "  2. Set up overlap detection on flowers"
Write-Host "  3. Add HTTP POST to /complete_task"
Write-Host ""
