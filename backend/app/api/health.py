"""Liveness is independent of services; diagnostics probe local dependencies on demand."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Literal

from app.infrastructure.ollama import OllamaConnection, OllamaError, get_ollama_connection
from app.infrastructure.qdrant import QdrantConnection, QdrantUnavailable, get_qdrant_connection

router = APIRouter()


class Liveness(BaseModel):
    status: Literal["alive"] = "alive"


class Readiness(BaseModel):
    status: Literal["ready"] = "ready"
    dependencies: Literal["not_checked"] = "not_checked"


class Dependencies(BaseModel):
    sqlite: Literal["not_configured"] = "not_configured"
    qdrant: Literal["healthy", "unavailable"]
    ollama: Literal["healthy", "unavailable", "models_missing"]
    ollama_embed_model: Literal["available", "missing", "not_checked"] = "not_checked"
    ollama_generation_model: Literal["available", "missing", "not_checked"] = "not_checked"


@router.get("/health/live", response_model=Liveness)
async def live() -> Liveness:
    return Liveness()


@router.get("/health/ready", response_model=Readiness)
async def ready() -> Readiness:
    return Readiness()


@router.get("/api/v1/system/dependencies", response_model=Dependencies)
async def dependencies(connection: QdrantConnection = Depends(get_qdrant_connection),
                       ollama: OllamaConnection = Depends(get_ollama_connection)) -> Dependencies:
    qdrant = "healthy"
    try:
        await connection.check_health()
    except QdrantUnavailable:
        qdrant = "unavailable"
    try:
        models = await ollama.list_models()
    except OllamaError:
        return Dependencies(qdrant=qdrant, ollama="unavailable")
    embed = "available" if ollama.settings.ollama_embed_model in models else "missing"
    generation = "available" if ollama.settings.ollama_generation_model in models else "missing"
    return Dependencies(qdrant=qdrant,
                        ollama="healthy" if embed == generation == "available" else "models_missing",
                        ollama_embed_model=embed, ollama_generation_model=generation)
