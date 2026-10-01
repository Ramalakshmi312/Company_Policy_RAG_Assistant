from dataclasses import dataclass
from typing import Optional

from backend.application.ask_question import AskQuestionUseCase
from backend.application.ingest_documents import IngestDocumentsUseCase
from backend.application.prompt_builder import PromptBuilder
from backend.application.retrieval_pipeline import RetrievalPipeline
from backend.composition import factories
from backend.config import Settings
from backend.database import get_connection, init_db
from backend.infrastructure.embeddings import SentenceTransformerEmbedder
from backend.infrastructure.persistence import (
    SqliteAnswerCache, SqliteDocumentRepository, SqliteQueryLogRepository,
)
from backend.infrastructure.vector_store import ChromaVectorStore

_FALLBACK_TEMPLATE = "Answer based only on the context.\nContext: {{CONTEXT}}\nQuestion: {{QUESTION}}\nAnswer:"


@dataclass
class Container:
    """Composition root: the only place that knows concrete implementations."""

    settings: Settings
    vector_store: ChromaVectorStore
    documents: SqliteDocumentRepository
    query_log: SqliteQueryLogRepository
    cache: SqliteAnswerCache
    pipeline: RetrievalPipeline
    ingest: IngestDocumentsUseCase
    ask: AskQuestionUseCase

    def reset_all(self) -> None:
        self.vector_store.reset()
        self.documents.clear()
        self.query_log.clear()
        self.cache.clear()


def build_container(settings: Optional[Settings] = None) -> Container:
    s = settings or Settings()
    init_db()

    embedder = SentenceTransformerEmbedder(s.embedding_model)
    store = ChromaVectorStore(s.chroma_dir)
    documents = SqliteDocumentRepository(get_connection)
    query_log = SqliteQueryLogRepository(get_connection)
    cache = SqliteAnswerCache(get_connection)

    pipeline = RetrievalPipeline(
        retriever=factories.build_retriever(s, embedder, store),
        reranker=factories.build_reranker(s),
        top_k=s.top_k,
        candidate_multiplier=s.candidate_multiplier,
        min_score=s.min_relevance_score,
    )

    template = (
        s.prompt_path.read_text(encoding="utf-8") if s.prompt_path.exists() else _FALLBACK_TEMPLATE
    )

    return Container(
        settings=s,
        vector_store=store,
        documents=documents,
        query_log=query_log,
        cache=cache,
        pipeline=pipeline,
        ingest=IngestDocumentsUseCase(
            factories.build_loaders(), factories.build_chunker(s), embedder, store, documents
        ),
        ask=AskQuestionUseCase(
            pipeline,
            PromptBuilder(template, s.context_char_budget),
            factories.build_llm(s),
            cache,
            query_log,
        ),
    )
