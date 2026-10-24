from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment and optional .env file."""

    model_config = SettingsConfigDict(
        env_prefix="OPENPDF_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "OpenPDF Intelligence"
    api_url: str = "http://127.0.0.1:8000"
    ocr_backend: Literal["hf", "vllm"] = "hf"
    model_id: str = "datalab-to/chandra-ocr-2"
    vllm_api_base: str = "http://127.0.0.1:8001/v1"
    vllm_model_name: str = "datalab-to/chandra-ocr-2"
    max_pdf_mb: int = Field(default=100, ge=1, le=1024)
    max_pages: int = Field(default=250, ge=1, le=5000)
    render_dpi: int = Field(default=144, ge=72, le=300)
    temp_dir: Path = Path(".runtime")


@lru_cache
def get_settings() -> Settings:
    return Settings()
