import asyncio
from io import BytesIO

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from openpdf import config
from openpdf.api import main as api_main
from openpdf.core.pdf_ops import validate_pdf
from pypdf import PdfWriter
from unittest.mock import patch
from fastapi.testclient import TestClient

def make_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


class TrackingUpload:
    """Minimal upload stub that records how many bytes are requested."""

    def __init__(self, filename: str, data: bytes):
        self.filename = filename
        self.data = data
        self.requested_sizes = []

    async def read(self, size: int = -1) -> bytes:
        self.requested_sizes.append(size)
        if size < 0:
            return self.data
        return self.data[:size]


def test_read_pdf_accepts_valid_pdf():
    data = make_pdf()
    upload = UploadFile(filename="sample.pdf", file=BytesIO(data))

    name, result = asyncio.run(api_main._read_pdf(upload))

    assert name == "sample.pdf"
    assert result == data
    assert validate_pdf(result) == 1


def test_read_pdf_rejects_non_pdf_extension():
    upload = UploadFile(filename="sample.txt", file=BytesIO(b"not a PDF"))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(api_main._read_pdf(upload))

    assert exc.value.status_code == 415


def test_read_pdf_rejects_oversized_upload_without_full_read(monkeypatch):
    max_bytes = 1024 * 1024
    monkeypatch.setattr(
        api_main,
        "settings",
        config.Settings(max_pdf_mb=1, max_pages=250),
    )

    upload = TrackingUpload(
        filename="large.pdf",
        data=b"x" * (max_bytes + 100),
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(api_main._read_pdf(upload))

    assert exc.value.status_code == 413
    assert upload.requested_sizes == [max_bytes + 1]


def test_ocr_endpoint_does_not_expose_internal_exception(monkeypatch):
    monkeypatch.setattr(
        api_main,
        "settings",
        config.Settings(max_pdf_mb=1, max_pages=250),
    )

    secret_detail = "Model failed at C:\\private\\internal\\model.safetensors"
    client = TestClient(api_main.app)

    with patch.object(
        api_main,
        "render_pdf_pages",
        side_effect=RuntimeError(secret_detail),
    ):
        response = client.post(
            "/ocr/export",
            files={"file": ("sample.pdf", make_pdf(), "application/pdf")},
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "OCR processing failed. Please try again."
    assert secret_detail not in response.text
