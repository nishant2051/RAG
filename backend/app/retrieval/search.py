"""Dense retrieval over explicitly eligible content; no durable authorization state."""
import asyncio
from dataclasses import dataclass
from hashlib import sha256
import math
from uuid import UUID

from qdrant_client import models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from app.api.errors import AppError
from app.ingestion.chunking import SourceSpan
from app.ingestion.indexing import EmbeddingProfile, IndexingConfig, validate_vectors
from app.infrastructure.ollama import OllamaConnection
from app.infrastructure.qdrant import QdrantConnection, QdrantUnavailable


class RetrievalError(AppError):
    def __init__(self, code: str, message: str, status: int = 422):
        super().__init__(code, message, status)


@dataclass(frozen=True)
class RetrievalScope:
    content_ids: frozenset[str]
    profile: EmbeddingProfile

    def __post_init__(self) -> None:
        if not isinstance(self.content_ids, (list, tuple, set, frozenset)) or any(
            not isinstance(c, str) or not c.strip() or c != c.strip() for c in self.content_ids
        ):
            raise RetrievalError("invalid_retrieval_scope", "Supply explicit content identities without surrounding whitespace")
        if not isinstance(self.profile, EmbeddingProfile):
            raise RetrievalError("unsupported_embedding_profile", "Supply the active Nomic EmbeddingProfile")
        object.__setattr__(self, "content_ids", frozenset(self.content_ids))


@dataclass(frozen=True)
class RetrievalConfig:
    collection_name: str = "rag_nomic_documents_v1"
    top_k: int = 5
    candidate_multiplier: int = 2
    min_score: float | None = None

    def __post_init__(self) -> None:
        IndexingConfig(collection_name=self.collection_name)
        if (type(self.top_k) is not int or not 1 <= self.top_k <= 20
                or type(self.candidate_multiplier) is not int or not 1 <= self.candidate_multiplier <= 4):
            raise RetrievalError("invalid_retrieval_config", "top_k must be 1–20 and candidate_multiplier 1–4")
        if self.min_score is not None and (
            type(self.min_score) not in (int, float) or not math.isfinite(self.min_score)
            or not -1 <= self.min_score <= 1
        ):
            raise RetrievalError("invalid_retrieval_config", "Optional cosine min_score must be finite and between -1 and 1")


@dataclass(frozen=True)
class Passage:
    text: str
    score: float
    point_id: str
    content_id: str
    chunk_index: int
    content_hash: str
    profile: EmbeddingProfile
    source_reference: str | None
    section_path: tuple[str, ...]
    start_line: int | None
    end_line: int | None
    source_spans: tuple[SourceSpan, ...]
    warnings: tuple[str, ...]


def _line(value: object) -> int | None:
    return value if type(value) is int and value > 0 else None


def _strings(value: object) -> tuple[str, ...]:
    return tuple(value) if isinstance(value, list) and all(isinstance(v, str) for v in value) else ()


def _passage(hit: models.ScoredPoint, scope: RetrievalScope) -> Passage | None:
    p = hit.payload
    if not isinstance(p, dict):
        return None
    text, content, digest = p.get("text"), p.get("content_id"), p.get("content_hash")
    if (not isinstance(text, str) or not text.strip() or not isinstance(content, str)
            or content not in scope.content_ids or not isinstance(digest, str)
            or sha256(text.encode("utf-8")).hexdigest() != digest
            or type(p.get("chunk_index")) is not int or p["chunk_index"] < 0
            or p.get("profile_id") != scope.profile.profile_id
            or p.get("embedding_model") != scope.profile.model
            or type(p.get("embedding_dimensions")) is not int
            or p["embedding_dimensions"] != scope.profile.dimensions
            or p.get("embedding_input_mode") != "search_document"
            or type(hit.score) not in (int, float) or not math.isfinite(hit.score)):
        return None
    try:
        point_id = str(UUID(str(hit.id)))
    except (ValueError, TypeError, AttributeError):
        return None
    spans = []
    raw_spans = p.get("source_spans")
    for span in raw_spans if isinstance(raw_spans, list) else []:
        if not isinstance(span, dict):
            continue
        values = [span.get(k) for k in ("block_index", "start_char", "end_char")]
        if all(type(v) is int and v >= 0 for v in values) and values[2] >= values[1]:
            spans.append(SourceSpan(*values, _line(span.get("block_start_line")), _line(span.get("block_end_line"))))
    start, end = _line(p.get("start_line")), _line(p.get("end_line"))
    if start is not None and end is not None and end < start:
        start = end = None
    source = p.get("source_reference")
    return Passage(text, float(hit.score), point_id, content, p["chunk_index"], digest,
                   scope.profile, source if isinstance(source, str) else None,
                   _strings(p.get("section_path")), start, end, tuple(spans), _strings(p.get("warnings")))


