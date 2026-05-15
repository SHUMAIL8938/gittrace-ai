import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _require(key: str) -> str:
    """Get env var or raise clearly — never silently use wrong config."""
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(
            f"Required environment variable '{key}' is not set. "
            f"Check your .env file."
        )
    return value


def _optional(key: str, default: str) -> str:
    return os.environ.get(key, default)


GROQ_API_KEY: str = _require("GROQ_API_KEY")
GROQ_MODEL: str = _optional("GROQ_MODEL", "llama-3.3-70b-versatile")

CHROMA_API_KEY: str | None = os.environ.get("CHROMA_API_KEY")
CHROMA_TENANT: str | None = os.environ.get("CHROMA_TENANT")
CHROMA_DATABASE: str | None = os.environ.get("CHROMA_DATABASE")
CHROMA_LOCAL_PATH: str = _optional("CHROMA_LOCAL_PATH", "chroma_db")

MAX_CHUNK_LINES: int = int(_optional("MAX_CHUNK_LINES", "100"))
MAX_REPO_SIZE_MB: int = int(_optional("MAX_REPO_SIZE_MB", "500"))
MAX_FILE_BYTES: int = int(_optional("MAX_FILE_BYTES", "100000"))

HYBRID_N_RESULTS: int = int(_optional("HYBRID_N_RESULTS", "10"))
RERANK_TOP_N: int = int(_optional("RERANK_TOP_N", "5"))

RATE_LIMIT_PER_MINUTE: int = int(_optional("RATE_LIMIT_PER_MINUTE", "10"))
ALLOWED_ORIGINS: list[str] = _optional(
    "ALLOWED_ORIGINS", "http://localhost:3000"
).split(",")

ENVIRONMENT: str = _optional("ENVIRONMENT", "development")
IS_PRODUCTION: bool = ENVIRONMENT == "production"

logger.info("Configuration loaded. Environment: %s", ENVIRONMENT)