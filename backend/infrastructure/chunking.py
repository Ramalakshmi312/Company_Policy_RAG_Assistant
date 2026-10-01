import re
from typing import List

from backend.domain.entities import Chunk, Page
from backend.domain.ports import Chunker


def clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _make_chunk(filename: str, page: int, counter: int, text: str) -> Chunk:
    return Chunk(f"{filename}__page{page}__chunk{counter}", filename, page, text)


class FixedWindowChunker(Chunker):
    """Overlapping fixed-size word windows."""

    def __init__(self, size: int, overlap: int) -> None:
        if overlap >= size:
            raise ValueError("overlap must be smaller than chunk size")
        self._size, self._overlap = size, overlap

    def chunk(self, filename: str, pages: List[Page]) -> List[Chunk]:
        out: List[Chunk] = []
        for page in pages:
            words = clean_text(page.text).split()
            start = 0
            while start < len(words):
                text = " ".join(words[start:start + self._size]).strip()
                if text:
                    out.append(_make_chunk(filename, page.page_number, len(out), text))
                start += self._size - self._overlap
        return out


class SentenceChunker(Chunker):
    """Packs whole sentences up to ~size words, carrying trailing sentences as overlap."""

    _SENTENCE = re.compile(r"(?<=[.!?])\s+|\n{2,}")

    def __init__(self, size: int, overlap: int) -> None:
        if overlap >= size:
            raise ValueError("overlap must be smaller than chunk size")
        self._size, self._overlap = size, overlap

    def chunk(self, filename: str, pages: List[Page]) -> List[Chunk]:
        out: List[Chunk] = []
        for page in pages:
            sentences = [s.strip() for s in self._SENTENCE.split(clean_text(page.text)) if s.strip()]
            window: List[str] = []
            words = 0
            for sentence in sentences:
                n = len(sentence.split())
                if window and words + n > self._size:
                    out.append(_make_chunk(filename, page.page_number, len(out), " ".join(window)))
                    window, words = self._carry_overlap(window)
                window.append(sentence)
                words += n
            if window:
                out.append(_make_chunk(filename, page.page_number, len(out), " ".join(window)))
        return out

    def _carry_overlap(self, window: List[str]):
        carried: List[str] = []
        count = 0
        for sentence in reversed(window):
            n = len(sentence.split())
            if count + n > self._overlap:
                break
            carried.insert(0, sentence)
            count += n
        return carried, count
