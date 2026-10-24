# OpenPDF Intelligence

Open-source, local-first PDF utilities with Chandra OCR 2, a Streamlit UI, and a FastAPI service.

> **Model notice:** This repository does not bundle model weights. Chandra OCR 2 is downloaded separately when configured. Review the model's current license and usage restrictions before use, especially commercial use. See [MODEL-LICENSE-NOTICE.md](MODEL-LICENSE-NOTICE.md).

## Features in this starter scaffold

- Native text extraction from digital PDFs.
- OCR of PDF pages using Chandra via Hugging Face Transformers or a vLLM inference server.
- Exports OCR results to Markdown, HTML, JSON, and TXT.
- Merge, split, rotate, reorder, and extract PDF pages.
- Browser UI (Streamlit) and REST API (FastAPI).
- Environment-based configuration, basic validation, tests, and Windows scripts.
- Original files are not modified in-place by the application.

This is an initial scaffold, not a production-hardened document management system. OCR output is model-generated and should be reviewed for accuracy. HTML export wraps OCR Markdown as escaped text; it does not claim to reproduce original visual layout. Searchable-PDF generation and visual editing are future work.

## Requirements

- Python 3.11 recommended.
- Windows 10/11, Linux, or macOS.
- For local Hugging Face inference: a compatible PyTorch installation and sufficient RAM/VRAM. Chandra OCR 2 is a large model; check the model card and your hardware before downloading.
- For vLLM: a separately running compatible vLLM/Chandra server. vLLM support and hardware availability vary by platform.

## Quick start (Windows PowerShell)

```powershell
# From the extracted project folder
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_windows.ps1
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
```

Install the desired OCR backend dependencies:

```powershell
# Hugging Face backend (PyTorch installation can be hardware-specific)
pip install -e ".[hf]"

# Or vLLM client adapter only; run the vLLM server separately
pip install -e ".[vllm]"
```

Install both optional groups if you want to switch between them. Follow the official PyTorch installation selector for a CUDA-specific build where appropriate.

## Run the application

Terminal 1 — API:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn openpdf.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2 — UI:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app\streamlit_app.py
```

Open Streamlit at `http://localhost:8501` and API docs at `http://127.0.0.1:8000/docs`.

## Configure OCR

Edit `.env`:

```dotenv
OPENPDF_OCR_BACKEND=hf
OPENPDF_MODEL_ID=datalab-to/chandra-ocr-2
OPENPDF_VLLM_API_BASE=http://127.0.0.1:8001/v1
OPENPDF_VLLM_MODEL_NAME=datalab-to/chandra-ocr-2
OPENPDF_MAX_PDF_MB=100
OPENPDF_RENDER_DPI=144
```

For vLLM, set `OPENPDF_OCR_BACKEND=vllm` and configure the API base/model name for your server. Start and test the server independently before OCR requests. The adapter uses Chandra's documented `InferenceManager` interface for both methods.

## API examples

Health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Extract native PDF text:

```powershell
curl.exe -F "file=@sample.pdf" http://127.0.0.1:8000/pdf/extract-text
```

OCR a PDF and get a ZIP containing per-page and combined Markdown/HTML/JSON/TXT:

```powershell
curl.exe -X POST -F "file=@sample.pdf" http://127.0.0.1:8000/ocr/export -o ocr-results.zip
```

Merge PDFs (multipart field `files`, repeated):

```powershell
curl.exe -X POST -F "files=@one.pdf" -F "files=@two.pdf" `
  "http://127.0.0.1:8000/pdf/merge" -o merged.pdf
```

Split/extract selected 1-based pages:

```powershell
curl.exe -X POST -F "file=@sample.pdf" -F "pages=1,3-5" `
  "http://127.0.0.1:8000/pdf/extract-pages" -o extracted.pdf
```

## Tests

```powershell
pip install -e ".[dev]"
pytest
```

Tests cover core PDF utilities and export serialization without downloading the model.

## Repository map

```text
app/streamlit_app.py         Streamlit browser UI
openpdf/api/main.py          FastAPI routes
openpdf/core/pdf_ops.py      PDF extraction/manipulation
openpdf/core/exports.py      OCR output serialization
openpdf/ocr/chandra.py       Chandra backend adapter
openpdf/config.py            Environment configuration
tests/                       Model-free tests
scripts/                      Windows setup and launch helpers
```

## Safety and limitations

- The API binds to loopback by default in the provided commands. Do not expose it publicly without authentication, authorization, rate limits, upload limits, and hardened deployment settings.
- PDFs are untrusted inputs. Keep dependencies patched and use a restricted environment for hostile files.
- Password-protected/encrypted PDFs are not handled unless unlocked before upload.
- PDF modification features are structural page operations, not arbitrary editing of existing text in place.
- Redaction is not implemented in this starter; do not use overlays to conceal confidential content.
- OCR may hallucinate, omit, or misread content. Verify critical results against the source.
- Do not upload confidential documents to a remote inference server unless you control and trust that server.
