from typing import List

from backend.domain.ports import Embedder


class SentenceTransformerEmbedder(Embedder):
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._get_model().encode(texts, show_progress_bar=False, batch_size=32).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self._get_model().encode([text], show_progress_bar=False)[0].tolist()
