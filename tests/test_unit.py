"""Offline unit tests: no server, model downloads, or network required."""
from typing import List

import pytest

from backend.application.ask_question import NO_CONTEXT_MESSAGE, AskQuestionUseCase, EmptyQuestionError
from backend.application.evaluation import EvalCase, evaluate_retrieval
from backend.application.prompt_builder import PromptBuilder
from backend.application.retrieval_pipeline import RetrievalPipeline
from backend.composition import factories
from backend.config import Settings
from backend.domain.entities import Chunk, Citation, Page, RetrievedChunk
from backend.domain.ports import AnswerCache, LLMClient, QueryLogRepository, Reranker, Retriever, VectorStore
from backend.infrastructure.chunking import FixedWindowChunker, SentenceChunker
from backend.infrastructure.llm import ExtractiveLLM, FallbackLLM
from backend.infrastructure.rerankers import KeywordReranker
from backend.infrastructure.retrieval import Bm25Retriever, HybridRetriever


def chunk(cid: str, text: str, doc: str = "policy.pdf", page: int = 1) -> Chunk:
    return Chunk(cid, doc, page, text)


class FakeStore(VectorStore):
    def __init__(self, chunks: List[Chunk]) -> None:
        self._chunks = chunks

    def add(self, chunks, embeddings): self._chunks += chunks
    def search(self, embedding, limit): return [RetrievedChunk(c, 0.5) for c in self._chunks[:limit]]
    def all_chunks(self): return list(self._chunks)
    def count(self): return len(self._chunks)
    def reset(self): self._chunks = []


class FixedRetriever(Retriever):
    def __init__(self, ids: List[str]) -> None:
        self._ids = ids

    def retrieve(self, query, limit):
        return [RetrievedChunk(chunk(i, i), 1.0) for i in self._ids][:limit]


class MemCache(AnswerCache):
    def __init__(self): self.data = {}
    def get(self, q): return self.data.get(q)
    def put(self, q, a, c): self.data[q] = (a, c)
    def clear(self): self.data.clear()


class MemLog(QueryLogRepository):
    def __init__(self): self.rows = []
    def log(self, *args): self.rows.append(args)
    def recent(self, limit=100): return self.rows
    def summary(self): return {}
    def clear(self): self.rows.clear()


class EchoLLM(LLMClient):
    def __init__(self): self.calls = 0

    def generate(self, question, context, prompt):
        self.calls += 1
        return "answer"


class BoomLLM(LLMClient):
    def generate(self, question, context, prompt):
        raise RuntimeError("down")


class PassReranker(Reranker):
    def rerank(self, query, candidates, top_k): return candidates[:top_k]


# ── chunking ──────────────────────────────────────────────────────────────────
def test_fixed_chunker_overlaps_and_ids_are_unique():
    text = " ".join(f"w{i}" for i in range(25))
    chunks = FixedWindowChunker(10, 2).chunk("a.pdf", [Page(1, text)])
    assert len(chunks) == 4
    assert chunks[0].text.split()[-2:] == chunks[1].text.split()[:2]
    assert len({c.chunk_id for c in chunks}) == len(chunks)


def test_sentence_chunker_never_splits_sentences():
    text = "First rule applies here. Second rule is longer than the first one. Third."
    chunks = SentenceChunker(8, 0).chunk("a.pdf", [Page(2, text)])
    assert all(c.page_number == 2 for c in chunks)
    assert "Second rule is longer than the first one." in " ".join(c.text for c in chunks)
    assert all(c.text.rstrip().endswith((".", "!", "?")) for c in chunks)


def test_chunker_rejects_bad_overlap():
    with pytest.raises(ValueError):
        FixedWindowChunker(5, 5)


# ── retrieval ─────────────────────────────────────────────────────────────────
def test_bm25_ranks_exact_term_match_first():
    store = FakeStore([
        chunk("a", "Employees accrue twenty days of annual leave."),
        chunk("b", "The office parking policy restricts overnight vehicles."),
        chunk("c", "Expense claims must include receipts."),
    ])
    top = Bm25Retriever(store).retrieve("parking policy", 2)
    assert top[0].chunk.chunk_id == "b"
    assert top[0].score == 1.0


