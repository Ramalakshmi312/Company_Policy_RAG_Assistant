from pydantic import BaseModel
from typing import List, Optional


class IngestResponse(BaseModel):
    status: str
    documents_ingested: int
    total_chunks: int
    message: str


class AskRequest(BaseModel):
    question: str


class ChunkResult(BaseModel):
    chunk_id: str
    text: str
    document_name: str
    page_number: int
    score: float


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[dict]
    retrieved_chunks: List[ChunkResult]
    cache_hit: bool
    response_time_ms: float


class DocumentInfo(BaseModel):
    id: int
    filename: str
    page_count: int
    chunk_count: int
    created_at: str


class AnalyticsEntry(BaseModel):
    id: int
    question: str
    answer: Optional[str]
    response_time_ms: float
    retrieved_chunk_count: int
    cache_hit: bool
    timestamp: str
