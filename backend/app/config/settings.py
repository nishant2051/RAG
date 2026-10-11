"""Validated local configuration; no .env file is loaded implicitly.

RAG_HOST defaults to 127.0.0.1; RAG_PORT to 8000; RAG_ENVIRONMENT to
development (or production). RAG_CORS_ORIGINS is a comma-separated list
of local HTTP(S) origins, defaulting to localhost and 127.0.0.1 on port 5173.
Set it explicitly for a frontend using another port, such as 5174.
"""

import ipaddress
import os
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    environment: Literal["development", "production"] = "development"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])

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
    values = {key: os.environ[f"RAG_{key.upper()}"] for key in ("host", "port", "environment") if f"RAG_{key.upper()}" in os.environ}
    if "RAG_CORS_ORIGINS" in os.environ:
        values["cors_origins"] = os.environ["RAG_CORS_ORIGINS"].split(",")
    return Settings.model_validate(values)
