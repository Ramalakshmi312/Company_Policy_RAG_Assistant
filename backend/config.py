import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Base directories ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent          # Proj/
PDF_DIR  = BASE_DIR / ".pdf"                     # Proj/.pdf/
STORAGE_DIR = Path(__file__).parent / "storage"  # Proj/backend/storage/
CHROMA_DIR  = STORAGE_DIR / "chroma"             # Proj/backend/storage/chroma/
DB_PATH     = STORAGE_DIR / "app.db"             # Proj/backend/storage/app.db

# Ensure storage directories exist at import time
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# ── Ollama ────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3")

# ── Embeddings ────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K = int(os.getenv("TOP_K", "5"))

# ── Pipeline strategies (selected by factories) ───────────────────────────────
CHUNKER_STRATEGY   = os.getenv("CHUNKER_STRATEGY", "sentence")    # fixed | sentence
RETRIEVER_STRATEGY = os.getenv("RETRIEVER_STRATEGY", "hybrid")    # dense | bm25 | hybrid
RERANKER_STRATEGY  = os.getenv("RERANKER_STRATEGY", "keyword")    # none | keyword | cross_encoder
CROSS_ENCODER_MODEL = os.getenv("CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
CANDIDATE_MULTIPLIER = int(os.getenv("CANDIDATE_MULTIPLIER", "4"))
MIN_RELEVANCE_SCORE  = float(os.getenv("MIN_RELEVANCE_SCORE", "0.0"))
CONTEXT_CHAR_BUDGET  = int(os.getenv("CONTEXT_CHAR_BUDGET", "6000"))
LLM_TIMEOUT_S        = int(os.getenv("LLM_TIMEOUT_S", "90"))
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000",
    ).split(",")
    if o.strip()
]
PROMPT_PATH = Path(__file__).parent / "prompts" / "answer_prompt.txt"
API_KEY   = os.getenv("API_KEY", "")            # empty disables auth (local dev)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


@dataclass(frozen=True)
class Settings:
    pdf_dir: Path = PDF_DIR
    chroma_dir: Path = CHROMA_DIR
    ollama_base_url: str = OLLAMA_BASE_URL
    ollama_model: str = OLLAMA_MODEL
    llm_timeout_s: int = LLM_TIMEOUT_S
    embedding_model: str = EMBEDDING_MODEL
    chunk_size: int = CHUNK_SIZE
    chunk_overlap: int = CHUNK_OVERLAP
    chunker: str = CHUNKER_STRATEGY
    retriever: str = RETRIEVER_STRATEGY
    reranker: str = RERANKER_STRATEGY
    cross_encoder_model: str = CROSS_ENCODER_MODEL
    top_k: int = TOP_K
    candidate_multiplier: int = CANDIDATE_MULTIPLIER
    min_relevance_score: float = MIN_RELEVANCE_SCORE
    context_char_budget: int = CONTEXT_CHAR_BUDGET
    prompt_path: Path = PROMPT_PATH
    api_key: str = API_KEY
