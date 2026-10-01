import time
from typing import List

from backend.application.prompt_builder import PromptBuilder
from backend.application.retrieval_pipeline import RetrievalPipeline
from backend.domain.entities import Answer, Citation, RetrievedChunk
from backend.domain.ports import AnswerCache, LLMClient, QueryLogRepository

NO_CONTEXT_MESSAGE = (
    "I could not find relevant information in the uploaded documents. "
    "Please ensure documents have been ingested via the Documents page."
)


class EmptyQuestionError(ValueError):
    pass


def unique_citations(retrieved: List[RetrievedChunk]) -> List[Citation]:
    seen, out = set(), []
    for r in retrieved:
        cit = Citation(r.chunk.document_name, r.chunk.page_number)
        if cit not in seen:
            seen.add(cit)
            out.append(cit)
    return out


class AskQuestionUseCase:
    """cache -> retrieve -> rerank -> prompt -> LLM -> cite -> cache/log."""

    def __init__(
        self,
        pipeline: RetrievalPipeline,
        prompt_builder: PromptBuilder,
        llm: LLMClient,
        cache: AnswerCache,
        query_log: QueryLogRepository,
    ) -> None:
        self._pipeline = pipeline
        self._prompts = prompt_builder
        self._llm = llm
        self._cache = cache
        self._log = query_log

    def execute(self, question: str) -> Answer:
        question = question.strip()
        if not question:
            raise EmptyQuestionError("Question cannot be empty.")

        start = time.perf_counter()

        cached = self._cache.get(question)
        if cached:
            text, citations = cached
            return self._finish(Answer(question, text, citations, [], True), start)

        retrieved = self._pipeline.run(question)
        if not retrieved:
            return self._finish(Answer(question, NO_CONTEXT_MESSAGE), start)

        prompt = self._prompts.build(question, retrieved)
        text = self._llm.generate(question, retrieved, prompt)
        citations = unique_citations(retrieved)
        self._cache.put(question, text, citations)
        return self._finish(Answer(question, text, citations, retrieved), start)

    def _finish(self, answer: Answer, start: float) -> Answer:
        answer.response_time_ms = round((time.perf_counter() - start) * 1000, 2)
        self._log.log(
            answer.question, answer.text, answer.response_time_ms,
            len(answer.retrieved), answer.cache_hit,
        )
        return answer
