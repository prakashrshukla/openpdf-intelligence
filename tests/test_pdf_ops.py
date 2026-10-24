import pytest
from pypdf import PdfWriter, PdfReader
from io import BytesIO

from openpdf.core.pdf_ops import (
    extract_pages, parse_page_selection, rotate_pages, validate_pdf, merge_pdfs,
)


def pdf_with_pages(count=3):
    writer = PdfWriter()
    for _ in range(count):
        writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_validate_pdf_counts_pages():
    assert validate_pdf(pdf_with_pages(3)) == 3


def test_validate_rejects_non_pdf():
    with pytest.raises(ValueError):
        validate_pdf(b"not a pdf")


def test_parse_page_selection():
    assert parse_page_selection("1,3-4", 5) == [1, 3, 4]


@pytest.mark.parametrize("selection", ["", "0", "4", "3-1", "1,,2", "1,1"])
def test_parse_page_selection_rejects_bad_values(selection):
    with pytest.raises(ValueError):
        parse_page_selection(selection, 3)


def test_extract_pages():
    result = extract_pages(pdf_with_pages(3), [1, 3])
    assert len(PdfReader(BytesIO(result)).pages) == 2


def test_merge_pdfs():
    result = merge_pdfs([pdf_with_pages(1), pdf_with_pages(2)])
    assert len(PdfReader(BytesIO(result)).pages) == 3


def test_rotate_pages():
    result = rotate_pages(pdf_with_pages(2), [2], 90)
    reader = PdfReader(BytesIO(result))
    assert reader.pages[0].get("/Rotate", 0) == 0
    assert reader.pages[1].get("/Rotate", 0) == 90
