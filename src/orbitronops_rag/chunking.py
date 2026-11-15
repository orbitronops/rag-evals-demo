"""Chunking: split a Markdown document into retrievable chunks.

Deterministic, no dependencies. Splits on headings and blank lines, then
packs paragraphs into chunks of at most ``max_chars`` characters, carrying
the most recent heading forward so each chunk keeps its context.
"""
from __future__ import annotations

import re
from pathlib import Path

from orbitronops_rag.models import Chunk, Document

DEFAULT_MAX_CHARS = 900


def load_documents(data_dir: str | Path) -> list[Document]:
    """Load every ``*.md`` file in ``data_dir`` as a Document, sorted by name."""
    docs: list[Document] = []
    for path in sorted(Path(data_dir).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = _title_from_text(text, fallback=path.stem)
        docs.append(Document(source=f"data/{path.name}", title=title, text=text))
    return docs


def _title_from_text(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def chunk_document(doc: Document, max_chars: int = DEFAULT_MAX_CHARS) -> list[Chunk]:
    """Split one document into chunks.

    A chunk is one or more paragraphs under the same heading, packed up to
    ``max_chars``. Very long paragraphs are hard-split at ``max_chars``.
    Returns at least one chunk for a non-empty document.
    """
    chunks: list[Chunk] = []
    heading = doc.title
    current = ""

    def flush(text: str, heading_text: str) -> None:
        nonlocal chunks
        text = text.strip()
        if not text:
            return
        chunks.append(
            Chunk(
                id=f"{Path(doc.source).name}#c{len(chunks) + 1}",
                source=doc.source,
                title=heading_text,
                text=text,
            )
        )

    for block in re.split(r"\n\s*\n", doc.text):
        block = block.strip()
        if not block:
            continue
        if block.startswith("#"):
            # New heading: flush what we have, then start under the new heading.
            flush(current, heading)
            current = ""
            heading = re.sub(r"^#+\s*", "", block.splitlines()[0]).strip()
            rest = "\n".join(block.splitlines()[1:]).strip()
            if rest:
                block = rest
            else:
                continue
        # Hard-split an over-long block so no chunk exceeds max_chars by much.
        pieces = [block[i : i + max_chars] for i in range(0, len(block), max_chars)] or [block]
        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            if current and len(current) + len(piece) + 2 > max_chars:
                flush(current, heading)
                current = piece
            elif current:
                current = f"{current}\n\n{piece}"
            else:
                current = piece
    flush(current, heading)
    return chunks


def chunk_corpus(docs: list[Document], max_chars: int = DEFAULT_MAX_CHARS) -> list[Chunk]:
    chunks: list[Chunk] = []
    for doc in docs:
        chunks.extend(chunk_document(doc, max_chars=max_chars))
    return chunks
