from __future__ import annotations

from dataclasses import dataclass

from config import MAX_CHUNK_CHARS, OVERLAP_CHARS


@dataclass
class Chunk:
    text: str
    source: str
    strategy: str
    index: int


def fixed_chunk(content: str, source: str, *, overlap: bool = True) -> list[Chunk]:
    step = MAX_CHUNK_CHARS - OVERLAP_CHARS if overlap else MAX_CHUNK_CHARS
    chunks: list[Chunk] = []
    for i in range(0, len(content), step):
        piece = content[i : i + MAX_CHUNK_CHARS]
        if piece.strip():
            label = "fixed_overlap" if overlap else "fixed_no_overlap"
            chunks.append(Chunk(text=piece, source=source, strategy=label, index=len(chunks)))
    return chunks
