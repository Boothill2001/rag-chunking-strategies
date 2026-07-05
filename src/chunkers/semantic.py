from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from config import MAX_CHUNK_CHARS, SEMANTIC_SIM_THRESHOLD, EMBEDDING_MODEL
from src.chunkers.fixed import Chunk

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
    return _model


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return float(np.dot(a, b) / norm)


def semantic_chunk(content: str, source: str, threshold: float = SEMANTIC_SIM_THRESHOLD) -> list[Chunk]:
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    if len(paragraphs) == 1:
        return [Chunk(text=paragraphs[0], source=source, strategy="semantic", index=0)]

    model = _get_model()
    embeddings = model.encode(paragraphs, normalize_embeddings=True)

    chunks: list[Chunk] = []
    current_group: list[str] = [paragraphs[0]]

    for i in range(1, len(paragraphs)):
        sim = _cosine_sim(embeddings[i - 1], embeddings[i])
        merged = "\n\n".join(current_group + [paragraphs[i]])

        if sim >= threshold and len(merged) <= MAX_CHUNK_CHARS:
            current_group.append(paragraphs[i])
        else:
            chunks.append(Chunk(
                text="\n\n".join(current_group),
                source=source,
                strategy="semantic",
                index=len(chunks),
            ))
            current_group = [paragraphs[i]]

    if current_group:
        chunks.append(Chunk(
            text="\n\n".join(current_group),
            source=source,
            strategy="semantic",
            index=len(chunks),
        ))

    return chunks
