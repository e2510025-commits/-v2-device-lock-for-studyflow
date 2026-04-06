$ErrorActionPreference = "Stop"

$exePath = Join-Path $PSScriptRoot "..\dist\studyflow-lock.exe"
$exePath = [System.IO.Path]::GetFullPath($exePath)

if (-not (Test-Path $exePath)) {
  throw "Executable not found: $exePath"
}

$startup = [Environment]::GetFolderPath("Startup")
$linkPath = Join-Path $startup "StudyFlow Device Lock.lnk"

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($linkPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = [System.IO.Path]::GetDirectoryName($exePath)
$shortcut.WindowStyle = 7
$shortcut.Description = "StudyFlow Device Lock"
$shortcut.Save()

Write-Host "Startup shortcut installed: $linkPath"
