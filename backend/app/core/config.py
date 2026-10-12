"""Settings loaded from backend/.env (explicit path, so it works from any folder)."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "openai/gpt-oss-20b"


@dataclass(frozen=True)
class Settings:
    nvidia_api_key: str = field(repr=False)  # repr=False keeps the key out of logs and prints
    nvidia_base_url: str = DEFAULT_BASE_URL
    default_model: str = DEFAULT_MODEL
    request_timeout: float = 60.0


def get_settings() -> Settings:
    load_dotenv(ENV_PATH)
    return Settings(
        nvidia_api_key=os.getenv("NVIDIA_API_KEY", "").strip(),
        nvidia_base_url=os.getenv("NVIDIA_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        default_model=os.getenv("NEXUS_DEFAULT_MODEL", DEFAULT_MODEL),
        request_timeout=float(os.getenv("NEXUS_REQUEST_TIMEOUT", "60")),
    )
