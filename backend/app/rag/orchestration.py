"""Inline M2 composition; document status is not transactional vector activation."""
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import re

from sqlalchemy.orm import Session

from app.api.errors import AppError
from app.config.settings import Settings
from app.documents.models import Document
from app.ingestion.chunking import chunk_document
from app.ingestion.indexing import EmbeddingProfile, index_chunks
from app.ingestion.parsers.registry import parse_document
from app.infrastructure.ollama import OllamaConnection
from app.infrastructure.qdrant import QdrantConnection
from app.rag.generation import generate_grounded_answer
from app.retrieval.search import RetrievalScope, search_passages


@dataclass(frozen=True)
class StoredSource:
    document_id: str
    filename: str
    content_id: str
    object_reference: str
    status: str
    format: str


def resolve_sources(session: Session, document_ids: list[str]) -> tuple[StoredSource, ...]:
    sources = []
    try:
        for identity in sorted(set(document_ids)):
            document = session.get(Document, identity)
            if document is None:
                raise AppError("document_not_found", "Requested document does not exist", 404)
            suffix = document.original_filename.rsplit(".", 1)[-1].lower()
            if suffix not in {"txt", "md"}:
                raise AppError("unsupported_format", "Only .txt and .md files are supported", 415)
            digest = document.content_sha256
            if (not re.fullmatch(r"[0-9a-f]{64}", digest)
                    or document.object_reference != f"objects/{digest[:2]}/{digest}"):
                raise AppError("invalid_stored_content", "Stored content identity is invalid", 409)
            sources.append(StoredSource(identity, document.original_filename, digest,
                                        document.object_reference, document.status, suffix))
        return tuple(sources)
    finally:
        # Release the SQLite read transaction before any network/model work.
        session.rollback()


def source_chunks(source: StoredSource, settings: Settings):
    root = settings.storage_root.resolve()
    path = (root / source.object_reference).resolve()
    if not path.is_relative_to(root):
        raise AppError("invalid_stored_content", "Stored content location is invalid", 409)
    try:
        with path.open("rb") as stream:
            content = stream.read(settings.upload_max_bytes + 1)
    except OSError as exc:
        raise AppError("stored_content_unavailable", "Stored content is unavailable", 409) from exc
    if len(content) > settings.upload_max_bytes:
        raise AppError("upload_too_large", "Stored content exceeds size limit", 413)
    if sha256(content).hexdigest() != source.content_id:
        raise AppError("invalid_stored_content", "Stored content checksum does not match", 409)
    # Content identity avoids logical-document metadata leaking through deduplication.
    return chunk_document(parse_document(content, source.format, source_reference=source.content_id))


async def index_document(document_id: str, *, session: Session, settings: Settings,
                         ollama: OllamaConnection, qdrant: QdrantConnection) -> dict:
    source, = resolve_sources(session, [document_id])
    chunks = source_chunks(source, settings)
    result = await index_chunks(chunks, content_id=source.content_id, profile=EmbeddingProfile(),
                                ollama=ollama, qdrant=qdrant)
    try:
        document = session.get(Document, document_id)
        if document is None or document.content_sha256 != source.content_id:
            raise AppError("document_changed", "Document changed during indexing", 409)
        document.status = "indexed"
        session.commit()
    except BaseException:
        session.rollback()
        raise
    return {"document_id": document_id, "status": "indexed", "indexed_chunk_count": result.count,
            "content_id": result.content_id, "collection_name": result.collection_name,
            "profile_id": result.profile_id}


async def answer_question(question: str, document_ids: list[str], *, session: Session,
                          ollama: OllamaConnection, qdrant: QdrantConnection) -> dict:
    sources = resolve_sources(session, document_ids)
    by_content = {}
    for source in sources:
        if source.status == "indexed":
            by_content.setdefault(source.content_id, source)
    passages = await search_passages(question, scope=RetrievalScope(frozenset(by_content), EmbeddingProfile()),
                                     ollama=ollama, qdrant=qdrant)
    # Replace shared vector source labels with a deterministic requested document ID.
    passages = tuple(replace(p, source_reference=by_content[p.content_id].document_id) for p in passages)
    result = await generate_grounded_answer(question, passages, ollama=ollama)
    citations = []
    for reference in result.references:
        passage = reference.passage
        source = by_content[passage.content_id]
        citations.append({"evidence_id": reference.evidence_id, "document_id": source.document_id,
                          "filename": source.filename, **asdict(passage)})
    return {"answer": result.answer, "outcome": result.outcome,
            "citations": citations, "prompt_version": result.prompt_version}
