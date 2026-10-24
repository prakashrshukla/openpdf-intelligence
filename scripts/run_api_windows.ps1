$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (-not (Test-Path ".venv\Scripts\uvicorn.exe")) {
    throw "Virtual environment missing. Run scripts\setup_windows.ps1 first."
}
& ".\.venv\Scripts\uvicorn.exe" openpdf.api.main:app --host 127.0.0.1 --port 8000 --reload
