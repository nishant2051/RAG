"""Deterministic chunking of parsed text, independent of ingestion workflows.

Tokens are estimated as ceil(Unicode characters / 4), including whitespace.
This is not a Nomic tokenizer guarantee. Embedding callers must still use
Ollama truncate=false and handle oversized-input rejection.
"""
from dataclasses import dataclass
from hashlib import sha256
import re

from .parsers.models import ExtractionError, ParsedDocument


@dataclass(frozen=True)
class ChunkingConfig:
    target_tokens: int = 500
    overlap_tokens: int = 75
    max_tokens: int = 1000

    def __post_init__(self) -> None:
        for name in ("target_tokens", "overlap_tokens", "max_tokens"):
            if type(getattr(self, name)) is not int:
                raise ValueError(f"{name} must be an integer")
        if self.target_tokens <= 0 or self.max_tokens <= 0:
            raise ValueError("target_tokens and max_tokens must be positive")
        if not 0 <= self.overlap_tokens < self.target_tokens:
            raise ValueError("overlap_tokens must be nonnegative and less than target_tokens")


def estimate_tokens(text: str) -> int:
    return (len(text) + 3) // 4


@dataclass(frozen=True)
class SourceSpan:
    """Half-open character offsets into an original block; lines enclose that block."""
    block_index: int
    start_char: int
    end_char: int
    block_start_line: int | None
    block_end_line: int | None


@dataclass(frozen=True)
class TextChunk:
    index: int
    text: str
    section_path: tuple[str, ...]
    start_line: int | None
    end_line: int | None
    estimated_tokens: int
    content_hash: str
    source_spans: tuple[SourceSpan, ...]
    source_reference: str | None
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class _Piece:
    text: str
    span: SourceSpan
    complete: bool


def _cut(text: str, limit: int) -> int:
    """Prefer lines, then sentences, then whitespace; never skip characters."""
    if len(text) <= limit:
        return len(text)
    window = text[:limit]
    for pattern in (r"\n", r"[.!?](?:\s+)", r"\s+"):
        ends = [match.end() for match in re.finditer(pattern, window)]
        if ends:
            return ends[-1]
    return limit


def chunk_document(document: ParsedDocument, config: ChunkingConfig = ChunkingConfig()) -> tuple[TextChunk, ...]:
    """Return ordered chunks; empty extraction raises the parser's typed failure.

    Headings always start a new group, even when heading names repeat. Whole
    blocks stay coherent when they fit. Split content is copied byte-for-byte
    at the Python string level, with offsets for lossless source coverage.
    Joining distinct pieces adds two newlines; hashes cover that exact text.
    """
    limit = min(config.target_tokens, config.max_tokens) * 4
    overlap_limit = min(config.overlap_tokens * 4, limit - 1)
    chunks: list[TextChunk] = []
    pending: list[_Piece] = []
    section: tuple[str, ...] | None = None
    warnings = list(document.warnings)
    known_types = {"heading", "paragraph", "list", "code", "table"}
    for index, block in enumerate(document.blocks):
        if block.block_type not in known_types:
            warnings.append(f"Unknown block type {block.block_type!r} at block {index}; retained as text")
    warning_tuple = tuple(warnings)

    def joined(pieces: list[_Piece]) -> str:
        return "\n\n".join(piece.text for piece in pieces)

    def emit() -> None:
        text = joined(pending)
        spans = tuple(piece.span for piece in pending)
        # Parser line spans can include fences or transformed table source.
        # Only whole blocks support honest enclosing chunk line ranges.
        located = all(piece.complete and piece.span.block_start_line is not None
                      and piece.span.block_end_line is not None for piece in pending)
        chunks.append(TextChunk(len(chunks), text, section or (),
                                spans[0].block_start_line if located else None,
                                spans[-1].block_end_line if located else None,
                                estimate_tokens(text), sha256(text.encode("utf-8")).hexdigest(),
                                spans, document.source_reference, warning_tuple))

    def overlap(room: int) -> list[_Piece]:
        budget = min(overlap_limit, room)
        result: list[_Piece] = []
        for piece in reversed(pending):
            if budget <= 0:
                break
            count = min(len(piece.text), budget)
            # Take a suffix verbatim, including unbroken strings and whitespace.
            span = piece.span
            result.insert(0, _Piece(piece.text[-count:], SourceSpan(
                span.block_index, span.end_char - count, span.end_char,
                span.block_start_line, span.block_end_line), piece.complete and count == len(piece.text)))
            budget -= count + 2
        return result

    for index, block in enumerate(document.blocks):
        if not block.text:
            continue
        if section != block.section_path or block.block_type == "heading":
            if pending:
                emit()
                pending = []
            section = block.section_path
        offset = 0
        while offset < len(block.text):
            end = offset + _cut(block.text[offset:], limit)
            piece = _Piece(block.text[offset:end], SourceSpan(
                index, offset, end, block.start_line, block.end_line),
                offset == 0 and end == len(block.text))
            if pending and len(joined(pending)) + 2 + len(piece.text) > limit:
                emit()
                pending = overlap(limit - len(piece.text) - 2)
            pending.append(piece)
            offset = end
    if pending:
        emit()
    if not chunks or not any(chunk.text.strip() for chunk in chunks):
        raise ExtractionError("empty_extraction", "Document contains no extractable text")
    return tuple(chunks)
