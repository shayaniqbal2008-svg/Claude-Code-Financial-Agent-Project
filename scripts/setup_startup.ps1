# Adds the dashboard tray app to Windows Startup so it launches on login
# Run once (no admin required)

param(
    [string]$ProjectDir = (Split-Path $PSScriptRoot -Parent)
)

$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) { Write-Error "python not found in PATH. Install Python and try again."; exit 1 }
$PythonwPath = Join-Path (Split-Path $PythonCmd.Source -Parent) "pythonw.exe"
if (-not (Test-Path $PythonwPath)) { Write-Error "pythonw.exe not found at $PythonwPath. Ensure Python was installed with the standard Windows installer."; exit 1 }

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
