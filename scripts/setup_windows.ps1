$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Creating virtual environment..."
if (-not (Test-Path ".venv")) {
    py -3.13 -m venv .venv
}
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Pip = Join-Path $Root ".venv\Scripts\pip.exe"

Write-Host "Upgrading packaging tools..."
& $Python -m pip install --upgrade pip setuptools wheel
Write-Host "Installing base application and developer/test dependencies..."
& $Pip install -e ".[dev]"
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}
Write-Host ""
Write-Host "Setup complete. Activate with:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "Then install your selected OCR backend as described in README.md."
