from __future__ import annotations

import math
from typing import Iterable


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if not vector_a or not vector_b:
        return 0.0
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def top_k_similar(
    query_vector: list[float],
    embeddings: Iterable[tuple[int, list[float]]],
    k: int = 5,
) -> list[tuple[int, float]]:
    scored = [(record_id, cosine_similarity(query_vector, vector)) for record_id, vector in embeddings]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]
