from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class Page:
    page_number: int
    text: str


@dataclass(frozen=True)
class LoadedDocument:
    filename: str
    file_hash: str
    pages: List[Page]


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_name: str
    page_number: int
    text: str


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class Citation:
    document_name: str
    page_number: int

    def to_dict(self) -> Dict:
        return {"document_name": self.document_name, "page_number": self.page_number}


@dataclass
class Answer:
    question: str
    text: str
    citations: List[Citation] = field(default_factory=list)
    retrieved: List[RetrievedChunk] = field(default_factory=list)
    cache_hit: bool = False
    response_time_ms: float = 0.0


@dataclass
class IngestionResult:
    documents_ingested: int = 0
    total_chunks: int = 0
    skipped_duplicates: int = 0
    found_files: int = 0
