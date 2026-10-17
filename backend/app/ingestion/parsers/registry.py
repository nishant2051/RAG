"""Dispatch validated stored formats without accessing caller-supplied filesystem paths."""
from typing import Literal

from .markdown import parse_markdown
from .models import ExtractionError, ParsedDocument, Parser
from .txt import parse_txt

DocumentFormat = Literal["txt", "md"]
_PARSERS: dict[str, Parser] = {"txt": parse_txt, "md": parse_markdown}


def parse_document(content: bytes, document_format: DocumentFormat, *,
                   source_reference: str | None = None) -> ParsedDocument:
    parser = _PARSERS.get(document_format)
    if parser is None:
        raise ExtractionError("unsupported_format", "Only txt and md parsing is supported")
    return parser(content, source_reference=source_reference)
