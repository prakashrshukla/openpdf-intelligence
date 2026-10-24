# OpenPDF Intelligence

Open-source, local-first PDF utilities with Chandra OCR 2, a Streamlit user interface, and a FastAPI service.

OpenPDF Intelligence aims to provide a single application for extracting text, processing PDFs, running OCR, and exporting results in common formats, with configurable local or remote inference.

> **Model notice:** This repository does not bundle model weights. Chandra OCR 2 model files must be obtained separately. Review the model card, license, usage restrictions, and hardware requirements before use, especially for commercial applications. See [MODEL-LICENSE-NOTICE.md](MODEL-LICENSE-NOTICE.md).

## Project status

**Current stage:** Working starter application; production hardening in progress.

| Area | Current status |
|---|---|
| Streamlit UI | Application starts and the UI is accessible locally |
| FastAPI service | Running; health endpoint verified |
| PDF utilities | Core operations implemented and regression-tested |
| OCR integration | Chandra adapter implemented; full inference performance still needs validation |
| Model configuration | Local directory and Hugging Face repository sources supported for the HF backend |
| Export formats | Markdown, HTML, JSON, and TXT in a ZIP bundle |
| Automated tests | 24 tests passing at the latest verified checkpoint |
| Production readiness | In progress |
| Ollama provider | Planned; not implemented |

The project is not yet a production-hardened document management system. OCR output is model-generated and should be reviewed for accuracy. HTML export escapes OCR Markdown rather than reproducing the original page layout. Searchable-PDF generation and visual editing are future enhancements.

## Features

### PDF operations

- Extract native text from digital PDFs.
- Merge multiple PDFs.
- Extract selected pages.
- Rotate selected pages.
- Validate PDF structure and page count.
- Render PDF pages for OCR.
- Enforce configurable PDF upload-size and page-count limits.

### OCR and exports

- Chandra OCR 2 integration through the `InferenceManager` interface.
- Hugging Face Transformers inference.
- Optional vLLM server integration.
- Local model directory or Hugging Face repository configuration.
- Export OCR results as Markdown, HTML, JSON, and TXT.
- Package export artifacts into a downloadable ZIP file.
- Sequential OCR processing to avoid unnecessarily concurrent GPU inference.

### Application interfaces

- Streamlit browser UI.
- FastAPI REST endpoints.
- Interactive Swagger API documentation.
- Environment-based configuration.
- Automated regression tests.

## Architecture overview

```text
                 User / Browser
                       |
             +---------+---------+
             |                   |
        Streamlit UI         Swagger UI
             |                   |
             +---------+---------+
                       |
                    FastAPI
                       |
             +---------+---------+
             |                   |
        PDF Operations        OCR Export
             |                   |
      pypdf / PyMuPDF       Chandra Adapter
                                 |
                     +-----------+-----------+
                     |                       |
                Transformers              vLLM API
                     |                       |
                Local / HF              Model Server
                     |
                OCR Results
                     |
              Export Generator
                     |
             Markdown / HTML /
                JSON / TXT
                     |
                  ZIP File
```

The diagram represents the current logical architecture. It does not imply that the application has already implemented production-grade authentication, distributed processing, or multi-user job orchestration.

## Requirements

- Python 3.11 or newer.
- Windows 10/11, Linux, or macOS.
- Sufficient system RAM and disk space for the selected model.
- A compatible PyTorch installation for local Hugging Face inference.
- A compatible, separately running vLLM/Chandra server when using the vLLM backend.
- Network access for downloading model files when they are not already cached.

Chandra OCR 2 is a large model. Hardware compatibility, memory requirements, inference speed, and supported optimizations should be validated on the target machine before production deployment.

## Installation

### Windows PowerShell

Run from the project directory:

```powershell
cd D:\codebase\openpdf-intelligence

Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_windows.ps1

.\.venv\Scripts\Activate.ps1
```

If you are setting up a fresh checkout, create your environment file:

```powershell
Copy-Item .env.example .env
```

Install the development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Install the optional OCR dependencies:

```powershell
# Hugging Face / Transformers backend
python -m pip install -e ".[hf]"

# Or the vLLM client adapter
python -m pip install -e ".[vllm]"
```

