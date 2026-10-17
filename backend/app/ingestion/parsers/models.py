"""Immutable extraction contract. Lines are one-based and inclusive after newline normalization."""
from dataclasses import dataclass
from typing import Literal, Protocol

from app.api.errors import AppError


class ExtractionError(AppError):
    def __init__(self, code: str, message: str):
        super().__init__(code, message, 422)


@dataclass(frozen=True)
class DocumentBlock:
    block_type: Literal["heading", "paragraph", "list", "code", "table"]
    text: str
    section_path: tuple[str, ...] = ()
    start_line: int | None = None
    end_line: int | None = None
    table_rows: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class ParsedDocument:
    blocks: tuple[DocumentBlock, ...]
    parser_id: str
    source_reference: str | None = None
    warnings: tuple[str, ...] = ()


class Parser(Protocol):
    def __call__(self, content: bytes, *, source_reference: str | None = None) -> ParsedDocument: ...


def decode(content: bytes) -> str:
    try:
        text = content.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as exc:
        raise ExtractionError("invalid_utf8", "Document must contain valid UTF-8 text") from exc
    if not text.strip():
        raise ExtractionError("empty_extraction", "Document contains no extractable text")
    return text