async def search_passages(
    question: str, *, scope: RetrievalScope, ollama: OllamaConnection,
    qdrant: QdrantConnection, config: RetrievalConfig = RetrievalConfig(),
) -> tuple[Passage, ...]:
    """Caller supplies eligible content, not SQLite-authorized active generations.

    Empty scope skips dependencies. Fewer than top_k (including zero) is valid;
    scores remain raw cosine similarities, not calibrated confidence values.
    Callers own connection cleanup. Ties are sorted within the candidate window.
    """
    if not isinstance(question, str) or not question.strip():
        raise RetrievalError("invalid_query", "Provide a nonblank question")
    if not isinstance(scope, RetrievalScope):
        raise RetrievalError("invalid_retrieval_scope", "Provide an explicit RetrievalScope")
    if not scope.content_ids:
        return ()
    if ollama.settings.ollama_embed_model != scope.profile.model:
        raise RetrievalError("embedding_model_mismatch", "Configured Ollama embedding model must match the active profile")
    vector = await ollama.embed_query(question)
    validate_vectors([vector], 1, scope.profile.dimensions)
    query_filter = models.Filter(must=[
        models.FieldCondition(key="content_id", match=models.MatchAny(any=sorted(scope.content_ids))),
        models.FieldCondition(key="profile_id", match=models.MatchValue(value=scope.profile.profile_id)),
    ])
    try:
        async with asyncio.timeout(qdrant.timeout_seconds):
            if not await qdrant.client.collection_exists(config.collection_name):
                raise RetrievalError("retrieval_collection_missing", "Index eligible content into the configured collection before retrieval", 409)
            info = await qdrant.client.get_collection(config.collection_name)
            vectors = info.config.params.vectors
            if (not isinstance(vectors, models.VectorParams) or vectors.size != scope.profile.dimensions
                    or vectors.distance != models.Distance.COSINE):
                raise RetrievalError("incompatible_vector_collection", "Retrieval requires unnamed 768-dimensional cosine vectors", 409)
            response = await qdrant.client.query_points(
                collection_name=config.collection_name, query=vector, query_filter=query_filter,
                limit=config.top_k * config.candidate_multiplier, with_payload=True,
                with_vectors=False, score_threshold=config.min_score)
    except (TimeoutError, ResponseHandlingException, UnexpectedResponse, OSError) as exc:
        raise QdrantUnavailable() from exc
    passages = [p for hit in response.points if (p := _passage(hit, scope)) is not None
                and (config.min_score is None or p.score >= config.min_score)]
    passages.sort(key=lambda p: (-p.score, p.point_id))
    selected: list[Passage] = []
    seen_ids: set[str] = set()
    seen_hashes: set[tuple[str, str]] = set()
    for passage in passages:
        key = (passage.content_id, passage.content_hash)
        if passage.point_id in seen_ids or key in seen_hashes:
            continue
        seen_ids.add(passage.point_id)
        seen_hashes.add(key)
        selected.append(passage)
        if len(selected) == config.top_k:
            break
    return tuple(selected)