Install both optional groups if you need to switch between the two inference backends.

For GPU inference, install a PyTorch build compatible with your CUDA environment by following the official [PyTorch installation instructions](https://pytorch.org/get-started/locally/).

## Configuration

Runtime settings are loaded from `.env` and environment variables with the `OPENPDF_` prefix.

### Option A: Use a local model directory

Use this option when the Chandra model files already exist locally.

```dotenv
OPENPDF_OCR_BACKEND=hf
OPENPDF_MODEL_SOURCE=local
OPENPDF_MODEL_ID=D:\ai_models\chandra-ocr-2
```

The configured model directory must exist and contain `config.json`. The adapter validates these requirements before initializing Chandra.

This mode avoids using a Hugging Face repository ID as the model checkpoint. It does not guarantee that every required model file is present or that inference will fit within available memory.

### Option B: Use a Hugging Face repository

```dotenv
OPENPDF_OCR_BACKEND=hf
OPENPDF_MODEL_SOURCE=huggingface
OPENPDF_MODEL_ID=datalab-to/chandra-ocr-2
```

The first OCR request may download model files if they are not already cached. Ensure that sufficient disk space and network access are available.

### Optional Hugging Face cache

```dotenv
OPENPDF_HF_CACHE_DIR=D:\hf-cache
```

Leave this setting unset to use the Hugging Face library's default cache location.

Restart the application after changing model-source or cache settings.

### Option C: Use a vLLM server

```dotenv
OPENPDF_OCR_BACKEND=vllm
OPENPDF_VLLM_API_BASE=http://127.0.0.1:8001/v1
OPENPDF_VLLM_MODEL_NAME=datalab-to/chandra-ocr-2
```

The separately running server manages model loading. Configure the API base URL and model name to match the server.

Verify server availability and compatibility before submitting OCR requests.

`OPENPDF_MODEL_SOURCE` applies to the Hugging Face backend. When using vLLM, model loading is managed by the server.

### General application settings

```dotenv
OPENPDF_APP_NAME=OpenPDF Intelligence
OPENPDF_API_URL=http://127.0.0.1:8000

OPENPDF_MAX_PDF_MB=100
OPENPDF_MAX_PAGES=250
OPENPDF_RENDER_DPI=144

OPENPDF_TEMP_DIR=.runtime
```

| Setting | Purpose |
|---|---|
| `OPENPDF_APP_NAME` | Application name |
| `OPENPDF_API_URL` | API base URL used by application configuration |
| `OPENPDF_OCR_BACKEND` | `hf` or `vllm` |
| `OPENPDF_MODEL_SOURCE` | `local` or `huggingface` |
| `OPENPDF_MODEL_ID` | Local model directory or repository ID |
| `OPENPDF_HF_CACHE_DIR` | Optional Hugging Face Hub cache directory |
| `OPENPDF_VLLM_API_BASE` | vLLM-compatible API base URL |
| `OPENPDF_VLLM_MODEL_NAME` | Model name served by vLLM |
| `OPENPDF_MAX_PDF_MB` | Maximum PDF size in MB |
| `OPENPDF_MAX_PAGES` | Maximum PDF page count |
| `OPENPDF_RENDER_DPI` | PDF page-rendering DPI |
| `OPENPDF_TEMP_DIR` | Configured runtime directory; verify its usage before relying on it for temporary-file isolation |

The current OCR providers are Hugging Face Transformers and vLLM. Ollama is not yet implemented as a provider.

## Run the application

Run the API and UI in separate PowerShell terminals.

### Terminal 1: FastAPI

```powershell
cd D:\codebase\openpdf-intelligence
.\.venv\Scripts\Activate.ps1

uvicorn openpdf.api.main:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2: Streamlit

```powershell
cd D:\codebase\openpdf-intelligence
.\.venv\Scripts\Activate.ps1

streamlit run app\streamlit_app.py
```

Open the application at:

- Streamlit: http://localhost:8501
- API health: http://127.0.0.1:8000/health
- Swagger documentation: http://127.0.0.1:8000/docs

The supplied commands bind the API to loopback for local development. Do not expose it publicly without appropriate security and deployment controls.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Basic API health and backend information |
| `POST` | `/pdf/extract-text` | Extract native PDF text |
| `POST` | `/pdf/merge` | Merge uploaded PDFs |
| `POST` | `/pdf/extract-pages` | Extract selected pages |
| `POST` | `/pdf/rotate` | Rotate selected pages |
| `POST` | `/ocr/export` | Run OCR and return a ZIP export |

Interactive request schemas and response details are available in Swagger UI at `/docs`.

### Example: Health check

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health |
    ConvertTo-Json
```

### Example: Extract native PDF text

```powershell
curl.exe -F "file=@sample.pdf" `
  http://127.0.0.1:8000/pdf/extract-text
```

### Example: Export OCR results

```powershell
curl.exe -X POST `
  -F "file=@sample.pdf" `
  http://127.0.0.1:8000/ocr/export `
  -o ocr-results.zip
```

OCR may be slow on memory-constrained hardware. Run this command only when the configured model and inference environment are ready.

### Example: Merge PDFs

```powershell
curl.exe -X POST `
  -F "files=@one.pdf" `
  -F "files=@two.pdf" `
  http://127.0.0.1:8000/pdf/merge `
  -o merged.pdf
```

### Example: Extract pages

```powershell
curl.exe -X POST `
  -F "file=@sample.pdf" `
  -F "pages=1,3-5" `
  http://127.0.0.1:8000/pdf/extract-pages `
  -o extracted.pdf
```

## Tests and quality checks

Activate the project virtual environment before running tests.

```powershell
python -m pytest
```

**Latest verified checkpoint:** 24 tests passed.

The test suite covers PDF operations, export serialization, OCR configuration, upload validation, bounded PDF reads, and safe OCR error responses.

Run the tests again after any code change. The last verified test count does not guarantee that subsequent changes remain regression-free.

Additional recommended checks as the project matures:

```powershell
python -m compileall openpdf app
python -m ruff check .
```

The Ruff command is a recommended quality check; it must be run separately to establish whether the current repository passes linting.

## Development roadmap

The roadmap below describes proposed work. Items marked as planned or in progress are not claims of completed implementation.

### Phase 1 — Core reliability and input safety

**Status: In progress**

- [x] Implement configurable PDF upload-size and page-count settings.
- [x] Add bounded PDF reads that reject oversized uploads.
- [x] Add regression tests for PDF upload validation.
- [x] Return a generic OCR error response instead of exposing internal exception details.
- [x] Add regression coverage for OCR error responses.
- [ ] Apply request-level upload limits before multipart parsing can consume excessive resources.
- [ ] Enforce aggregate request limits for multiple-file uploads.
- [ ] Standardize input-validation errors across all endpoints.
- [ ] Review encrypted, malformed, and resource-intensive PDFs.
- [ ] Audit temporary-file and upload cleanup behavior.

**Exit criteria:** upload and PDF edge cases are covered by tests, resource consumption is bounded at the relevant layers, and client responses do not disclose internal exception details.

### Phase 2 — API production hardening

**Status: Planned**

- [ ] Add comprehensive API integration tests for every endpoint.
- [ ] Add structured application logging and request correlation IDs.
- [ ] Review error handling for PDF operations and OCR.
- [ ] Introduce an application lifespan for controlled resource initialization and shutdown.
- [ ] Define readiness checks separately from basic liveness.
- [ ] Review concurrency and worker limits for PDF processing and GPU-bound OCR.
- [ ] Verify consistent response codes and response schemas.
- [ ] Document API compatibility and error behavior.

**Exit criteria:** API behavior is documented, tested, observable, and predictable under expected failures.

### Phase 3 — OCR performance and model management

**Status: Planned; performance investigation required**

- [ ] Benchmark local Chandra inference with controlled inputs.
- [ ] Investigate CPU/GPU model placement and memory utilization.
- [ ] Validate model compatibility and required files before inference.
- [ ] Review generation limits, timeouts, and cancellation behavior.
- [ ] Test local and Hugging Face model sources independently.
- [ ] Validate the vLLM adapter against a compatible running server.
- [ ] Add OCR job progress and useful failure diagnostics.
- [ ] Define model-loading and warm-up behavior.
- [ ] Document supported hardware and expected performance ranges.

**Exit criteria:** inference performance and memory requirements are measured, and model failures are diagnosable without exposing internal details to clients.

### Phase 4 — User experience and document workflows

**Status: Planned**

- [ ] Review the Streamlit UI against the supported API capabilities.
- [ ] Improve upload feedback, validation messages, and error presentation.
- [ ] Add progress indicators for long-running OCR tasks.
- [ ] Provide clearer download and export workflows.
- [ ] Review multi-file selection and page-selection usability.
- [ ] Add tests for critical UI and API workflows.
- [ ] Improve accessibility and user-facing documentation.

**Exit criteria:** the primary workflows are understandable, tested, and usable without requiring direct API calls.

### Phase 5 — Additional providers and extensibility

**Status: Planned**

- [ ] Define a stable provider interface and provider capability model.
- [ ] Implement Ollama support only after selecting and validating a compatible vision model.
- [ ] Keep provider-specific settings isolated from shared PDF workflows.
- [ ] Add provider-specific configuration and error tests.
- [ ] Document privacy, resource, and compatibility trade-offs.
- [ ] Preserve existing Hugging Face and vLLM behavior during provider expansion.

**Exit criteria:** each provider is independently testable and does not break the shared PDF processing and export features.

### Phase 6 — Security, deployment, and release readiness

**Status: Planned**

- [ ] Add authentication and authorization before any shared or public deployment.
- [ ] Establish request and processing timeouts.
- [ ] Review rate limiting, concurrency limits, and denial-of-service risks.
- [ ] Add dependency vulnerability checks and a dependency update process.
- [ ] Review secrets and environment-file handling.
- [ ] Add deployment-specific configuration and operational documentation.
- [ ] Define backup, retention, and temporary-data cleanup policies where applicable.
- [ ] Add release checklists and automated quality gates.
- [ ] Test deployment and recovery procedures.

**Exit criteria:** the intended deployment environment has documented security controls, operational limits, and repeatable release procedures.

## Repository structure

```text
openpdf-intelligence/
├── app/
│   └── streamlit_app.py
├── openpdf/
│   ├── api/
│   │   └── main.py
│   ├── core/
│   │   ├── exports.py
│   │   └── pdf_ops.py
│   ├── ocr/
│   │   └── chandra.py
│   └── config.py
├── tests/
│   ├── test_api.py
│   ├── test_chandra_config.py
│   ├── test_exports.py
│   └── test_pdf_ops.py
├── scripts/
├── .env.example
├── MODEL-LICENSE-NOTICE.md
├── README.md
└── pyproject.toml
```

This is the expected project layout based on the files inspected during development. Verify the actual repository tree if files have been moved or added.

## Security and limitations

- Keep the API bound to loopback during local development.
- Do not expose the API publicly without authentication, authorization, rate limits, upload limits, and hardened deployment settings.
- Treat uploaded PDFs as untrusted input.
- Keep PDF-processing and ML dependencies patched.
- Validate uploads before processing them and enforce limits at both the request and application layers.
- Avoid exposing filesystem paths, stack traces, model details, or sensitive information in client-facing errors.
- Do not upload confidential documents to remote inference services unless you control and trust the destination.
- Password-protected PDFs may require unlocking before upload.
- PDF modifications are structural page operations, not arbitrary editing of existing text.
- Redaction is not implemented. Do not use visual overlays to conceal confidential information.
- OCR may hallucinate, omit, or misread content. Verify critical results against the source document.
- Review applicable model licenses before commercial use.

## Contributing

When contributing:

1. Inspect the existing implementation before modifying it.
2. Add or update regression tests for behavior changes.
3. Preserve existing API contracts unless a change is explicitly planned.
4. Avoid downloading model weights or running long inference jobs in routine unit tests.
5. Run `python -m pytest` before submitting changes.
6. Document new configuration settings, dependencies, and limitations.
7. Keep proposed roadmap items separate from completed capabilities.

## License

Review the repository's license file and [MODEL-LICENSE-NOTICE.md](MODEL-LICENSE-NOTICE.md) for the licensing terms of the application and its model dependencies.