def test_bm25_reindexes_when_store_grows():
    store = FakeStore([chunk("a", "alpha beta")])
    bm25 = Bm25Retriever(store)
    assert bm25.retrieve("gamma", 3) == []
    store.add([chunk("b", "gamma delta")], [])
    assert bm25.retrieve("gamma", 3)[0].chunk.chunk_id == "b"


def test_rrf_promotes_chunk_found_by_both_retrievers():
    hybrid = HybridRetriever([FixedRetriever(["x", "shared"]), FixedRetriever(["y", "shared"])])
    results = hybrid.retrieve("q", 3)
    assert results[0].chunk.chunk_id == "shared"
    assert all(0 <= r.score <= 1 for r in results)


def test_keyword_reranker_boosts_overlapping_chunk():
    cands = [
        RetrievedChunk(chunk("low", "unrelated text"), 0.6),
        RetrievedChunk(chunk("hit", "remote work policy details"), 0.55),
    ]
    out = KeywordReranker().rerank("remote work policy", cands, 1)
    assert [r.chunk.chunk_id for r in out] == ["hit"]


# ── LLM ───────────────────────────────────────────────────────────────────────
def test_fallback_llm_uses_extractive_when_primary_fails():
    ctx = [RetrievedChunk(chunk("a", "Employees must badge in daily at the main entrance."), 1.0)]
    out = FallbackLLM(BoomLLM(), ExtractiveLLM()).generate("badge in", ctx, "")
    assert "[Source: policy.pdf, Page: 1]" in out


# ── use cases ─────────────────────────────────────────────────────────────────
def make_ask(retriever, llm=None, min_score=0.0):
    llm = llm or EchoLLM()
    pipeline = RetrievalPipeline(retriever, PassReranker(), top_k=2, candidate_multiplier=2, min_score=min_score)
    cache, log = MemCache(), MemLog()
    return AskQuestionUseCase(pipeline, PromptBuilder("{{CONTEXT}}|{{QUESTION}}", 1000), llm, cache, log), llm, cache, log


def test_ask_rejects_blank_question():
    uc, *_ = make_ask(FixedRetriever(["a"]))
    with pytest.raises(EmptyQuestionError):
        uc.execute("   ")


def test_ask_refuses_without_context_and_does_not_cache():
    uc, llm, cache, _ = make_ask(FixedRetriever([]))
    ans = uc.execute("anything")
    assert ans.text == NO_CONTEXT_MESSAGE
    assert llm.calls == 0 and not cache.data


def test_ask_caches_and_dedupes_citations():
    uc, llm, cache, log = make_ask(FixedRetriever(["a", "b"]))
    first = uc.execute("What is policy?")
    assert first.citations == [Citation("policy.pdf", 1)]
    second = uc.execute("What is policy?")
    assert second.cache_hit and llm.calls == 1
    assert [row[-1] for row in log.rows] == [False, True]


def test_min_score_filters_weak_chunks():
    uc, *_ = make_ask(FixedRetriever(["a"]), min_score=1.5)
    assert uc.execute("q").retrieved == []


def test_prompt_builder_respects_char_budget():
    ctx = [RetrievedChunk(chunk(str(i), "x" * 100), 1.0) for i in range(5)]
    prompt = PromptBuilder("{{CONTEXT}}", 300).build("q", ctx)
    assert prompt.count("Source:") == 2


# ── evaluation & factories ────────────────────────────────────────────────────
def test_evaluation_computes_recall_and_mrr():
    pipeline = RetrievalPipeline(FixedRetriever(["a", "b"]), PassReranker(), 2, 1, 0.0)
    cases = [EvalCase("q1", "policy.pdf"), EvalCase("q2", "missing.pdf")]
    assert evaluate_retrieval(pipeline, cases) == {"cases": 2, "recall_at_k": 0.5, "mrr": 0.5}


def test_factories_select_strategy_and_reject_unknown():
    assert isinstance(factories.build_chunker(Settings(chunker="fixed")), FixedWindowChunker)
    assert isinstance(factories.build_reranker(Settings(reranker="keyword")), KeywordReranker)
    with pytest.raises(ValueError, match="Unknown retriever"):
        factories.build_retriever(Settings(retriever="nope"), None, FakeStore([]))
