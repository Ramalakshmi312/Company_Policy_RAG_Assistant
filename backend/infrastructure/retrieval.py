import math
import re
from collections import Counter
from typing import Dict, List, Optional

from backend.domain.entities import Chunk, RetrievedChunk
from backend.domain.ports import Embedder, Retriever, VectorStore

_TOKEN = re.compile(r"\w+")


def tokenize(text: str) -> List[str]:
    return _TOKEN.findall(text.lower())


class DenseRetriever(Retriever):
    def __init__(self, embedder: Embedder, store: VectorStore) -> None:
        self._embedder = embedder
        self._store = store

    def retrieve(self, query: str, limit: int) -> List[RetrievedChunk]:
        return self._store.search(self._embedder.embed_query(query), limit)


class Bm25Retriever(Retriever):
    """In-memory Okapi BM25; the index is rebuilt when the store's chunk count changes."""

    def __init__(self, store: VectorStore, k1: float = 1.5, b: float = 0.75) -> None:
        self._store = store
        self._k1, self._b = k1, b
        self._indexed_count = -1
        self._chunks: List[Chunk] = []
        self._tfs: List[Counter] = []
        self._lengths: List[int] = []
        self._df: Dict[str, int] = {}
        self._avg_len = 0.0

    def _ensure_index(self) -> None:
        count = self._store.count()
        if count == self._indexed_count:
            return
        self._chunks = self._store.all_chunks()
        self._tfs = [Counter(tokenize(c.text)) for c in self._chunks]
        self._lengths = [sum(tf.values()) for tf in self._tfs]
        self._df = Counter(term for tf in self._tfs for term in tf)
        self._avg_len = (sum(self._lengths) / len(self._lengths)) if self._lengths else 0.0
        self._indexed_count = count

    def retrieve(self, query: str, limit: int) -> List[RetrievedChunk]:
        self._ensure_index()
        terms = set(tokenize(query))
        n = len(self._chunks)
        if not terms or n == 0:
            return []

        scored = []
        for i, tf in enumerate(self._tfs):
            score = 0.0
            for term in terms:
                freq = tf.get(term)
                if not freq:
                    continue
                idf = math.log(1 + (n - self._df[term] + 0.5) / (self._df[term] + 0.5))
                norm = 1 - self._b + self._b * self._lengths[i] / (self._avg_len or 1)
                score += idf * freq * (self._k1 + 1) / (freq + self._k1 * norm)
            if score > 0:
                scored.append((score, self._chunks[i]))

        scored.sort(key=lambda s: s[0], reverse=True)
        top = scored[:limit]
        best: Optional[float] = top[0][0] if top else None
        return [RetrievedChunk(c, s / best) for s, c in top] if best else []


class HybridRetriever(Retriever):
    """Reciprocal Rank Fusion over several retrievers; scores are normalised to [0, 1]."""

    def __init__(self, retrievers: List[Retriever], rrf_k: int = 60) -> None:
        self._retrievers = retrievers
        self._rrf_k = rrf_k

    def retrieve(self, query: str, limit: int) -> List[RetrievedChunk]:
        fused: Dict[str, float] = {}
        by_id: Dict[str, Chunk] = {}
        for retriever in self._retrievers:
            for rank, item in enumerate(retriever.retrieve(query, limit), start=1):
                cid = item.chunk.chunk_id
                by_id[cid] = item.chunk
                fused[cid] = fused.get(cid, 0.0) + 1.0 / (self._rrf_k + rank)

        max_possible = len(self._retrievers) / (self._rrf_k + 1)
        ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:limit]
        return [RetrievedChunk(by_id[cid], round(score / max_possible, 4)) for cid, score in ranked]
