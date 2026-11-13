# Hybrid Architecture: AI-Chatbot (Beven) + LociStoaDEV (Jkamaryt)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SwiftUI (LociStoaDEV)                         │
│  ┌──────────────┐         HTTP/HTTPS requests         ┌──────────────┐ │
│  │ ChatView.swift│ ────────────────────────────────▶ │              │
│  │ APIClient.swift│                                 │  FastAPI     │
│  │ SSEClient.swift│ ◀─────────────────────────────── │  AI-Chatbot  │
│  └──────────────┘        SSE streaming / REST          │  (Beven)     │
│                                                        └──────────────┘
│  ┌──────────────┐         ┌──────────────┐
│  │ SearchView.swift       │  Vector DB (Chroma)
│  │ ...                   │  (local)
│  └──────────────┘         └──────────────┘
└─────────────────────────────────────────────────────────────────────┘
```

## Repository Sources

| Folder | Repo | Purpose |
|--------|------|---------|
| `src/beven/` | `bmpofu-create/AI-Chatbot` | FastAPI backend + vector DB + local LLM |
| `src/jkamaryt/` | `Jkamaryt/LociStoaDEV` | SwiftUI iOS/macOS client |

## Endpoint Portability Assessment

### ✅ HIGHLY PORTABLE

1. **`GET /health`** — Simple health check. Portable.
2. **`GET /sources`** — Source metadata. Portable.
3. **`GET /highlights`** — Event data. Portable.
4. **`POST /ingest`** / `POST /ingest/{source}` — Admin-only. Optional portability (auth via `X-API-Key`).
5. **`GET /search`** — Vector search. Requires the AI-Chatbot vector DB to be running or a local backend (Chroma/pgvector) shared via network.

### ⚠️ MODERATELY PORTABLE

6. **`POST /chat`** — Streaming chat via **Server-Sent Events (SSE)**. This is the most complex endpoint:
   - Uses SSE format: `data: {...}\n\n`
   - Event types: `status`, `token`, `sources`, `done`, `error`
   - Requires streaming HTTP in the Swift client (URLSession with `URLSession.AsyncSequence` or manual SSE parsing).

### ❌ NOT PORTABLE (by design)

7. **Local LLM (Ollama/Transformers)** — Runs on the AI-Chatbot machine. The Swift app should NOT run the model; it only calls the API.

8. **Chroma DB** — Runs locally in the AI-Chatbot container. Swift app does not need access.

## Proposed Hybrid Architecture

### Backend (Beven) — `/src/beven/`
- FastAPI app with all RAG logic
- Ingestion + scheduling
- Vector store (Chroma)
- Local LLM inference
- Serves chat UI at `GET /`

### Frontend (Jkamaryt) — `/src/jkamaryt/`
- SwiftUI views adapted to consume the AI-Chatbot API
- `APIClient` for REST calls
- `SSEClient` for streaming chat
- `ChatView` to render conversation

### Communication
- REST endpoints: JSON over HTTP
- Streaming: SSE on `POST /chat`
- Auth: `X-API-Key` header for ingest endpoints (admin); chat is public

## Next Steps

1. **Stand up Beven backend** on a local machine / Docker host:
   - `docker-compose up -d db`
   - `uvicorn app.main:app --host 127.0.0.1 --port 8000`
2. **Run first ingest**: `POST /ingest`
3. **Verify** `GET /health` returns chunk count > 0.
4. **Implement Swift `APIClient`**:
   - GET endpoints → `URLSession` + `JSONDecoder`
   - POST /chat → `URLSession.AsyncSequence` for SSE or manual event parsing
5. **Implement Swift `ChatView`** using the SSE stream events.
6. **Add CORS**: set `CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173` (or port used by Swift simulator/webview).
7. **Wire up authentication** for admin endpoints (`/ingest`) via shared API key (e.g., environment or keychain).

---

*Assessment date: 2026-11-11 · Source repos: `bmpofu-create/AI-Chatbot`, `Jkamaryt/LociStoaDEV`*
