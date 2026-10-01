"""Offline retrieval evaluation: recall@k and MRR over a labelled question set."""
from dataclasses import dataclass
from typing import Dict, List, Optional

from backend.application.retrieval_pipeline import RetrievalPipeline


@dataclass(frozen=True)
class EvalCase:
    question: str
    expected_document: str
    expected_page: Optional[int] = None


def _is_hit(case: EvalCase, document: str, page: int) -> bool:
    if document != case.expected_document:
        return False
    return case.expected_page is None or page == case.expected_page


def evaluate_retrieval(pipeline: RetrievalPipeline, cases: List[EvalCase]) -> Dict[str, float]:
    if not cases:
        return {"cases": 0, "recall_at_k": 0.0, "mrr": 0.0}

    hits, reciprocal_ranks = 0, 0.0
    for case in cases:
        results = pipeline.run(case.question)
        rank = next(
            (i for i, r in enumerate(results, 1)
             if _is_hit(case, r.chunk.document_name, r.chunk.page_number)),
            None,
        )
        if rank:
            hits += 1
            reciprocal_ranks += 1 / rank

    n = len(cases)
    return {"cases": n, "recall_at_k": round(hits / n, 4), "mrr": round(reciprocal_ranks / n, 4)}
