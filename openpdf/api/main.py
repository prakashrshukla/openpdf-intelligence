from __future__ import annotations

import io
from concurrent.futures import ThreadPoolExecutor
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from openpdf.config import get_settings
from openpdf.core.exports import export_bundle, normalize_page_result
from openpdf.core.pdf_ops import (
    extract_native_text, extract_pages, merge_pdfs, parse_page_selection,
    rotate_pages, validate_pdf, render_pdf_pages,
)
from openpdf.ocr.chandra import get_ocr_adapter

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0",
              description="Local-first PDF tools with Chandra OCR 2.")
executor = ThreadPoolExecutor(max_workers=1)


class PageText(BaseModel):
    page: int
    text: str


class TextExtractionResponse(BaseModel):
    filename: str
    pages: list[PageText]


async def _read_pdf(file: UploadFile) -> tuple[str, bytes]:
    name = file.filename or "document.pdf"
    if not name.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Please upload a .pdf file.")
    data = await file.read()
    if len(data) > settings.max_pdf_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"PDF exceeds {settings.max_pdf_mb} MB limit.")
    try:
        validate_pdf(data, max_pages=settings.max_pages)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return name, data


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "ocr_backend": settings.ocr_backend}


@app.post("/pdf/extract-text", response_model=TextExtractionResponse)
async def extract_text(file: UploadFile = File(...)):
    name, data = await _read_pdf(file)
    try:
        pages = extract_native_text(data, max_pages=settings.max_pages)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"filename": name, "pages": pages}


@app.post("/pdf/merge")
async def merge(files: list[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Upload at least two PDF files.")
    documents = []
    for file in files:
        _, data = await _read_pdf(file)
        documents.append(data)
    try:
        output = merge_pdfs(documents)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(output, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="merged.pdf"'})


@app.post("/pdf/extract-pages")
async def extract_selected_pages(file: UploadFile = File(...), pages: str = Form(...)):
    name, data = await _read_pdf(file)
    try:
        count = validate_pdf(data, max_pages=settings.max_pages)
        selected = parse_page_selection(pages, count)
        output = extract_pages(data, selected)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(output, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{name.rsplit(".", 1)[0]}-pages.pdf"'})


@app.post("/pdf/rotate")
async def rotate(file: UploadFile = File(...), pages: str = Form(...),
                 degrees: int = Form(...)):
    name, data = await _read_pdf(file)
    try:
        count = validate_pdf(data, max_pages=settings.max_pages)
        selected = parse_page_selection(pages, count)
        output = rotate_pages(data, selected, degrees)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(output, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{name.rsplit(".", 1)[0]}-rotated.pdf"'})


@app.post("/ocr/export")
async def ocr_export(file: UploadFile = File(...)):
    name, data = await _read_pdf(file)
    try:
        pages = list(render_pdf_pages(data, dpi=settings.render_dpi, max_pages=settings.max_pages))
        adapter = get_ocr_adapter()
        results = []
        for page_number, image in pages:
            # Keep GPU-bound OCR sequential in this starter to avoid memory spikes.
            markdown_text = await __import__("asyncio").get_running_loop().run_in_executor(
                executor, adapter.recognize, image
            )
            results.append(normalize_page_result(page_number, markdown_text, settings.ocr_backend))
        bundle = export_bundle(results, source_name=name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OCR failed: {exc}") from exc
    return Response(bundle, media_type="application/zip",
                    headers={"Content-Disposition": 'attachment; filename="ocr-results.zip"'})
