"""Validated local configuration from root .env and environment overrides.

RAG_HOST defaults to 127.0.0.1; RAG_PORT to 8000; RAG_ENVIRONMENT to
development (or production). RAG_CORS_ORIGINS is a comma-separated list
of local HTTP(S) origins, defaulting to localhost and 127.0.0.1 on port 5173.
Set it explicitly for a frontend using another port, such as 5174.
"""

import ipaddress
import os
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from dotenv import dotenv_values
from pydantic import BaseModel, Field, field_validator


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseModel):
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_timeout_seconds: int = Field(default=120, ge=1, le=300)
    ollama_embed_model: str = "nomic-embed-text:latest"
    ollama_generation_model: str = "qwen3:4b"
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_timeout_seconds: int = Field(default=3, ge=1, le=60)
    database_path: Path = BACKEND_ROOT / "data" / "rag.sqlite3"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    environment: Literal["development", "production"] = "development"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])

    @field_validator("qdrant_url", "ollama_base_url")
    @classmethod
    def local_qdrant_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        port = parsed.port
        if (value != value.strip() or parsed.scheme not in {"http", "https"}
            or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username is not None or parsed.password is not None
            or parsed.path not in {"", "/"} or parsed.query or parsed.fragment
            or (port is not None and not 1 <= port <= 65535)):
            raise ValueError("service URL must be a loopback HTTP(S) URL without credentials or paths")
        return value.rstrip("/")

    @field_validator("ollama_embed_model", "ollama_generation_model")
    @classmethod
    def model_tag(cls, value: str) -> str:
        if not value or value != value.strip() or any(c.isspace() for c in value):
            raise ValueError("model tag must be nonempty and contain no whitespace")
        return value

    @field_validator("database_path", mode="before")
    @classmethod
    def local_database_path(cls, value: str | Path) -> Path:
        raw = str(value)
        if (not raw.strip() or raw != raw.strip() or ":" in raw
            or "\\" in raw or raw.startswith("//") or "\x00" in raw):
            raise ValueError("database_path must be a local SQLite file path, not a URL or :memory:")
        path = Path(raw).expanduser()
        path = (path if path.is_absolute() else BACKEND_ROOT / path).resolve()
        if path.is_dir():
            raise ValueError("database_path must name a file, not a directory")
        return path

    @field_validator("host")
    @classmethod
    def local_host(cls, value: str) -> str:
        if value != "localhost":
            try:
                if not ipaddress.ip_address(value).is_loopback:
                    raise ValueError("host must be a loopback address or localhost")
            except ValueError as exc:
                raise ValueError("host must be a loopback address or localhost") from exc
        return value

    @field_validator("cors_origins")
    @classmethod
    def local_origins(cls, values: list[str]) -> list[str]:
        for value in values:
            parsed = urlsplit(value)
            # Accessing port also rejects invalid/non-numeric port values.
            port = parsed.port
            if (parsed.scheme not in {"http", "https"}
                or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
                or parsed.username is not None or parsed.password is not None
                or parsed.path or parsed.query or parsed.fragment
                or (port is not None and not 1 <= port <= 65535)):
                raise ValueError("CORS origins must be localhost HTTP(S) origins without paths")
        return values


def load_settings() -> Settings:
    # Fixed repository path, independent of cwd; do not mutate process environment.
    environment = {**dotenv_values(BACKEND_ROOT.parent / ".env", interpolate=False), **os.environ}
    values = {key: environment[f"RAG_{key.upper()}"] for key in ("host", "port", "environment", "database_path") if f"RAG_{key.upper()}" in environment}
    if "RAG_CORS_ORIGINS" in environment:
        values["cors_origins"] = environment["RAG_CORS_ORIGINS"].split(",")
    for key in ("qdrant_url", "qdrant_timeout_seconds", "ollama_base_url", "ollama_timeout_seconds", "ollama_embed_model", "ollama_generation_model"):
        if key.upper() in environment:
            values[key] = environment[key.upper()]
    return Settings.model_validate(values)
