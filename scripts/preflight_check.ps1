$ErrorActionPreference = "Stop"

$root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
Set-Location $root

if (-not (Test-Path ".env")) {
  throw ".env がありません。.env.example をコピーしてください。"
}

$envValues = @{}
Get-Content ".env" | ForEach-Object {
  if ($_ -match "^\s*#") { return }
  if ($_ -match "^\s*$") { return }
  $parts = $_.Split("=", 2)
  if ($parts.Length -eq 2) { $envValues[$parts[0].Trim()] = $parts[1].Trim() }
}

$servicePath = $envValues["FIREBASE_SERVICE_ACCOUNT_PATH"]
if (-not $servicePath) { $servicePath = "./service-account.json" }

if (-not (Test-Path $servicePath)) {
  throw "FIREBASE_SERVICE_ACCOUNT_PATH が見つかりません: $servicePath"
}
Write-Host "Preflight OK: service account file is present."
