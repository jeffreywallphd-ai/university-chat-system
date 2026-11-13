"""
FastAPI application for the Michigan Tech campus chatbot (AI-Chatbot).

Endpoints:
- GET /          - Serve the static UI
- GET /health    - Health check
- GET /highlights - Upcoming events
- GET /sources    - List of configured sources
- POST /chat     - Streaming chat (SSE)
- POST /ingest   - Ingest a source
- POST /ingest/{source} - Bulk ingest
"""

from fastapi import FastAPI, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import settings
from .embed import embed
from .events import answer_about, upcoming_events, _lookup_message, _stream_chat
from .ingest import ingest_all, ingest_one
from .scraper import Doc
from .store import search, list_texts, upsert_doc, prune_source

app = FastAPI(title="NovusPal API", version="0.3.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def index():
    """Serve the static UI."""
    return {
        "message": "NovusPal API is running. Access the UI at /."
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        **settings.stats(),
        **settings.sources,
        **settings.admin_api_key
    }


@app.get("/highlights")
def highlights():
    """Upcoming events from the Michigan Tech calendar."""
    return {
        "events": upcoming_events(),
        "count": len(upcoming_events())
    }


@app.get("/sources")
def sources():
    """List all configured sources."""
    return {
        "sources": settings.SOURCES,
        "total": len(settings.SOURCES)
    }


@app.post("/chat")
def chat(body: ChatIn):
    """Streaming chat endpoint using Server-Sent Events."""
    return StreamingResponse(
        generate(body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )


@app.post("/ingest")
def ingest_all():
    """Ingest all configured sources."""
    return {
        "status": "started",
        "sources": list(settings.SOURCES),
        "message": "Ingestion started"
    }


@app.post("/ingest/{source_name}")
def ingest_one(source_name: str):
    """Ingest a single source by name."""
    if source_name not in settings.SOURCES:
        raise HTTPException(status_code=404, detail=f"Unknown source: {source_name}")
    result = ingest_one(source_name)
    return result


@app.get("/search")
def search(query: str, k: int = 5, category: str | None = None):
    """Search for pages using vector search."""
    results = search(query, k=k, category=category)
    return {
        "query": query,
        "results": results,
        "count": len(results)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
