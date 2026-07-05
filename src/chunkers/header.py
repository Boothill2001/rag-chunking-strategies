from __future__ import annotations

import re

from config import MAX_CHUNK_CHARS, OVERLAP_CHARS
from src.chunkers.fixed import Chunk

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def _split_sections(content: str) -> list[tuple[str, str]]:
    matches = list(HEADING_RE.finditer(content))
    if not matches:
        return [("(no heading)", content.strip())]

    sections: list[tuple[str, str]] = []
    preamble = content[: matches[0].start()].strip()
    if preamble:
        sections.append(("(preamble)", preamble))

    for i, m in enumerate(matches):
        title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        if body:
            sections.append((title, body))

    return sections


def _split_long(text: str, title: str) -> list[str]:
    prefixed = f"{title}\n{text}"
    if len(prefixed) <= MAX_CHUNK_CHARS:
        return [prefixed]

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(f"{title}\n{candidate}") <= MAX_CHUNK_CHARS:
            current = candidate
        else:
            if current:
                chunks.append(f"{title}\n{current}")
                overlap = current[-OVERLAP_CHARS:] if len(current) > OVERLAP_CHARS else current
                current = f"{overlap}\n\n{para}".strip()
            else:
                for j in range(0, len(para), MAX_CHUNK_CHARS - len(title) - 1):
                    piece = para[j : j + MAX_CHUNK_CHARS - len(title) - 1]
                    chunks.append(f"{title}\n{piece}")
                current = ""

    if current:
        chunks.append(f"{title}\n{current}")

    return chunks


def header_chunk(content: str, source: str) -> list[Chunk]:
    sections = _split_sections(content)
    chunks: list[Chunk] = []

    for title, body in sections:
        pieces = _split_long(body, title)
        for piece in pieces:
            chunks.append(Chunk(text=piece, source=source, strategy="header", index=len(chunks)))

    return chunks
