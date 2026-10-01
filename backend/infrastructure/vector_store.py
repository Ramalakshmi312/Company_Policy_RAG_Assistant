from pathlib import Path
from typing import List

from backend.domain.entities import Chunk, RetrievedChunk
from backend.domain.ports import VectorStore

COLLECTION_NAME = "policy_chunks"
_BATCH = 100


def _to_chunk(chunk_id: str, text: str, meta: dict) -> Chunk:
    return Chunk(chunk_id, meta.get("document_name", ""), int(meta.get("page_number", 0)), text)


class ChromaVectorStore(VectorStore):
    def __init__(self, path: Path) -> None:
        self._path = path
        self._client = None
        self._collection = None

    def _get_client(self):
        if self._client is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=str(self._path))
        return self._client

    def _get_collection(self):
        if self._collection is None:
            self._collection = self._get_client().get_or_create_collection(
                name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def warm_up(self) -> None:
        self._get_collection()

    def add(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        col = self._get_collection()
        for i in range(0, len(chunks), _BATCH):
            batch = chunks[i:i + _BATCH]
            col.upsert(
                ids=[c.chunk_id for c in batch],
                documents=[c.text for c in batch],
                embeddings=embeddings[i:i + _BATCH],
                metadatas=[
                    {"document_name": c.document_name, "page_number": str(c.page_number)}
                    for c in batch
                ],
            )

    def search(self, embedding: List[float], limit: int) -> List[RetrievedChunk]:
        col = self._get_collection()
        total = col.count()
        if total == 0:
            return []
        res = col.query(
            query_embeddings=[embedding],
            n_results=min(limit, total),
            include=["documents", "metadatas", "distances"],
        )
        return [
            RetrievedChunk(_to_chunk(cid, doc, meta), max(0.0, 1.0 - float(dist)))
            for cid, doc, meta, dist in zip(
                res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
            )
        ]

    def all_chunks(self) -> List[Chunk]:
        res = self._get_collection().get(include=["documents", "metadatas"])
        return [_to_chunk(i, d, m) for i, d, m in zip(res["ids"], res["documents"], res["metadatas"])]

    def count(self) -> int:
        return self._get_collection().count()

    def reset(self) -> None:
        client = self._get_client()
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self._collection = client.create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
