$ErrorActionPreference = "Stop"

Write-Host "Installing dependencies..."
python -m pip install -r requirements.txt
python -m pip install pyinstaller

Write-Host "Building one-file executable..."
pyinstaller --onefile --name studyflow-lock main.py

Write-Host "Done. Output: dist/studyflow-lock.exe"
