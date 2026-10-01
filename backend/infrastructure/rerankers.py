import math
from typing import List

from backend.domain.entities import RetrievedChunk
from backend.domain.ports import Reranker
from backend.infrastructure.retrieval import tokenize


class NoopReranker(Reranker):
    def rerank(self, query: str, candidates: List[RetrievedChunk], top_k: int) -> List[RetrievedChunk]:
        return sorted(candidates, key=lambda r: r.score, reverse=True)[:top_k]


class KeywordReranker(Reranker):
    """Blends the retriever score with query-term overlap."""

    def __init__(self, retrieval_weight: float = 0.7) -> None:
        self._w = retrieval_weight

    def rerank(self, query: str, candidates: List[RetrievedChunk], top_k: int) -> List[RetrievedChunk]:
        terms = set(tokenize(query))
        out = []
        for r in candidates:
            overlap = len(terms & set(tokenize(r.chunk.text))) / len(terms) if terms else 0.0
            out.append(RetrievedChunk(r.chunk, round(self._w * r.score + (1 - self._w) * overlap, 4)))
        return sorted(out, key=lambda r: r.score, reverse=True)[:top_k]


class CrossEncoderReranker(Reranker):
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model = None

    def rerank(self, query: str, candidates: List[RetrievedChunk], top_k: int) -> List[RetrievedChunk]:
        if self._model is None:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self._model_name)
        logits = self._model.predict([(query, r.chunk.text) for r in candidates])
        out = [
            RetrievedChunk(r.chunk, round(1 / (1 + math.exp(-float(s))), 4))
            for r, s in zip(candidates, logits)
        ]
        return sorted(out, key=lambda r: r.score, reverse=True)[:top_k]
