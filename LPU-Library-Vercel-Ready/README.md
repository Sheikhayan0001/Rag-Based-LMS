# LPU LIBRARY — Vercel RAG edition

Your existing LPU Library interface is kept in `frontend/index.html`. This edition connects its AI Librarian to a FastAPI RAG backend designed for Vercel.

## What is already in this project

- Existing single-page LPU Library UI, including the catalogue, saved books, subject explorer, knowledge graph, recommendations and AI comparison.
- FastAPI routes for chat, health, books, conversations and admin document ingestion.
- Retrieval-Augmented Generation (RAG): PDF/TXT/MD extraction, chunking, hosted embeddings, PostgreSQL `pgvector` similarity search, and grounded LLM answers with source excerpts.
- Persistent vector chunks and conversation history in PostgreSQL.
- Admin-key-protected document upload and a protected **Load 18 demo notes** action.
- 18 original synthetic topic notes covering AI, ML, deep learning, NLP, RAG, DSA, databases, networks, operating systems, Python, backend development, security, cloud, data engineering, recommenders and software engineering.

**Data warning:** the included corpus is a starter demo, not a full textbook collection or official LPU source. The catalogue titles and shelf labels are illustrative and must not be presented as verified LPU holdings or real physical locations. The uploaded documents are processed into searchable chunks in PostgreSQL; the original uploaded file is not retained as a downloadable archive.

**RAG is not model training.** It retrieves relevant passages from the documents you index and passes them to an LLM to generate a cited answer.

## Fast deployment — Vercel + Neon + AI Gateway

Vercel's current FastAPI runtime supports a FastAPI `app` exported from `index.py`; its Python runtime supports FastAPI. The frontend is mounted as a FastAPI static directory, with API routes registered before the final static mount. See the [FastAPI deployment guide](https://vercel.com/docs/frameworks/backend/fastapi).

### 1. Put this project on GitHub

1. Extract this ZIP into a folder.
2. Open that folder in VS Code.
3. Create a GitHub repository and push the **contents** of this folder (not the ZIP file).
4. In Vercel, choose **Add New → Project**, import that GitHub repository, and keep the Root Directory as `./`.

### 2. Add persistent PostgreSQL

In the Vercel project, open **Storage / Marketplace**, install the **Neon Postgres** integration, and create a database. Vercel's old Vercel Postgres product is no longer offered for new projects; new Postgres databases are connected through Marketplace providers. Ensure the project receives an environment variable named `DATABASE_URL`. Use the pooled connection string if the provider presents one for serverless workloads.

The backend creates the `vector` extension and required tables during application startup. Neon supports `pgvector`; if the database role cannot create the extension, run this once in the Neon SQL editor:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. Enable Vercel AI Gateway

In Vercel, open AI Gateway and create an API key. Add the following environment variables under **Project → Settings → Environment Variables**:

| Name | Value |
|---|---|
| `AI_GATEWAY_API_KEY` | Your AI Gateway API key |
| `CHAT_MODEL` | `openai/gpt-4o-mini` |
| `EMBEDDING_MODEL` | `openai/text-embedding-3-small` |
| `TOP_K` | `6` |
| `CHUNK_SIZE` | `1000` |
| `CHUNK_OVERLAP` | `160` |
| `MAX_UPLOAD_MB` | `4` |

AI Gateway exposes OpenAI-compatible endpoints and supports embeddings. The configured embedding model returns 1536-dimensional vectors, matching the database `vector(1536)` column. Check model availability and usage costs in your AI Gateway account before public use.

### 4. Set the admin-only upload secret

Generate a long random secret on your computer in PowerShell:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated value into a Vercel environment variable named `ADMIN_INGEST_KEY`. Do not paste the real key into HTML, GitHub, screenshots, or chat. The website asks an administrator to enter this key when seeding demo notes or uploading a document; the server validates it. This is a shared-secret admin gate for a project demo, not institutional SSO or a full multi-user identity system.

### 5. Deploy and seed the starter corpus

After adding all environment variables, redeploy the project. Open the Vercel deployment URL and check:

- `https://YOUR-APP.vercel.app/api/health` — should return `status: ok` after the database and AI Gateway are configured and at least one chunk exists.
- `https://YOUR-APP.vercel.app/docs` — FastAPI API documentation.

To make the preloaded notes available to public visitors, go to the AI Librarian section, enter the admin key, then click **Load 18 demo notes** once. It indexes the bundled synthetic notes into the shared Neon vector table. The chat is public; document ingestion is guarded by the admin key.

Afterward, upload authorized PDFs, TXT or Markdown files using the same admin controls. Keep uploads within the configured size limit.

## Environment variables for local testing

Copy `backend/.env.example` to `backend/.env` and fill in the same three secrets/credentials: `DATABASE_URL`, `AI_GATEWAY_API_KEY`, and `ADMIN_INGEST_KEY`. Do not commit `.env`.

In PowerShell from the project root:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000`. Use `Ctrl+C` to stop the local server. Local mode also uses the hosted AI Gateway and PostgreSQL; Ollama is not required.

## API routes

- `GET /api/health`
- `GET /api/books` and `GET /api/books/{book_id}`
- `POST /api/chat`
- `GET /api/conversations/{conversation_id}` and `DELETE /api/conversations/{conversation_id}`
- `POST /api/admin/ingest` — requires `X-Admin-Key`
- `POST /api/admin/ingest-demo` — requires `X-Admin-Key`

## Important limitations before a real LPU rollout

- Replace demo knowledge notes and catalogue records with material the university authorizes you to use.
- Replace placeholder shelf labels with verified location/seat data from the library.
- Add institutional sign-in and role-based authorization before using this for real students or staff. The current admin key is suitable only for a controlled demo.
- Add request rate limits, upload malware scanning, document retention/deletion rules, backups, monitoring and formal retrieval/answer evaluations.
- Set usage limits and monitor AI Gateway/database costs.

## Verification

Run the included lightweight checks from the repository root:

```powershell
python -m compileall -q index.py backend
python -m pytest -q
```

These checks validate syntax and static project wiring. They do not prove that the cloud services work; live RAG testing requires your own Neon connection string and AI Gateway key.
