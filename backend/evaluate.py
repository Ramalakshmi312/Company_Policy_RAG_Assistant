"""Usage: python -m backend.evaluate path/to/cases.json

cases.json: [{"question": "...", "expected_document": "x.pdf", "expected_page": 3}, ...]
Runs every configured retriever/reranker combination and prints recall@k and MRR.
"""
import json
import sys
from dataclasses import replace
from pathlib import Path

from backend.application.evaluation import EvalCase, evaluate_retrieval
from backend.application.retrieval_pipeline import RetrievalPipeline
from backend.composition import factories
from backend.config import Settings
from backend.infrastructure.embeddings import SentenceTransformerEmbedder
from backend.infrastructure.vector_store import ChromaVectorStore

RETRIEVERS = ["dense", "bm25", "hybrid"]
RERANKERS = ["none", "keyword", "cross_encoder"]


def main(path: str) -> None:
    cases = [EvalCase(**c) for c in json.loads(Path(path).read_text(encoding="utf-8"))]
    base = Settings()
    embedder = SentenceTransformerEmbedder(base.embedding_model)
    store = ChromaVectorStore(base.chroma_dir)

    print(f"{'retriever':<10} {'reranker':<14} {'recall@k':>9} {'mrr':>7}")
    for retriever in RETRIEVERS:
        for reranker in RERANKERS:
            s = replace(base, retriever=retriever, reranker=reranker)
            pipeline = RetrievalPipeline(
                factories.build_retriever(s, embedder, store),
                factories.build_reranker(s),
                s.top_k, s.candidate_multiplier, s.min_relevance_score,
            )
            m = evaluate_retrieval(pipeline, cases)
            print(f"{retriever:<10} {reranker:<14} {m['recall_at_k']:>9} {m['mrr']:>7}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
