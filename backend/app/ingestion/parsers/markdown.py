"""CommonMark extraction with tables; HTML is retained as inert source text."""
from importlib.metadata import version

from markdown_it import MarkdownIt

from .models import DocumentBlock, ExtractionError, ParsedDocument, decode


def parse_markdown(content: bytes, *, source_reference: str | None = None) -> ParsedDocument:
    source = decode(content)
    lines = source.split("\n")
    tokens = MarkdownIt("commonmark").enable("table").parse(source)
    blocks = []
    headings: list[tuple[int, str]] = []
    warnings = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        kind = token.type
        end = index + 1
        rows: tuple[tuple[str, ...], ...] = ()
        if kind in {"bullet_list_open", "ordered_list_open", "table_open"}:
            closing = kind.replace("_open", "_close")
            depth = 1
            while end < len(tokens):
                if tokens[end].type == kind:
                    depth += 1
                elif tokens[end].type == closing:
                    depth -= 1
                end += 1
                if depth == 0:
                    break
            inner = tokens[index:end]
            if kind == "table_open":
                table = []
                row = []
                for child in inner:
                    if child.type == "tr_open":
                        row = []
                    elif child.type == "inline":
                        row.append(child.content)
                    elif child.type == "tr_close":
                        table.append(tuple(row))
                rows = tuple(table)
                text = "\n".join(" | ".join(row) for row in rows)
                block_type = "table"
            else:
                # Keep list markers, nesting, and embedded code formatting intact.
                text = "\n".join(lines[token.map[0]:token.map[1]])
                block_type = "list"
        elif kind in {"heading_open", "paragraph_open"}:
            text = tokens[index + 1].content
            end = index + 3
            block_type = "heading" if kind == "heading_open" else "paragraph"
            if block_type == "heading":
                level = int(token.tag[1:])
                headings = [(n, title) for n, title in headings if n < level]
                headings.append((level, text))
        elif kind in {"fence", "code_block", "html_block"}:
            text = token.content
            block_type = "paragraph" if kind == "html_block" else "code"
            if kind == "html_block" and "HTML retained as inert source text" not in warnings:
                warnings.append("HTML retained as inert source text")
        else:
            index += 1
            continue
        if text.strip():
            location = token.map
            blocks.append(DocumentBlock(block_type, text, tuple(title for _, title in headings),
                                        location[0] + 1 if location else None,
                                        location[1] if location else None, rows))
        index = end
    if not blocks:
        raise ExtractionError("empty_extraction", "Document contains no extractable text")
    return ParsedDocument(tuple(blocks), f"markdown/1;markdown-it-py/{version('markdown-it-py')}",
                          source_reference, tuple(warnings))
