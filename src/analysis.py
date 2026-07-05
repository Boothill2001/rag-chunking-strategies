from __future__ import annotations

from dataclasses import dataclass

from config import APPROX_CHARS_PER_TOKEN
from src.chunkers.fixed import Chunk


@dataclass
class ChunkStats:
    strategy: str
    chunk_count: int
    avg_length: float
    min_length: int
    max_length: int
    avg_tokens: float
    boundary_quality: float


def _ends_at_boundary(text: str) -> bool:
    stripped = text.rstrip()
    if not stripped:
        return True
    return stripped[-1] in ".!?:\n" or stripped.endswith("```")


def analyze_chunks(chunks: list[Chunk]) -> ChunkStats:
    if not chunks:
        return ChunkStats(
            strategy="unknown", chunk_count=0, avg_length=0, min_length=0,
            max_length=0, avg_tokens=0, boundary_quality=0,
        )

    lengths = [len(c.text) for c in chunks]
    good_boundaries = sum(1 for c in chunks if _ends_at_boundary(c.text))

    return ChunkStats(
        strategy=chunks[0].strategy,
        chunk_count=len(chunks),
        avg_length=sum(lengths) / len(lengths),
        min_length=min(lengths),
        max_length=max(lengths),
        avg_tokens=sum(lengths) / len(lengths) / APPROX_CHARS_PER_TOKEN,
        boundary_quality=good_boundaries / len(chunks),
    )
