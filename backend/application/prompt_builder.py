from typing import List

from backend.domain.entities import RetrievedChunk


class PromptBuilder:
    """Renders the prompt template with numbered, citation-ready context within a size budget."""

    def __init__(self, template: str, char_budget: int) -> None:
        self._template = template
        self._char_budget = char_budget

    def build(self, question: str, context: List[RetrievedChunk]) -> str:
        blocks: List[str] = []
        used = 0
        for idx, item in enumerate(context, start=1):
            c = item.chunk
            block = f"[{idx}] Source: {c.document_name}, Page: {c.page_number}\n{c.text}"
            if blocks and used + len(block) > self._char_budget:
                break
            blocks.append(block)
            used += len(block)
        return (
            self._template
            .replace("{{CONTEXT}}", "\n\n".join(blocks))
            .replace("{{QUESTION}}", question)
        )
