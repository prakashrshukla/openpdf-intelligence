
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from openpdf.config import Settings, get_settings


class OCRAdapter(Protocol):
    def recognize(self, image) -> str: ...


class ChandraOCR:
    """Lazy adapter for Chandra OCR with configurable model source.

    The model is loaded only on the first OCR request. Model weights are not
    bundled with this application.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._manager = None

    def _configure_environment(self) -> None:
        """Configure model and cache settings before importing Chandra modules."""
        settings = self.settings
        model_id = str(settings.model_id).strip()

        if not model_id:
            raise RuntimeError("OPENPDF_MODEL_ID must not be empty.")

        if settings.ocr_backend == "hf" and settings.model_source == "local":
            model_path = Path(model_id).expanduser()

            if not model_path.is_dir():
                raise RuntimeError(
                    "Local Chandra model directory was not found: "
                    f"{model_path}. Check OPENPDF_MODEL_ID in your .env file."
                )

            if not (model_path / "config.json").is_file():
                raise RuntimeError(
                    f"Local model directory does not contain config.json: {model_path}"
                )

            model_id = str(model_path.resolve())

        os.environ["MODEL_CHECKPOINT"] = model_id
        os.environ["VLLM_API_BASE"] = settings.vllm_api_base
        os.environ["VLLM_MODEL_NAME"] = settings.vllm_model_name

        if settings.hf_cache_dir is not None:
            cache_path = settings.hf_cache_dir.expanduser().resolve()
            os.environ["HF_HUB_CACHE"] = str(cache_path)

    def _get_manager(self):
        if self._manager is None:
            self._configure_environment()

            try:
                from chandra.model import InferenceManager
            except ImportError as exc:
                raise RuntimeError(
                    "Chandra OCR is not installed. Install the optional OCR dependency "
                    "for your chosen backend; see README.md."
                ) from exc

            self._manager = InferenceManager(method=self.settings.ocr_backend)

        return self._manager

    def recognize(self, image) -> str:
        # Set configuration before importing modules that may read environment variables.
        self._configure_environment()

        try:
            from chandra.model.schema import BatchInputItem
            from chandra.output import parse_markdown
        except ImportError as exc:
            raise RuntimeError(
                "The installed chandra-ocr package does not expose the expected API. "
                "Check the upstream Chandra documentation and installed version."
            ) from exc

        item = BatchInputItem(image=image, prompt_type="ocr_layout")
        result = self._get_manager().generate([item])[0]

        markdown_text = getattr(result, "markdown", None)
        if not markdown_text:
            raw = getattr(result, "raw", "")
            markdown_text = parse_markdown(raw) if raw else ""

        if not markdown_text:
            raise RuntimeError("Chandra returned no Markdown text for this page.")

        return str(markdown_text)


@lru_cache(maxsize=1)
def get_ocr_adapter() -> ChandraOCR:
    return ChandraOCR()
