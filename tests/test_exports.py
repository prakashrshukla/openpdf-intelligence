import json
from zipfile import ZipFile
from io import BytesIO

from openpdf.core.exports import export_bundle, normalize_page_result


def test_export_bundle_contains_expected_formats():
    result = export_bundle([normalize_page_result(1, "# Hello", "hf")], "sample.pdf")
    with ZipFile(BytesIO(result)) as archive:
        names = set(archive.namelist())
        assert {"sample.md", "sample.html", "sample.json", "sample.txt"} <= names
        payload = json.loads(archive.read("sample.json"))
        assert payload["pages"][0]["markdown"] == "# Hello"


def test_html_escapes_model_output():
    result = export_bundle([normalize_page_result(1, "<script>alert(1)</script>", "hf")])
    with ZipFile(BytesIO(result)) as archive:
        html = archive.read("document.html").decode()
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
