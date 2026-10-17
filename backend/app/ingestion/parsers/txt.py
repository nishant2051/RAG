"""Plain text extraction with paragraph order and source lines preserved."""
from .models import DocumentBlock, ParsedDocument, decode


def parse_txt(content: bytes, *, source_reference: str | None = None) -> ParsedDocument:
    lines = decode(content).split("\n")
    blocks = []
    start = 0
    while start < len(lines):
        if not lines[start].strip():
            start += 1
            continue
        end = start + 1
        while end < len(lines) and lines[end].strip():
            end += 1
        blocks.append(DocumentBlock("paragraph", "\n".join(lines[start:end]),
                                    start_line=start + 1, end_line=end))
        start = end
    return ParsedDocument(tuple(blocks), "txt/1", source_reference)
