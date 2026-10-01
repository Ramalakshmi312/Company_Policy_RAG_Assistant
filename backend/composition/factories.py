from typing import Callable, Dict, List

from backend.config import Settings
from backend.domain.ports import (
    Chunker, DocumentLoader, Embedder, LLMClient, Reranker, Retriever, VectorStore,
)
from backend.infrastructure.chunking import FixedWindowChunker, SentenceChunker
from backend.infrastructure.llm import ExtractiveLLM, FallbackLLM, OllamaClient
from backend.infrastructure.loaders import PdfLoader, TextLoader
from backend.infrastructure.rerankers import CrossEncoderReranker, KeywordReranker, NoopReranker
from backend.infrastructure.retrieval import Bm25Retriever, DenseRetriever, HybridRetriever


def _pick(kind: str, name: str, registry: Dict[str, Callable]):
    try:
        return registry[name]()
    except KeyError:
        raise ValueError(f"Unknown {kind} '{name}'. Options: {sorted(registry)}") from None


def build_loaders() -> List[DocumentLoader]:
    return [PdfLoader(), TextLoader()]


def build_chunker(s: Settings) -> Chunker:
    return _pick("chunker", s.chunker, {
        "fixed": lambda: FixedWindowChunker(s.chunk_size, s.chunk_overlap),
        "sentence": lambda: SentenceChunker(s.chunk_size, s.chunk_overlap),
    })


def build_retriever(s: Settings, embedder: Embedder, store: VectorStore) -> Retriever:
    return _pick("retriever", s.retriever, {
        "dense": lambda: DenseRetriever(embedder, store),
        "bm25": lambda: Bm25Retriever(store),
        "hybrid": lambda: HybridRetriever([DenseRetriever(embedder, store), Bm25Retriever(store)]),
    })


def build_reranker(s: Settings) -> Reranker:
    return _pick("reranker", s.reranker, {
        "none": NoopReranker,
        "keyword": KeywordReranker,
        "cross_encoder": lambda: CrossEncoderReranker(s.cross_encoder_model),
    })


def build_llm(s: Settings) -> LLMClient:
    return FallbackLLM(
        primary=OllamaClient(s.ollama_base_url, s.ollama_model, s.llm_timeout_s),
        fallback=ExtractiveLLM(),
    )
