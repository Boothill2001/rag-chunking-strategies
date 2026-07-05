from __future__ import annotations

import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from config import EMBEDDING_DIM
from src.chunkers.fixed import Chunk
from src.embeddings import embed_texts, embed_query


def retrieve(chunks: list[Chunk], query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
    if not chunks:
        return []

    client = QdrantClient(":memory:")
    collection = f"tmp_{uuid.uuid4().hex[:8]}"

    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )

    texts = [c.text for c in chunks]
    vectors = embed_texts(texts)

    points = [
        PointStruct(id=i, vector=vectors[i].tolist(), payload={"index": i})
        for i in range(len(chunks))
    ]
    client.upsert(collection_name=collection, points=points)

    query_vec = embed_query(query)
    results = client.query_points(
        collection_name=collection,
        query=query_vec.tolist(),
        limit=top_k,
    )

    ranked: list[tuple[Chunk, float]] = []
    for pt in results.points:
        idx = pt.payload["index"]
        ranked.append((chunks[idx], pt.score))

    client.delete_collection(collection_name=collection)
    return ranked
