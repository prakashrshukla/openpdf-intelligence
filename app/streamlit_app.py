from __future__ import annotations

import json
import os
import requests
import streamlit as st

API_URL = os.getenv("OPENPDF_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="OpenPDF Intelligence", page_icon="📄", layout="wide")
st.title("📄 OpenPDF Intelligence")
st.caption("Local-first PDF extraction and manipulation with Chandra OCR 2")

with st.sidebar:
    st.subheader("Connection")
    api_url = st.text_input("FastAPI base URL", API_URL)
    st.caption("Default API is localhost. Only connect to an API server you trust.")
    try:
        response = requests.get(f"{api_url.rstrip('/')}/health", timeout=3)
        response.raise_for_status()
        st.success(f"API connected · OCR backend: {response.json().get('ocr_backend', 'unknown')}")
    except requests.RequestException:
        st.warning("API not reachable. Start FastAPI in another terminal.")

tab_ocr, tab_text, tab_pages, tab_merge = st.tabs(
    ["AI OCR & Export", "Extract Text", "Extract / Rotate Pages", "Merge PDFs"]
)

with tab_ocr:
    st.subheader("OCR scanned or complex PDFs")
    ocr_file = st.file_uploader("Choose a PDF", type=["pdf"], key="ocr")
    st.info("The first OCR request may load model weights and take time. Model weights are not included.")
    if st.button("Run OCR and prepare exports", type="primary", disabled=ocr_file is None):
        with st.spinner("Rendering pages and running Chandra OCR…"):
            try:
                resp = requests.post(
                    f"{api_url.rstrip('/')}/ocr/export",
                    files={"file": (ocr_file.name, ocr_file.getvalue(), "application/pdf")},
                    timeout=None,
                )
                resp.raise_for_status()
                st.download_button(
                    "Download OCR results ZIP", resp.content,
                    file_name="ocr-results.zip", mime="application/zip",
                )
                st.success("OCR export bundle is ready.")
            except requests.RequestException as exc:
                st.error(f"OCR request failed: {exc}")
                if getattr(exc, "response", None) is not None:
                    st.code(exc.response.text)

with tab_text:
    st.subheader("Extract embedded text")
    text_file = st.file_uploader("Choose a text-based PDF", type=["pdf"], key="native")
    if st.button("Extract text", disabled=text_file is None):
        try:
            resp = requests.post(
                f"{api_url.rstrip('/')}/pdf/extract-text",
                files={"file": (text_file.name, text_file.getvalue(), "application/pdf")},
                timeout=120,
            )
            resp.raise_for_status()
            payload = resp.json()
            for page in payload["pages"]:
                with st.expander(f"Page {page['page']}", expanded=page["page"] == 1):
                    st.text_area("Text", page["text"], height=180, key=f"p{page['page']}")
            st.download_button("Download JSON", json.dumps(payload, ensure_ascii=False, indent=2),
                               file_name="extracted-text.json", mime="application/json")
        except requests.RequestException as exc:
            st.error(f"Extraction failed: {exc}")

with tab_pages:
    st.subheader("Extract selected pages or rotate them")
    page_file = st.file_uploader("Choose a PDF", type=["pdf"], key="pages")
    selection = st.text_input("1-based pages", value="1", help="Examples: 1,3-5,8")
    action = st.radio("Operation", ["Extract pages", "Rotate pages"], horizontal=True)
    degrees = st.selectbox("Clockwise rotation", [90, 180, 270], disabled=action != "Rotate pages")
    if st.button("Process pages", disabled=page_file is None):
        endpoint = "pdf/extract-pages" if action == "Extract pages" else "pdf/rotate"
        data = {"pages": selection}
        if action == "Rotate pages":
            data["degrees"] = str(degrees)
        try:
            resp = requests.post(
                f"{api_url.rstrip('/')}/{endpoint}",
                files={"file": (page_file.name, page_file.getvalue(), "application/pdf")},
                data=data, timeout=120,
            )
            resp.raise_for_status()
            st.download_button("Download processed PDF", resp.content,
                               file_name="processed-pages.pdf", mime="application/pdf")
        except requests.RequestException as exc:
            st.error(f"PDF operation failed: {exc}")
            if getattr(exc, "response", None) is not None:
                st.code(exc.response.text)

with tab_merge:
    st.subheader("Merge PDF documents")
    merge_files = st.file_uploader("Choose two or more PDFs", type=["pdf"], accept_multiple_files=True)
    if st.button("Merge PDFs", disabled=not merge_files or len(merge_files) < 2):
        try:
            files = [("files", (f.name, f.getvalue(), "application/pdf")) for f in merge_files]
            resp = requests.post(f"{api_url.rstrip('/')}/pdf/merge", files=files, timeout=120)
            resp.raise_for_status()
            st.download_button("Download merged PDF", resp.content, file_name="merged.pdf",
                               mime="application/pdf")
        except requests.RequestException as exc:
            st.error(f"Merge failed: {exc}")

st.divider()
st.caption("OCR is probabilistic: verify important content. This starter does not implement true redaction or in-place text editing.")
