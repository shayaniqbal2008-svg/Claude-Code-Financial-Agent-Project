# One-command setup: installs dependencies and registers automation
# Run from PowerShell after filling in .env

param(
    [string]$ProjectDir = (Split-Path $PSScriptRoot -Parent)
)

Set-Location $ProjectDir

Write-Host "=== Financial Agent Setup ===" -ForegroundColor Cyan

# 1. Install Python dependencies
Write-Host "`n[1/3] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Error "pip install failed"; exit 1 }

# 2. Register Task Scheduler
Write-Host "`n[2/3] Registering daily Task Scheduler job..." -ForegroundColor Yellow
try {
    & "$PSScriptRoot\setup_scheduler.ps1" -ProjectDir $ProjectDir
} catch {
    Write-Warning "Task Scheduler registration failed (may need to run as Administrator): $_"
}

# 3. Register startup
Write-Host "`n[3/3] Adding dashboard to Windows Startup..." -ForegroundColor Yellow
& "$PSScriptRoot\setup_startup.ps1" -ProjectDir $ProjectDir

Write-Host "`n=== Setup complete ===" -ForegroundColor Green
Write-Host "Run the dashboard now: python dashboard\tray.py"
Write-Host "Run the agent now:     python agent\main.py"
