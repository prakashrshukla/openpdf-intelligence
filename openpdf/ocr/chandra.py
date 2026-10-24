from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from openpdf.config import Settings, get_settings


class OCRAdapter(Protocol):
    def recognize(self, image) -> str: ...


class ChandraOCR:
    """Lazy adapter around Chandra's documented InferenceManager interface.

    The model is loaded only on the first OCR request. No model weights are bundled.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._manager = None

    def _get_manager(self):
        if self._manager is None:
            try:
                from chandra.model import InferenceManager
            except ImportError as exc:
                raise RuntimeError(
                    "Chandra OCR is not installed. Install the optional OCR dependency "
                    "for your chosen backend; see README.md."
                ) from exc
            method = self.settings.ocr_backend
            # Chandra's upstream package reads vLLM configuration from environment.
            import os
            os.environ.setdefault("VLLM_API_BASE", self.settings.vllm_api_base)
            os.environ.setdefault("VLLM_MODEL_NAME", self.settings.vllm_model_name)
            os.environ.setdefault("MODEL_CHECKPOINT", self.settings.model_id)
            self._manager = InferenceManager(method=method)
        return self._manager

    def recognize(self, image) -> str:
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
