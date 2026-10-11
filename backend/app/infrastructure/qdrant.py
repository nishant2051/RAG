"""Request-scoped Qdrant connectivity only; no vector operations."""

import asyncio
from collections.abc import AsyncIterator

from fastapi import Request
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from app.api.errors import AppError
from app.config.settings import Settings


class QdrantUnavailable(AppError):
    def __init__(self) -> None:
        super().__init__("dependency_unavailable", "Qdrant is unavailable", 503,
                         {"dependency": "qdrant"})


class QdrantConnection:
    def __init__(self, settings: Settings) -> None:
        self.timeout_seconds = settings.qdrant_timeout_seconds
        # No version/network probe during construction; HTTP only, no proxy routing.
        self.client = AsyncQdrantClient(
            url=settings.qdrant_url, timeout=self.timeout_seconds,
            prefer_grpc=False, check_compatibility=False, trust_env=False,
        )

    async def check_health(self) -> None:
        try:
            async with asyncio.timeout(self.timeout_seconds):
                # Server info is a lightweight GET / with a typed JSON response.
                # The generated healthz binding expects JSON but the server sends text.
                await self.client.info()
        except (TimeoutError, ResponseHandlingException, UnexpectedResponse) as exc:
            raise QdrantUnavailable() from exc

    async def close(self) -> None:
        await self.client.close()


async def get_qdrant_connection(request: Request) -> AsyncIterator[QdrantConnection]:
    connection = QdrantConnection(request.app.state.settings)
    try:
        yield connection
    finally:
        await connection.close()
