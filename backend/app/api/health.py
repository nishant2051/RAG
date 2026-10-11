"""Liveness is independent of services; diagnostics probe Qdrant on demand."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Literal

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
    ollama: Literal["not_configured"] = "not_configured"


@router.get("/health/live", response_model=Liveness)
async def live() -> Liveness:
    return Liveness()


@router.get("/health/ready", response_model=Readiness)
async def ready() -> Readiness:
    return Readiness()


@router.get("/api/v1/system/dependencies", response_model=Dependencies)
async def dependencies(connection: QdrantConnection = Depends(get_qdrant_connection)) -> Dependencies:
    try:
        await connection.check_health()
    except QdrantUnavailable:
        return Dependencies(qdrant="unavailable")
    return Dependencies(qdrant="healthy")
