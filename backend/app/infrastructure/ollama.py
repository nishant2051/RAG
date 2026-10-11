"""Local Ollama adapter; no installation or RAG orchestration."""
import asyncio
import math
from collections.abc import AsyncIterator
from typing import Any

import httpx
from fastapi import Request
from pydantic import BaseModel, Field

from app.api.errors import AppError
from app.config.settings import Settings


class OllamaError(AppError):
    def __init__(self, code: str, message: str, status: int = 503, details: dict | None = None):
        super().__init__(code, message, status, {"dependency": "ollama", **(details or {})})


class GenerationOptions(BaseModel):
    temperature: float = Field(default=0.7, ge=0, le=2, allow_inf_nan=False)
    num_ctx: int = Field(default=4096, ge=512, le=32768, strict=True)
    num_predict: int = Field(default=128, ge=1, le=2048, strict=True)


class OllamaConnection:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedding_dimension: int | None = None
        self.client = httpx.AsyncClient(base_url=settings.ollama_base_url,
            timeout=settings.ollama_timeout_seconds, trust_env=False)

    async def close(self) -> None:
        await self.client.aclose()

    async def __aenter__(self) -> "OllamaConnection":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _call(self, path: str, payload: dict | None = None) -> dict:
        try:
            async with asyncio.timeout(self.settings.ollama_timeout_seconds):
                response = await self.client.request("GET" if payload is None else "POST", path, json=payload)
                if response.status_code == 404 and payload is not None:
                    raise OllamaError("model_unavailable", "Configured Ollama model is unavailable", details={"model": payload["model"]})
                if response.is_error:
                    try:
                        error = str(response.json().get("error", "")).lower()
                    except (ValueError, AttributeError):
                        error = ""
                    if any(term in error for term in ("context length", "input length", "too long")):
                        raise OllamaError("input_too_large", "Input exceeds the model context length", 422)
                    raise OllamaError("dependency_unavailable", "Ollama request failed")
                data = response.json()
                if not isinstance(data, dict) or "error" in data:
                    raise ValueError("invalid response")
                return data
        except (TimeoutError, httpx.TimeoutException) as exc:
            raise OllamaError("dependency_timeout", "Ollama request timed out") from exc
        except httpx.RequestError as exc:
            raise OllamaError("dependency_unavailable", "Ollama is unavailable") from exc
        except ValueError as exc:
            raise OllamaError("invalid_model_response", "Ollama returned an invalid response", 502) from exc

    async def list_models(self) -> list[str]:
        models = (await self._call("/api/tags")).get("models")
        if not isinstance(models, list) or any(not isinstance(m, dict) or not isinstance(m.get("name"), str) or not m["name"] for m in models):
            raise OllamaError("invalid_model_response", "Ollama returned invalid model discovery", 502)
        return [m["name"] for m in models]

    async def validate_models(self) -> list[str]:
        models = await self.list_models()
        missing = [m for m in (self.settings.ollama_embed_model, self.settings.ollama_generation_model) if m not in models]
        if missing:
            raise OllamaError("model_unavailable", "Configured Ollama models are unavailable", details={"missing_models": missing})
        return models

    async def _embed(self, texts: list[str], prefix: str) -> list[list[float]]:
        if not texts or any(not isinstance(t, str) or not t.strip() for t in texts):
            raise OllamaError("invalid_input", "Embedding input must contain nonempty text", 422)
        model = self.settings.ollama_embed_model
        inputs = [prefix + t for t in texts] if model.split(":")[0] == "nomic-embed-text" else texts
        vectors = (await self._call("/api/embed", {"model": model, "input": inputs, "truncate": False})).get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != len(texts) or any(
            not isinstance(v, list) or not v or any(type(n) not in (int, float) or not math.isfinite(n) for n in v) for v in vectors
        ):
            raise OllamaError("invalid_model_response", "Ollama returned invalid embeddings", 502)
        dimension = len(vectors[0])
        if any(len(v) != dimension for v in vectors) or self.embedding_dimension not in (None, dimension):
            raise OllamaError("invalid_model_response", "Ollama embedding dimensions are inconsistent", 502)
        self.embedding_dimension = dimension
        return vectors

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._embed(texts, "search_document: ")

    async def embed_query(self, text: str) -> list[float]:
        return (await self._embed([text], "search_query: "))[0]

    async def generate(self, prompt: str, options: GenerationOptions | None = None) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise OllamaError("invalid_input", "Generation prompt must be nonempty text", 422)
        data = await self._call("/api/generate", {"model": self.settings.ollama_generation_model,
            "prompt": prompt, "stream": False, "think": False, "options": (options or GenerationOptions()).model_dump()})
        if data.get("done") is not True or not isinstance(data.get("response"), str) or not data["response"].strip():
            raise OllamaError("invalid_model_response", "Ollama returned invalid generation output", 502)
        return data["response"]


async def get_ollama_connection(request: Request) -> AsyncIterator[OllamaConnection]:
    async with OllamaConnection(request.app.state.settings) as connection:
        yield connection
