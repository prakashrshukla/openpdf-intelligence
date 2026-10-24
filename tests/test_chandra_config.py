import json
from pathlib import Path

import pytest

from openpdf.config import Settings
from openpdf.ocr.chandra import ChandraOCR


def make_settings(**overrides):
    values = {
        "ocr_backend": "hf",
        "model_source": "local",
        "model_id": r"D:\ai_models\chandra-ocr-2",
        "hf_cache_dir": None,
    }
    values.update(overrides)
    return Settings(**values)


def test_local_model_path_is_configured(tmp_path, monkeypatch):
    model_dir = tmp_path / "chandra-model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text(
        json.dumps({"model_type": "test"}),
        encoding="utf-8",
    )

    settings = make_settings(model_id=str(model_dir))
    adapter = ChandraOCR(settings)

    monkeypatch.delenv("HF_HUB_CACHE", raising=False)
    adapter._configure_environment()

    assert Path(__import__("os").environ["MODEL_CHECKPOINT"]) == model_dir.resolve()


def test_local_model_directory_must_exist(tmp_path):
    missing_dir = tmp_path / "missing-model"
    adapter = ChandraOCR(make_settings(model_id=str(missing_dir)))

    with pytest.raises(RuntimeError, match="directory was not found"):
        adapter._configure_environment()


def test_local_model_requires_config_json(tmp_path):
    model_dir = tmp_path / "incomplete-model"
    model_dir.mkdir()

    adapter = ChandraOCR(make_settings(model_id=str(model_dir)))

    with pytest.raises(RuntimeError, match="config.json"):
        adapter._configure_environment()


def test_huggingface_source_accepts_repository_id(monkeypatch):
    settings = make_settings(
        model_source="huggingface",
        model_id="datalab-to/chandra-ocr-2",
    )
    adapter = ChandraOCR(settings)

    monkeypatch.delenv("HF_HUB_CACHE", raising=False)
    adapter._configure_environment()

    import os

    assert os.environ["MODEL_CHECKPOINT"] == "datalab-to/chandra-ocr-2"


def test_custom_huggingface_cache_is_configured(tmp_path, monkeypatch):
    cache_dir = tmp_path / "hf-cache"
    settings = make_settings(
        model_source="huggingface",
        model_id="datalab-to/chandra-ocr-2",
        hf_cache_dir=cache_dir,
    )
    adapter = ChandraOCR(settings)

    monkeypatch.delenv("HF_HUB_CACHE", raising=False)
    adapter._configure_environment()

    import os

    assert os.environ["HF_HUB_CACHE"] == str(cache_dir.resolve())


def test_local_source_does_not_validate_path_for_vllm():
    settings = make_settings(
        ocr_backend="vllm",
        model_source="local",
        model_id=r"D:\path\not\needed\by\vllm",
    )
    adapter = ChandraOCR(settings)

    adapter._configure_environment()
