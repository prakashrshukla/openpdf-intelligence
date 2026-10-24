$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (-not (Test-Path ".venv\Scripts\streamlit.exe")) {
    throw "Virtual environment missing. Run scripts\setup_windows.ps1 first."
}
& ".\.venv\Scripts\streamlit.exe" run app\streamlit_app.py
