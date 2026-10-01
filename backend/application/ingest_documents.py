from pathlib import Path
from typing import List

from backend.domain.entities import IngestionResult
from backend.domain.ports import Chunker, DocumentLoader, DocumentRepository, Embedder, VectorStore


class IngestDocumentsUseCase:
    """load -> dedupe by hash -> chunk -> embed -> index -> record metadata."""

    def __init__(
        self,
        loaders: List[DocumentLoader],
        chunker: Chunker,
        embedder: Embedder,
        vector_store: VectorStore,
        documents: DocumentRepository,
    ) -> None:
        self._loaders = loaders
        self._chunker = chunker
        self._embedder = embedder
        self._store = vector_store
        self._documents = documents

    def execute(self, source_dir: Path) -> IngestionResult:
        result = IngestionResult()
        for path in sorted(source_dir.iterdir()):
            loader = next((l for l in self._loaders if l.supports(path)), None)
            if loader is None:
                continue
            result.found_files += 1

            doc = loader.load(path)
            if self._documents.exists_by_hash(doc.file_hash):
                result.skipped_duplicates += 1
                continue

            chunks = self._chunker.chunk(doc.filename, doc.pages)
            if not chunks:
                continue

            embeddings = self._embedder.embed_documents([c.text for c in chunks])
            self._store.add(chunks, embeddings)
            self._documents.add(doc.filename, doc.file_hash, len(doc.pages), len(chunks))
            result.documents_ingested += 1
            result.total_chunks += len(chunks)
        return result
