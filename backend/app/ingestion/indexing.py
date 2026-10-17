"""Internal content-based indexing; no jobs, activation, deletion or HTTP wiring."""
import asyncio
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from app.api.errors import AppError
from app.infrastructure.ollama import OllamaConnection
from app.infrastructure.qdrant import QdrantConnection
from .chunking import TextChunk


class IndexingError(AppError):
    def __init__(self, code: str, message: str, status: int = 422, **details):
        super().__init__(code, message, status, details)


@dataclass(frozen=True)
class EmbeddingProfile:
    # Changing the model/input convention requires a new explicit profile.
    profile_id: str = "nomic-embed-text-latest-document-v1"
    model: str = "nomic-embed-text:latest"
    dimensions: int = 768

    def __post_init__(self) -> None:
        if (self.profile_id != "nomic-embed-text-latest-document-v1"
                or self.model != "nomic-embed-text:latest"
                or type(self.dimensions) is not int or self.dimensions != 768):
            raise IndexingError("unsupported_embedding_profile", "Only the Nomic document v1 profile with 768 dimensions is supported")


@dataclass(frozen=True)
class IndexingConfig:
    collection_name: str = "rag_nomic_documents_v1"
    batch_size: int = 16

    def __post_init__(self) -> None:
        if (not isinstance(self.collection_name, str) or not self.collection_name
                or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in self.collection_name)
                or len(self.collection_name) > 128):
            raise IndexingError("invalid_indexing_config", "Collection name must contain 1–128 ASCII letters, digits, underscores or hyphens")
        if type(self.batch_size) is not int or not 1 <= self.batch_size <= 256:
            raise IndexingError("invalid_indexing_config", "Batch size must be an integer from 1 to 256")


@dataclass(frozen=True)
class IndexingResult:
    count: int
    content_id: str
    profile_id: str
    collection_name: str
    point_ids: tuple[str, ...]


def chunk_identity(content_id: str, profile: EmbeddingProfile, chunk: TextChunk) -> str:
    """Stable UUID; position distinguishes repeated identical chunk text."""
    identity = json.dumps(["rag-point-v1", content_id, profile.profile_id,
                           chunk.index, chunk.content_hash], ensure_ascii=True, separators=(",", ":"))
    return str(uuid5(NAMESPACE_URL, identity))


def chunk_payload(content_id: str, profile: EmbeddingProfile, chunk: TextChunk) -> dict:
    return {"content_id": content_id, "profile_id": profile.profile_id,
            "embedding_model": profile.model, "embedding_dimensions": profile.dimensions,
            "embedding_input_mode": "search_document", "chunk_index": chunk.index,
            "text": chunk.text, "content_hash": chunk.content_hash,
            "section_path": list(chunk.section_path), "start_line": chunk.start_line,
            "end_line": chunk.end_line, "source_spans": [asdict(s) for s in chunk.source_spans],
            "source_reference": chunk.source_reference, "warnings": list(chunk.warnings),
            "estimated_tokens": chunk.estimated_tokens}


def validate_vectors(vectors: list[list[float]], count: int, dimensions: int) -> None:
    if (not isinstance(vectors, list) or len(vectors) != count
            or any(not isinstance(v, list) or len(v) != dimensions
                   or any(type(n) not in (int, float) or not math.isfinite(n) for n in v)
                   for v in vectors)):
        raise IndexingError("invalid_embedding_vectors", "Expected one finite numeric 768-dimensional vector per chunk", 502)


async def index_chunks(
    chunks: Sequence[TextChunk], *, content_id: str, profile: EmbeddingProfile,
    ollama: OllamaConnection, qdrant: QdrantConnection,
    config: IndexingConfig = IndexingConfig(),
) -> IndexingResult:
    """Index an immutable snapshot in order, without durable activation.

    Caller supplies a stable content identity (normally the raw content SHA-256),
    never an upload UUID. All embeddings are validated before vector writes.
    Upserts are bounded but not atomic: failures may leave acknowledged batches
    or an uncertain current batch. Repeating identical input safely reuses IDs;
    changed chunk sets do not remove old points. Callers own connection cleanup.
    Model tags can move; this profile does not pin an Ollama model digest.
    """
    chunks = tuple(chunks)
    if not isinstance(content_id, str) or not content_id.strip() or content_id != content_id.strip():
        raise IndexingError("invalid_content_identity", "Provide a nonempty stable content identity without surrounding whitespace")
    if not chunks:
        raise IndexingError("empty_index_input", "Provide at least one chunk to index")
    previous = -1
    for chunk in chunks:
        if (type(chunk.index) is not int or chunk.index <= previous or not chunk.text.strip()
                or sha256(chunk.text.encode("utf-8")).hexdigest() != chunk.content_hash):
            raise IndexingError("invalid_chunk_input", "Chunks must have increasing nonnegative indices, nonempty text and matching SHA-256 hashes")
        previous = chunk.index
    if ollama.settings.ollama_embed_model != profile.model:
        raise IndexingError("embedding_model_mismatch", "Configured Ollama embedding model does not match the explicit profile")
    acknowledged = 0
    try:
        async with asyncio.timeout(qdrant.timeout_seconds):
            if not await qdrant.client.collection_exists(config.collection_name):
                created = await qdrant.client.create_collection(
                    config.collection_name,
                    vectors_config=models.VectorParams(size=profile.dimensions, distance=models.Distance.COSINE))
                if not created:
                    raise IndexingError("collection_creation_failed", "Qdrant did not confirm collection creation", 502)
            info = await qdrant.client.get_collection(config.collection_name)
        vectors_config = info.config.params.vectors
        if (not isinstance(vectors_config, models.VectorParams)
                or vectors_config.size != profile.dimensions
                or vectors_config.distance != models.Distance.COSINE):
            raise IndexingError("incompatible_vector_collection", "Collection must use unnamed 768-dimensional cosine vectors; use a compatible collection", 409)

        # Hold embeddings until every batch validates: model failures cause no upserts.
        vectors: list[list[float]] = []
        for start in range(0, len(chunks), config.batch_size):
            batch = chunks[start:start + config.batch_size]
            embedded = await ollama.embed_documents([chunk.text for chunk in batch])
            validate_vectors(embedded, len(batch), profile.dimensions)
            vectors.extend(embedded)
        ids = tuple(chunk_identity(content_id, profile, chunk) for chunk in chunks)
        for start in range(0, len(chunks), config.batch_size):
            points = [models.PointStruct(id=ids[i], vector=vectors[i],
                      payload=chunk_payload(content_id, profile, chunks[i]))
                      for i in range(start, min(start + config.batch_size, len(chunks)))]
            async with asyncio.timeout(qdrant.timeout_seconds):
                result = await qdrant.client.upsert(config.collection_name, points=points, wait=True)
            if result.status != models.UpdateStatus.COMPLETED:
                raise IndexingError("upsert_not_completed", "Qdrant did not confirm completed upsert; retry identical input", 502,
                                    acknowledged_points=acknowledged, partial_write_possible=True)
            acknowledged += len(points)
    except (TimeoutError, ResponseHandlingException, UnexpectedResponse, OSError) as exc:
        raise IndexingError("qdrant_indexing_failed", "Qdrant indexing request failed; verify local Qdrant availability and retry identical input", 503,
                            acknowledged_points=acknowledged, partial_write_possible=True) from exc
    return IndexingResult(len(chunks), content_id, profile.profile_id, config.collection_name, ids)
