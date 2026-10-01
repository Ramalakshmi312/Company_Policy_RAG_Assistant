import json
import re
import sqlite3
from typing import Callable, Dict, List, Optional

from backend.domain.entities import Citation
from backend.domain.ports import AnswerCache, DocumentRepository, QueryLogRepository

Connect = Callable[[], sqlite3.Connection]


def _execute(connect: Connect, sql: str, params: tuple = (), fetch: str = "") :
    conn = connect()
    try:
        cur = conn.execute(sql, params)
        result = cur.fetchall() if fetch == "all" else cur.fetchone() if fetch == "one" else None
        conn.commit()
        return result
    finally:
        conn.close()


class SqliteDocumentRepository(DocumentRepository):
    def __init__(self, connect: Connect) -> None:
        self._connect = connect

    def exists_by_hash(self, file_hash: str) -> bool:
        return _execute(self._connect, "SELECT 1 FROM documents WHERE file_hash = ?", (file_hash,), "one") is not None

    def add(self, filename: str, file_hash: str, page_count: int, chunk_count: int) -> None:
        _execute(
            self._connect,
            "INSERT INTO documents (filename, file_hash, page_count, chunk_count) VALUES (?,?,?,?)",
            (filename, file_hash, page_count, chunk_count),
        )

    def list_all(self) -> List[Dict]:
        rows = _execute(self._connect, "SELECT * FROM documents ORDER BY created_at DESC", fetch="all")
        return [dict(r) for r in rows]

    def count(self) -> int:
        return _execute(self._connect, "SELECT COUNT(*) FROM documents", fetch="one")[0]

    def clear(self) -> None:
        _execute(self._connect, "DELETE FROM documents")


class SqliteQueryLogRepository(QueryLogRepository):
    def __init__(self, connect: Connect) -> None:
        self._connect = connect

    def log(self, question: str, answer: str, response_time_ms: float,
            retrieved_chunk_count: int, cache_hit: bool) -> None:
        _execute(
            self._connect,
            "INSERT INTO analytics (question, answer, response_time_ms, retrieved_chunk_count, cache_hit) "
            "VALUES (?,?,?,?,?)",
            (question, answer, response_time_ms, retrieved_chunk_count, int(cache_hit)),
        )

    def recent(self, limit: int = 100) -> List[Dict]:
        rows = _execute(
            self._connect,
            "SELECT id, question, answer, response_time_ms, retrieved_chunk_count, cache_hit, timestamp "
            "FROM analytics ORDER BY timestamp DESC, id DESC LIMIT ?",
            (limit,), "all",
        )
        return [dict(r) for r in rows]

    def summary(self) -> Dict:
        total = _execute(self._connect, "SELECT COUNT(*) FROM analytics", fetch="one")[0]
        avg = _execute(
            self._connect, "SELECT AVG(response_time_ms) FROM analytics WHERE cache_hit = 0", fetch="one"
        )[0] or 0
        hits = _execute(self._connect, "SELECT COUNT(*) FROM analytics WHERE cache_hit = 1", fetch="one")[0]
        return {"total_questions": total, "avg_response_time_ms": round(float(avg), 2), "cache_hits": hits}

    def clear(self) -> None:
        _execute(self._connect, "DELETE FROM analytics")


class SqliteAnswerCache(AnswerCache):
    def __init__(self, connect: Connect) -> None:
        self._connect = connect

    @staticmethod
    def _key(question: str) -> str:
        q = re.sub(r"[^\w\s]", "", question.lower().strip())
        return re.sub(r"\s+", " ", q)

    def get(self, question: str) -> Optional[tuple]:
        row = _execute(
            self._connect,
            "SELECT answer, sources FROM cache WHERE normalized_question = ?",
            (self._key(question),), "one",
        )
        if not row:
            return None
        sources = json.loads(row["sources"]) if row["sources"] else []
        return row["answer"], [Citation(s["document_name"], s["page_number"]) for s in sources]

    def put(self, question: str, answer: str, citations: List[Citation]) -> None:
        _execute(
            self._connect,
            "INSERT OR REPLACE INTO cache (normalized_question, answer, sources) VALUES (?,?,?)",
            (self._key(question), answer, json.dumps([c.to_dict() for c in citations])),
        )

    def clear(self) -> None:
        _execute(self._connect, "DELETE FROM cache")
