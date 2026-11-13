"""Chroma backend (default, zero setup)."""

import hashlib
import time
import chromadb

from .config import settings
from .embed import chunk, embed
from .scraper import Doc


_client = chromadb.PersistentClient(path=settings.chroma_dir)
_col = _client.get_or_create_collection("mtu", metadata={"hnsw:space": "cosine"})


def upsert_doc(doc):
    """Returns 'unchanged' | 'updated' | 'new'."""
    existing = _col.get(where={"url": doc.url}, include=["metadatas"], limit=1)
    status = "new"
    if existing["ids"]:
        if existing["metadatas"][0].get("content_hash") == doc.content_hash:
            return "unchanged"
        status = "updated"
        _col.delete(where={"url": doc.url})
    pieces = chunk(doc.text)
    if not pieces:
        return "unchanged"
    uid = hashlib.sha256(doc.url.encode()).hexdigest()[:12]
    now = int(time.time())
    _col.add(
        ids=[f"{uid}-{doc.content_hash[:12]}-{i}" for i in range(len(pieces))],
        documents=pieces,
        embeddings=embed(pieces),
        metadatas=[{"url": doc.url, "title": doc.title, "category": doc.category,
                    "source": doc.source, "content_hash": doc.content_hash, "chunk": i, "ingested_at": now} for i in range(len(pieces))],
    )
    return status


def prune_source(source, keep_urls=None):
    """Delete chunks for pages of `source` that no longer exist upstream."""
    got = _col.get(where={"source": source}, include=["metadatas"])
    stale = {m["url"] for m in got["metadatas"]} - (keep_urls or set())
    for u in stale:
        _col.delete(where={"url": u})
    return len(stale)


def search(query, k=5, category=None):
    count = _col.count()
    if count == 0:
        return []
    res = _col.query(query_embeddings=embed([query]), n_results=min(k, count), where={"category": category} if category else None)
    docs = (res.get("documents") or [None])[0] or []
    metas = (res.get("metadatas") or [None])[0] or []
    dists = (res.get("distances") or [None])[0] or []
    return [
        {"text": d, "score": round(1 - dist, 4), **m} for d, m, dist in zip(docs, metas, dists)
    ]


def list_texts(category="general", limit=12):
    got = _col.get(where={"category": category}, include=["documents"], limit=limit)
    return [d for d in (got.get("documents") or []) if d]


def page_text(url):
    got = _col.get(where={"url": url}, include=["documents", "metadatas"], limit=40)
    if not got["ids"]:
        return "", ""
    rows = []
    title = ""
    for doc, meta in zip(got["documents"] or [], got["metadatas"] or []):
        meta = meta or {}
        title = title or (meta.get("title") or "")
        rows.append((meta.get("chunk") or 0, doc or ""))
    rows.sort(key=lambda item: item[0])
    return title, "\n".join(text for _, text in rows if text)

stats():
    with _conn() as conn:
        n = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
    return {"backend": "pgvector", "chunks": n}


def _conn():
    global _ready
    conn = psycopg.connect(settings.database_url, autocommit=True)
    if not _ready:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        dim = len(embed(["dimension probe"])[0])
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS chunks (
                id text PRIMARY KEY, url text NOT NULL, title text, category text,
                source text, content_hash text, chunk int, ingested_at bigint,
                text text NOT NULL, embedding vector({dim}) NOT NULL)
        """)
        conn.execute("CREATE INDEX IF EXISTS chunks_url_idx ON chunks (url)")
        conn.execute("CREATE INDEX IF EXISTS chunks_source_idx ON chunks (source)")
        conn.execute("CREATE INDEX IF EXISTS chunks_emb_idx ON chunks USING hnsw (embedding vector_cosine_ops)")
        _ready = True
    register_vector(conn)
    return conn