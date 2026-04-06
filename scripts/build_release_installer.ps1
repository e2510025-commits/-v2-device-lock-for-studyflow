$ErrorActionPreference = "Stop"

param(
  [Parameter(Mandatory = $false)]
  [string]$Version = "0.2.0"
)

$env:APP_VERSION = $Version

Write-Host "Installing dependencies..."
python -m pip install -r requirements.txt
python -m pip install pyinstaller

Write-Host "Building one-file executable..."
pyinstaller --onefile --windowed --name studyflow-lock main.py

$inno = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $inno)) {
  throw "Inno Setup 6 not found. Please install from https://jrsoftware.org/isdl.php"
}

Write-Host "Building installer..."
& $inno "installer\StudyFlowLock.iss"

Write-Host "Done: dist\StudyFlow-Lock-Setup.exe"
