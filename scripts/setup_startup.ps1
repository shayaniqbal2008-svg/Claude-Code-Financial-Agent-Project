# Adds the dashboard tray app to Windows Startup so it launches on login
# Run once (no admin required)

param(
    [string]$ProjectDir = (Split-Path $PSScriptRoot -Parent)
)

$PythonwPath = Join-Path (Split-Path (Get-Command python).Source -Parent) "pythonw.exe"
$TrayScript = Join-Path $ProjectDir "dashboard\tray.py"
$StartupFolder = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupFolder "FinancialAgent.lnk"

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PythonwPath
$Shortcut.Arguments = "`"$TrayScript`""
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.Description = "Financial Agent Dashboard"
$Shortcut.Save()

Write-Host "Startup shortcut created at: $ShortcutPath"
Write-Host "The dashboard will launch automatically on next login."
