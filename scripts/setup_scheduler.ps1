# Registers the daily 8:00 AM CT agent run in Windows Task Scheduler
# Run once from PowerShell as Administrator

param(
    [string]$ProjectDir = (Split-Path $PSScriptRoot -Parent)
)

$PythonPath = (Get-Command python).Source
$ScriptPath = Join-Path $ProjectDir "agent\main.py"

# 8:00 AM local time (user's machine must be set to Central Time)
$Trigger = New-ScheduledTaskTrigger -Daily -At "08:00AM"

$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $ProjectDir

$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -StartWhenAvailable `
    -WakeToRun

Register-ScheduledTask `
    -TaskName "FinancialAgent-DailyRun" `
    -Trigger $Trigger `
    -Action $Action `
    -Settings $Settings `
    -Description "Financial Agent daily report at 8 AM CT" `
    -Force

Write-Host "Scheduled task registered: FinancialAgent-DailyRun at 8:00 AM daily"
Write-Host "Verify in Task Scheduler: taskschd.msc"
