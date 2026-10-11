"""API health only: dependency statuses are placeholders, not probes."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal

router = APIRouter()


class Liveness(BaseModel):
    status: Literal["alive"] = "alive"


class Readiness(BaseModel):
    status: Literal["ready"] = "ready"
    dependencies: Literal["not_checked"] = "not_checked"


class Dependencies(BaseModel):
    sqlite: Literal["not_configured"] = "not_configured"
    qdrant: Literal["not_configured"] = "not_configured"
    ollama: Literal["not_configured"] = "not_configured"


@router.get("/health/live", response_model=Liveness)
async def live() -> Liveness:
    return Liveness()


@router.get("/health/ready", response_model=Readiness)
async def ready() -> Readiness:
    return Readiness()


@router.get("/api/v1/system/dependencies", response_model=Dependencies)
async def dependencies() -> Dependencies:
    return Dependencies()
