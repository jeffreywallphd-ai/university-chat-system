"""Chroma backend (default, zero setup)."""
import hashlib
import time

import chromadb

from .config import settings
from .embed import chunk, embed
from .scraper import Doc

_client = chromadb.PersistentClient(path=settings.chroma_dir)
_col = _client.get_or_create_collection("mtu", metadata={"hnsw:space": "cosine"})


def upsert_doc(doc: Doc) -> str:
    """Returns 'unchanged' | 'updated' | 'new'."""
    existing = _col.get(where={"url": doc.url}, include=["metadatas"], limit=1)
    status = "new"
    if existing["ids"]:
        if existing["metadatas"][0].get("content_hash") == doc.content_hash:
            return "unchanged"
        status = "updated"
        _col.delete(where={"url": doc.url})  # drop old chunks so removed text disappears
    pieces = chunk(doc.text)
    if not pieces:
        return "unchanged"
    uid = hashlib.sha256(doc.url.encode()).hexdigest()[:12]
    now = int(time.time())
    _col.add(
        ids=[f"{uid}-{doc.content_hash[:12]}-{i}" for i in range(len(pieces))],
        documents=pieces,
        embeddings=embed(pieces),
        metadatas=[{
            "url": doc.url, "title": doc.title, "category": doc.category,
            "source": doc.source, "content_hash": doc.content_hash,
            "chunk": i, "ingested_at": now,
        } for i in range(len(pieces))],
    )
    return status


def prune_source(source: str, keep_urls: set[str]) -> int:
    """Delete chunks for pages of `source` that no longer exist upstream."""
    got = _col.get(where={"source": source}, include=["metadatas"])
    stale = {m["url"] for m in got["metadatas"]} - keep_urls
    for u in stale:
        _col.delete(where={"url": u})
    return len(stale)


def search(query: str, k: int = 5, category: str | None = None) -> list[dict]:
    count = _col.count()
    if count == 0:
        return []
    res = _col.query(
        query_embeddings=embed([query]),
        n_results=min(k, count),
        where={"category": category} if category else None,
    )
    docs = (res.get("documents") or [None])[0] or []
    metas = (res.get("metadatas") or [None])[0] or []
    dists = (res.get("distances") or [None])[0] or []
    return [
        {"text": d, "score": round(1 - dist, 4), **m}
        for d, m, dist in zip(docs, metas, dists)
    ]


def list_texts(category: str, limit: int = 12) -> list[str]:
    got = _col.get(where={"category": category}, include=["documents"], limit=limit)
    return [d for d in (got.get("documents") or []) if d]


def page_text(url: str) -> tuple[str, str]:
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


def stats() -> dict:
    return {"backend": "chroma", "chunks": _col.count()}
