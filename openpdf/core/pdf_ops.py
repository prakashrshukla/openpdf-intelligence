from __future__ import annotations

import io
import re
from collections.abc import Sequence

import fitz
from pypdf import PdfReader, PdfWriter


def _reader(data: bytes) -> PdfReader:
    reader = PdfReader(io.BytesIO(data), strict=False)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported. Unlock the PDF first.")
    return reader


def validate_pdf(data: bytes, max_pages: int = 250) -> int:
    if not data:
        raise ValueError("Uploaded file is empty.")
    if not data.lstrip().startswith(b"%PDF-"):
        raise ValueError("File does not appear to be a PDF.")
    count = len(_reader(data).pages)
    if count > max_pages:
        raise ValueError(f"PDF has {count} pages; configured limit is {max_pages}.")
    return count


def extract_native_text(data: bytes, max_pages: int = 250) -> list[dict]:
    reader = _reader(data)
    if len(reader.pages) > max_pages:
        raise ValueError(f"PDF exceeds page limit ({max_pages}).")
    return [
        {"page": i + 1, "text": page.extract_text() or ""}
        for i, page in enumerate(reader.pages)
    ]


def merge_pdfs(documents: Sequence[bytes]) -> bytes:
    if len(documents) < 2:
        raise ValueError("Provide at least two PDFs to merge.")
    writer = PdfWriter()
    for data in documents:
        reader = _reader(data)
        for page in reader.pages:
            writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def extract_pages(data: bytes, page_numbers: Sequence[int]) -> bytes:
    reader = _reader(data)
    if not page_numbers:
        raise ValueError("Select at least one page.")
    if any(p < 1 or p > len(reader.pages) for p in page_numbers):
        raise ValueError(f"Page numbers must be between 1 and {len(reader.pages)}.")
    writer = PdfWriter()
    for page_num in page_numbers:
        writer.add_page(reader.pages[page_num - 1])
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def parse_page_selection(selection: str, page_count: int) -> list[int]:
    """Parse 1-based page selections such as '1,3-5,8'."""
    result: list[int] = []
    if not selection.strip():
        raise ValueError("Page selection is empty.")
    for part in selection.split(","):
        part = part.strip()
        if re.fullmatch(r"\d+", part):
            result.append(int(part))
        elif re.fullmatch(r"\d+\s*-\s*\d+", part):
            start, end = [int(x.strip()) for x in part.split("-", 1)]
            if start > end:
                raise ValueError(f"Invalid descending range: {part}")
            result.extend(range(start, end + 1))
        else:
            raise ValueError(f"Invalid page selection: {part}")
    if len(set(result)) != len(result):
        raise ValueError("Duplicate page numbers are not allowed.")
    if any(p < 1 or p > page_count for p in result):
        raise ValueError(f"Page numbers must be between 1 and {page_count}.")
    return result


def rotate_pages(data: bytes, page_numbers: Sequence[int], degrees: int) -> bytes:
    if degrees not in (90, 180, 270):
        raise ValueError("Rotation must be 90, 180, or 270 degrees clockwise.")
    reader = _reader(data)
    if any(p < 1 or p > len(reader.pages) for p in page_numbers):
        raise ValueError(f"Page numbers must be between 1 and {len(reader.pages)}.")
    writer = PdfWriter()
    selected = set(page_numbers)
    for i, page in enumerate(reader.pages, start=1):
        if i in selected:
            page.rotate(degrees)
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def render_pdf_pages(data: bytes, dpi: int = 144, max_pages: int = 250):
    """Yield (1-based page number, PIL RGB image) for OCR."""
    count = validate_pdf(data, max_pages=max_pages)
    doc = fitz.open(stream=data, filetype="pdf")
    scale = dpi / 72
    matrix = fitz.Matrix(scale, scale)
    try:
        for i in range(count):
            pix = doc.load_page(i).get_pixmap(matrix=matrix, alpha=False)
            yield i + 1, pix.pil_image().convert("RGB")
    finally:
        doc.close()
