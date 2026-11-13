"""
Local embeddings and text chunking.

Runs sentence-transformers on this machine to generate vector embeddings
for page content during ingest and for user queries during search.
"""

from sentence_transformers import SentenceTransformer
import threading

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()


def embed(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of text strings."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model.encode(texts).tolist()


def chunk(text: str, size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks."""
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 1 <= size:
            cur = f"{cur}\n{p}" if cur else p
        else:
            if cur:
                chunks.append(cur)
            while len(p) > size:
                chunks.append(p[:size])
                p = p[size - overlap:]
            cur = p
    if cur:
        chunks.append(cur)
    return chunks