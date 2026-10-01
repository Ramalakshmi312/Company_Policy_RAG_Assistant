import hashlib
from pathlib import Path

import fitz  # PyMuPDF

from backend.domain.entities import LoadedDocument, Page
from backend.domain.ports import DocumentLoader


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            digest.update(block)
    return digest.hexdigest()


class PdfLoader(DocumentLoader):
    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def load(self, path: Path) -> LoadedDocument:
        with fitz.open(str(path)) as doc:
            pages = [Page(i + 1, doc.load_page(i).get_text("text")) for i in range(len(doc))]
        return LoadedDocument(path.name, sha256_of(path), pages)


class TextLoader(DocumentLoader):
    """Plain text / markdown treated as a single page."""

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in {".txt", ".md"}

    def load(self, path: Path) -> LoadedDocument:
        text = path.read_text(encoding="utf-8", errors="replace")
        return LoadedDocument(path.name, sha256_of(path), [Page(1, text)])
