from typing import List

from backend.domain.entities import RetrievedChunk
from backend.domain.ports import Reranker, Retriever


class RetrievalPipeline:
    """Candidate retrieval over-fetches, then the reranker narrows to top_k."""

    def __init__(
        self,
        retriever: Retriever,
        reranker: Reranker,
        top_k: int,
        candidate_multiplier: int,
        min_score: float,
    ) -> None:
        self._retriever = retriever
        self._reranker = reranker
        self._top_k = top_k
        self._candidates = max(1, candidate_multiplier) * top_k
        self._min_score = min_score

    def run(self, query: str) -> List[RetrievedChunk]:
        candidates = self._retriever.retrieve(query, self._candidates)
        if not candidates:
            return []
        ranked = self._reranker.rerank(query, candidates, self._top_k)
        return [r for r in ranked if r.score >= self._min_score]
