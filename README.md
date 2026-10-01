# Policy Document Intelligence Assistant

Production-oriented RAG system for question answering over organizational policy documents. Answers are grounded in retrieved passages and cited as `[Source: file, Page: N]`. Built with Clean Architecture, SOLID principles, and the Factory, Strategy, Decorator, Repository and Dependency Injection patterns.

---

## Architecture

```
                    FastAPI (interface)  -  X-API-Key auth, request-id logging, DTO validation
                                   |  Depends(get_container)
            +----------------------+-----------------------+
            v                                              v
   IngestDocumentsUseCase                          AskQuestionUseCase
            |                                              |
  INGESTION |                                   QUERY      |
  load (Factory by extension: pdf/txt/md)         cache lookup --hit--> answer
  -> dedupe by SHA-256                                        |miss
  -> chunk (Strategy: fixed | sentence)           RetrievalPipeline
  -> embed (sentence-transformers)                  retrieve  (Strategy: dense | bm25 | hybrid RRF)
  -> index in vector store (Chroma)                 rerank    (Strategy: none | keyword | cross_encoder)
  -> record metadata (SQLite)                       min-score filter  -> no context => refusal
                                                              |
                                                  PromptBuilder (char budget, numbered sources)
                                                              |
                                                  LLM (Strategy, Decorator: Ollama -> extractive fallback)
                                                              |
                                                  citations -> cache -> query log
```

Dependency rule: `interface -> application -> domain <- infrastructure`. Only `backend/composition/container.py` knows concrete classes.

```
backend/
  domain/          entities and ports (ABCs); no outward imports
  application/     use cases, retrieval pipeline, prompt builder, offline evaluation
  infrastructure/  loaders, chunking, embeddings, vector store, retrieval, rerankers, LLM, SQLite repositories
  composition/     factories.py (strategy selection from config), container.py (DI wiring)
  main.py          FastAPI routers, auth, request logging
  evaluate.py      CLI for retrieval evaluation (recall@k, MRR)
tests/             unit tests (fakes, no models) and in-process API tests
```

---

## Configuration

Copy `.env.example` to `.env`. Strategies are chosen by configuration only:

| Variable | Options / default |
|---|---|
| `CHUNKER_STRATEGY` | `fixed`, `sentence` (default) |
| `RETRIEVER_STRATEGY` | `dense`, `bm25`, `hybrid` (default) |
| `RERANKER_STRATEGY` | `none`, `keyword` (default), `cross_encoder` |
| `MIN_RELEVANCE_SCORE` | drop weak chunks; with none left the system refuses instead of guessing |
| `API_KEY` | when set, all data endpoints require the `X-API-Key` header |
| `CORS_ORIGINS` | comma-separated allowed origins |

Adding a new strategy means one class plus one registry entry in `factories.py`.

---

## Run

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn backend.main:app --reload        # http://localhost:8000/docs
```

Optional local LLM: `ollama pull llama3; ollama serve`. Without Ollama the system falls back to extractive answers.

Frontend: `cd frontend; npm install; npm run dev`. Set `VITE_API_URL` and `VITE_API_KEY` if the backend is not on `http://localhost:8000` or auth is enabled.

Docker: `docker compose up --build` starts the API and Ollama. Place documents in `.pdf/`.

---

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Liveness plus document/chunk counts and active strategies (no auth) |
| POST | `/ingest` | Ingest `.pdf`, `.txt`, `.md` files from `.pdf/` (idempotent) |
| POST | `/ask` | Grounded answer with citations and retrieved chunks |
| GET | `/documents` | Ingested documents |
| GET | `/analytics` | Query log and summary |
| DELETE | `/reset` | Wipe documents, vectors, cache and logs |

---

## Quality

```powershell
python -m pytest -q                       # unit and API tests, no server or model download needed
python -m backend.evaluate cases.json     # recall@k and MRR on a labelled question set
```

CI runs the test suite on every push (`.github/workflows/ci.yml`).
