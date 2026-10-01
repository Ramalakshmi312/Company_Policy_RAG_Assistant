"""Abstractions the application layer depends on; infrastructure implements them."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from backend.domain.entities import (
    Chunk,
    Citation,
    LoadedDocument,
    Page,
    RetrievedChunk,
)


class DocumentLoader(ABC):
    @abstractmethod
    def supports(self, path: Path) -> bool: ...

    @abstractmethod
    def load(self, path: Path) -> LoadedDocument: ...


class Chunker(ABC):
    @abstractmethod
    def chunk(self, filename: str, pages: List[Page]) -> List[Chunk]: ...


class Embedder(ABC):
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]: ...

    @abstractmethod
    def embed_query(self, text: str) -> List[float]: ...


class VectorStore(ABC):
    @abstractmethod
    def add(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None: ...

    @abstractmethod
    def search(self, embedding: List[float], limit: int) -> List[RetrievedChunk]:
        """Return chunks ordered by descending similarity in [0, 1]."""

    @abstractmethod
    def all_chunks(self) -> List[Chunk]: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def reset(self) -> None: ...


class Retriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, limit: int) -> List[RetrievedChunk]: ...


class Reranker(ABC):
    @abstractmethod
    def rerank(self, query: str, candidates: List[RetrievedChunk], top_k: int) -> List[RetrievedChunk]: ...


class LLMClient(ABC):
    @abstractmethod
    def generate(self, question: str, context: List[RetrievedChunk], prompt: str) -> str: ...


class AnswerCache(ABC):
    @abstractmethod
    def get(self, question: str) -> Optional[tuple]:
        """Return (answer_text, citations) or None."""

    @abstractmethod
    def put(self, question: str, answer: str, citations: List[Citation]) -> None: ...

    @abstractmethod
    def clear(self) -> None: ...


class DocumentRepository(ABC):
    @abstractmethod
    def exists_by_hash(self, file_hash: str) -> bool: ...

    @abstractmethod
    def add(self, filename: str, file_hash: str, page_count: int, chunk_count: int) -> None: ...

    @abstractmethod
    def list_all(self) -> List[Dict]: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def clear(self) -> None: ...


class QueryLogRepository(ABC):
    @abstractmethod
    def log(self, question: str, answer: str, response_time_ms: float,
            retrieved_chunk_count: int, cache_hit: bool) -> None: ...

    @abstractmethod
    def recent(self, limit: int = 100) -> List[Dict]: ...

    @abstractmethod
    def summary(self) -> Dict: ...

    @abstractmethod
    def clear(self) -> None: ...
