# Run Guide — Policy Document Intelligence Assistant

## Quick Start (run everything fresh)

Open **three separate terminals** from the `Proj/` directory.

---

## Terminal 1 — Backend

```powershell
# 1. Create and activate virtual environment (first time only)
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies (first time only)
pip install -r requirements.txt

# 3. Copy env file (first time only)
copy .env.example .env

# 4. Start FastAPI backend
uvicorn backend.main:app --reload
```

Backend available at: http://localhost:8000  
Interactive API docs: http://localhost:8000/docs

---

## Terminal 2 — Ollama LLM (optional)

```powershell
# Pull the model (first time only — ~4 GB download)
ollama pull llama3

# Start Ollama server
ollama serve
```

> Ollama runs at http://localhost:11434  
> Skip this step if you just want to test retrieval without LLM generation.

---

## Terminal 3 — Frontend

```powershell
cd frontend

# Install Node dependencies (first time only)
npm install

# Start Vite dev server
npm run dev
```

Frontend available at: http://localhost:5173

---

## Step-by-step usage

1. Open http://localhost:5173
2. Go to **Documents** → click **Ingest Documents**
   - Wait for the success message (first run embeds all chunks)
3. Go to **Ask Assistant** → type a question → click **Ask**
4. View citations, retrieved chunks, and the LLM answer
5. Go to **Analytics** to see query logs and performance stats

---

## Re-ingest after adding new PDFs

Place new PDFs in the `.pdf/` folder, then click **Ingest Documents** again.  
Duplicate files are detected by SHA-256 hash and skipped automatically.

---

## Reset everything

```powershell
# DELETE /reset via curl (wipes vectors, docs, cache, analytics)
curl -X DELETE http://localhost:8000/reset
```

Or use the Swagger UI at http://localhost:8000/docs.

---

## Run tests

```powershell
# With backend running and venv active, from Proj/ directory:
pip install pytest
python -m pytest tests/ -v
```

---

## Common issues

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: backend` | Run `uvicorn` from the `Proj/` root, not from inside `backend/` |
| Embedding model download fails | Ensure internet access for the first run |
| Ollama not found | Install from https://ollama.com — app works without it |
| CORS error in browser | Ensure backend is on port 8000 and frontend on port 5173 |
| `chromadb` version mismatch | Run `pip install --upgrade chromadb` |
