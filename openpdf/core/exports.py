from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from io import BytesIO


def normalize_page_result(page: int, markdown_text: str, backend: str) -> dict:
    return {
        "page": page,
        "markdown": markdown_text or "",
        "backend": backend,
    }


def export_bundle(results: list[dict], source_name: str = "document.pdf") -> bytes:
    """Return ZIP with combined and per-page OCR exports."""
    stem = Path(source_name).stem or "document"
    combined_md = "\n\n---\n\n".join(
        f"<!-- Page {r['page']} -->\n\n{r.get('markdown', '')}" for r in results
    )
    # Deliberately escaped plain Markdown in a simple HTML wrapper. Not a layout-faithful PDF.
    html_doc = (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<title>{html.escape(stem)}</title></head><body><pre>"
        f"{html.escape(combined_md)}</pre></body></html>"
    )
    txt = re.sub(r"[`*_>#|]", "", combined_md)
    payload = {
        "source": source_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pages": results,
    }
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr(f"{stem}.md", combined_md)
        archive.writestr(f"{stem}.html", html_doc)
        archive.writestr(f"{stem}.txt", txt)
        archive.writestr(f"{stem}.json", json.dumps(payload, ensure_ascii=False, indent=2))
        for result in results:
            archive.writestr(
                f"pages/page-{result['page']:04d}.md",
                result.get("markdown", ""),
            )
    return buffer.getvalue()
