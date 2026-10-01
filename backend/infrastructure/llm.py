import logging
import re
from typing import List

import requests

from backend.domain.entities import RetrievedChunk
from backend.domain.ports import LLMClient

logger = logging.getLogger(__name__)


class OllamaClient(LLMClient):
    def __init__(self, base_url: str, model: str, timeout_s: int) -> None:
        self._url = f"{base_url}/api/generate"
        self._model = model
        self._timeout = (3, timeout_s)

    def generate(self, question: str, context: List[RetrievedChunk], prompt: str) -> str:
        resp = requests.post(
            self._url,
            json={"model": self._model, "prompt": prompt, "stream": False},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json().get("response") or "No response returned by LLM."


class ExtractiveLLM(LLMClient):
    """Model-free answer: top sentences by question-term overlap, each cited."""

    _SPLIT = re.compile(r"(?<=[.!?])\s+")

    def generate(self, question: str, context: List[RetrievedChunk], prompt: str) -> str:
        q_words = set(re.findall(r"\w+", question.lower()))
        scored = []
        for item in context:
            c = item.chunk
            for sent in self._SPLIT.split(c.text.strip()):
                words = set(re.findall(r"\w+", sent.lower()))
                if words and len(sent.strip()) >= 20:
                    overlap = len(q_words & words) / len(q_words) if q_words else 0
                    scored.append((overlap, sent.strip(), c.document_name, c.page_number))

        if not scored:
            return "No relevant information was found in the uploaded documents."

        scored.sort(key=lambda s: s[0], reverse=True)
        seen, parts = set(), []
        for _, sent, doc, page in scored:
            if sent.lower() in seen:
                continue
            seen.add(sent.lower())
            parts.append(f"{sent} [Source: {doc}, Page: {page}]")
            if len(parts) == 5:
                break
        return "\n\n".join(parts)


class FallbackLLM(LLMClient):
    """Decorator: use `primary`, degrade to `fallback` on any failure."""

    def __init__(self, primary: LLMClient, fallback: LLMClient) -> None:
        self._primary, self._fallback = primary, fallback

    def generate(self, question: str, context: List[RetrievedChunk], prompt: str) -> str:
        try:
            return self._primary.generate(question, context, prompt)
        except Exception as exc:
            logger.warning("Primary LLM failed (%s); using fallback", exc)
            return self._fallback.generate(question, context, prompt)
