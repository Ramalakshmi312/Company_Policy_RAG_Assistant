import hmac
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.application.ask_question import EmptyQuestionError
from backend.composition.container import Container, build_container
from backend.config import CORS_ORIGINS, LOG_LEVEL
from backend.models import AskRequest, AskResponse, ChunkResult, IngestResponse

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("policy_rag")


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = build_container()
    container.vector_store.warm_up()
    app.state.container = container
    yield


app = FastAPI(title="Policy Document Intelligence Assistant", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info("%s %s -> %s %.1fms rid=%s", request.method, request.url.path,
                response.status_code, elapsed_ms, request_id)
    return response


def get_container(request: Request) -> Container:
    return request.app.state.container


def require_api_key(request: Request, c: Container = Depends(get_container)) -> None:
    expected = c.settings.api_key
    if not expected:
        return
    provided = request.headers.get("X-API-Key", "")
    if not hmac.compare_digest(provided.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


@app.get("/")
def root():
    return {"message": "Policy Document Intelligence Assistant API", "status": "running"}


@app.get("/health")
def health(c: Container = Depends(get_container)):
    return {
        "status": "ok",
        "documents": c.documents.count(),
        "chunks": c.vector_store.count(),
        "retriever": c.settings.retriever,
        "reranker": c.settings.reranker,
        "chunker": c.settings.chunker,
    }


@app.post("/ingest", response_model=IngestResponse, dependencies=[Depends(require_api_key)])
def ingest_documents(c: Container = Depends(get_container)):
    source = c.settings.pdf_dir
    if not source.exists():
        raise HTTPException(status_code=404, detail=f"PDF folder not found: {source}")

    result = c.ingest.execute(source)
    if result.found_files == 0:
        return IngestResponse(
            status="warning", documents_ingested=0, total_chunks=0,
            message="No supported documents found in the source directory.",
        )
    return IngestResponse(
        status="success",
        documents_ingested=result.documents_ingested,
        total_chunks=result.total_chunks,
        message=(
            f"Ingested {result.documents_ingested} new document(s) producing "
            f"{result.total_chunks} chunks; skipped {result.skipped_duplicates} duplicate(s)."
        ),
    )


@app.post("/ask", response_model=AskResponse, dependencies=[Depends(require_api_key)])
def ask_question(request: AskRequest, c: Container = Depends(get_container)):
    try:
        answer = c.ask.execute(request.question)
    except EmptyQuestionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return AskResponse(
        question=answer.question,
        answer=answer.text,
        sources=[cit.to_dict() for cit in answer.citations],
        retrieved_chunks=[
            ChunkResult(
                chunk_id=r.chunk.chunk_id,
                text=r.chunk.text,
                document_name=r.chunk.document_name,
                page_number=r.chunk.page_number,
                score=r.score,
            )
            for r in answer.retrieved
        ],
        cache_hit=answer.cache_hit,
        response_time_ms=answer.response_time_ms,
    )


@app.get("/documents", dependencies=[Depends(require_api_key)])
def get_documents(c: Container = Depends(get_container)):
    docs = c.documents.list_all()
    return {"documents": docs, "total": len(docs)}


@app.get("/analytics", dependencies=[Depends(require_api_key)])
def analytics(c: Container = Depends(get_container)):
    return {
        "summary": {
            **c.query_log.summary(),
            "total_documents": c.documents.count(),
            "total_chunks": c.vector_store.count(),
        },
        "logs": c.query_log.recent(),
    }


@app.delete("/reset", dependencies=[Depends(require_api_key)])
def reset(c: Container = Depends(get_container)):
    c.reset_all()
    return {"message": "All data has been reset. Please re-ingest documents."}
