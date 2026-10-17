"""Typed HTTP contracts for inline indexing and explicitly scoped answers."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db_session
from app.infrastructure.ollama import OllamaConnection, get_ollama_connection
from app.infrastructure.qdrant import QdrantConnection, get_qdrant_connection
from app.rag.orchestration import answer_question, index_document

router = APIRouter(prefix="/api/v1", tags=["rag"])


class IndexResult(BaseModel):
    document_id: UUID
    status: Literal["indexed"]
    indexed_chunk_count: int
    content_id: str
    collection_name: str
    profile_id: str


class AnswerRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4096)
    document_ids: list[UUID] = Field(min_length=1, max_length=100)

    @field_validator("question")
    @classmethod
    def bounded_question(cls, value: str) -> str:
        if not value.strip() or len(value.encode("utf-8")) > 4096:
            raise ValueError("Provide a nonblank question of at most 4096 UTF-8 bytes")
        return value.strip()


class SourceSpan(BaseModel):
    block_index: int
    start_char: int
    end_char: int
    block_start_line: int | None
    block_end_line: int | None


class Profile(BaseModel):
    profile_id: str
    model: str
    dimensions: int


class Citation(BaseModel):
    evidence_id: str
    document_id: UUID
    filename: str
    text: str
    score: float
    point_id: UUID
    content_id: str
    chunk_index: int
    content_hash: str
    profile: Profile
    source_reference: str
    section_path: list[str]
    start_line: int | None
    end_line: int | None
    source_spans: list[SourceSpan]
    warnings: list[str]


class AnswerResult(BaseModel):
    answer: str
    outcome: Literal["answered", "insufficient_evidence"]
    citations: list[Citation]
    prompt_version: str


@router.post("/documents/{document_id}/index", response_model=IndexResult)
async def index(document_id: UUID, request: Request, session: Session = Depends(get_db_session),
                ollama: OllamaConnection = Depends(get_ollama_connection),
                qdrant: QdrantConnection = Depends(get_qdrant_connection)):
    return await index_document(str(document_id), session=session, settings=request.app.state.settings,
                                ollama=ollama, qdrant=qdrant)


@router.post("/rag/answer", response_model=AnswerResult)
async def answer(body: AnswerRequest, session: Session = Depends(get_db_session),
                 ollama: OllamaConnection = Depends(get_ollama_connection),
                 qdrant: QdrantConnection = Depends(get_qdrant_connection)):
    return await answer_question(body.question, [str(identity) for identity in body.document_ids],
                                 session=session, ollama=ollama, qdrant=qdrant)
