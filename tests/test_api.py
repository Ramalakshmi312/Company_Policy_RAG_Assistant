"""In-process API tests: the container is stubbed, so no server, models or vector DB are needed."""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.application.ask_question import EmptyQuestionError
from backend.config import Settings
from backend.domain.entities import Answer, Chunk, Citation, IngestionResult, RetrievedChunk
from backend.main import app


class StubAsk:
    def execute(self, question: str) -> Answer:
        if not question.strip():
            raise EmptyQuestionError("Question cannot be empty.")
        chunk = Chunk("c1", "policy.pdf", 2, "Employees get 20 days of leave.")
        return Answer(question, "20 days.", [Citation("policy.pdf", 2)], [RetrievedChunk(chunk, 0.9)])


class StubIngest:
    def execute(self, source_dir):
        return IngestionResult(documents_ingested=1, total_chunks=3, skipped_duplicates=0, found_files=1)


def make_container(tmp_path, api_key: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        settings=Settings(pdf_dir=tmp_path, api_key=api_key),
        ask=StubAsk(),
        ingest=StubIngest(),
        documents=SimpleNamespace(count=lambda: 1, list_all=lambda: [{"filename": "policy.pdf"}]),
        vector_store=SimpleNamespace(count=lambda: 3),
        query_log=SimpleNamespace(summary=lambda: {"total_queries": 0}, recent=lambda: []),
        reset_all=lambda: None,
    )


@pytest.fixture
def client(tmp_path):
    app.state.container = make_container(tmp_path)
    return TestClient(app)


def test_root_and_health(client):
    assert client.get("/").json()["status"] == "running"
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["chunks"] == 3


def test_request_id_header_is_echoed(client):
    assert client.get("/", headers={"X-Request-ID": "abc123"}).headers["X-Request-ID"] == "abc123"
    assert client.get("/").headers["X-Request-ID"]


def test_ask_returns_answer_with_citations(client):
    body = client.post("/ask", json={"question": "How much leave?"}).json()
    assert body["answer"] == "20 days."
    assert body["sources"] == [{"document_name": "policy.pdf", "page_number": 2}]
    assert body["retrieved_chunks"][0]["score"] == 0.9


def test_ask_blank_question_is_400(client):
    assert client.post("/ask", json={"question": "  "}).status_code == 400


def test_ingest_reports_counts(client):
    body = client.post("/ingest").json()
    assert body["status"] == "success" and body["total_chunks"] == 3


def test_ingest_missing_folder_is_404(tmp_path):
    container = make_container(tmp_path)
    container.settings = Settings(pdf_dir=tmp_path / "missing")
    app.state.container = container
    assert TestClient(app).post("/ingest").status_code == 404


def test_documents_analytics_and_reset(client):
    assert client.get("/documents").json()["total"] == 1
    assert client.get("/analytics").json()["summary"]["total_chunks"] == 3
    assert client.delete("/reset").status_code == 200


def test_api_key_is_enforced_when_configured(tmp_path):
    app.state.container = make_container(tmp_path, api_key="secret")
    c = TestClient(app)
    assert c.get("/documents").status_code == 401
    assert c.get("/documents", headers={"X-API-Key": "wrong"}).status_code == 401
    assert c.get("/documents", headers={"X-API-Key": "secret"}).status_code == 200
    assert c.get("/health").status_code == 200
