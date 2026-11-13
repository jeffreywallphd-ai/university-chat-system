"""
Local retrieval-augmented answering (RAG) pipeline.

Uses LangChain to build prompts and run a local model. Retrieves relevant
campus page chunks from a vector store (Chroma / pgvector), builds a
response, and streams tokens back.
"""

import os
import threading
from collections.abc import Iterator

os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from .config import settings
from .embed import embed
from .events import answer_about
from . import store

SYSTEM = """You are MTU compass assistant, a student assistant for Michigan Technological University.
Talk like a knowledgeable friend on campus: warm, specific, and complete.

Campus notes are included with the question. They are your only source of campus facts.
- Open with the answer itself, in the first sentence.
- Copy clock times, dates, phone numbers, and prices exactly as written in the notes. Do not restate a schedule in your own words.
- Each note is a separate section. Do not combine days or hours from different notes.
- If the notes do not contain the fact, say you cannot confirm it. Never invent dates, hours, prices, phone numbers, or policies.
- Do not include citation markers like [1], URLs, or a sources list. The app shows sources separately.
- Write short paragraphs. Use a brief list only when the student needs steps."""

_chain = None
_chain_lock = threading.Lock()


def get_chain():
    """Get or lazily initialize the LangChain chain for the local model."""
    global _chain
    if _chain is None:
        with _chain_lock:
            if _chain is None:
                prompt = ChatPromptTemplate.from_messages([
                    ("system", SYSTEM),
                    ("human", "Campus notes:\n{context}\n\nQuestion: {question}"),
                ])
                llm = _build_llm()
                _chain = prompt | llm | StrOutputParser()
    return _chain


def _build_llm():
    """Build a local LLM: Ollama or Hugging Face Transformers."""
    if settings.llm_backend == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=settings.llm_model, base_url=settings.ollama_base_url)
    else:
        from langchain_huggingface import HuggingFacePipeline
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        tokenizer = AutoTokenizer.from_pretrained(settings.llm_model)
        model = AutoModelForCausalLM.from_pretrained(settings.llm_model)
        pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=settings.max_new_tokens)
        return HuggingFacePipeline(pipeline=pipe)


def retrieve(query: str, k: int = 4, category: str | None = None) -> list[dict]:
    """Retrieve relevant page chunks."""
    return store.search(query, k=k, category=category)


def stream_chat(message: str, category: str | None = None, top_k: int = 4, history: list[dict] | None = None) -> Iterator[dict]:
    """Stream chat response as SSE events."""
    yield {"type": "status", "status": "processing"}
    hits = retrieve(message, k=top_k, category=category)
    context = "\n\n".join(h.get("text", "") for h in hits if h.get("text"))
    chain = get_chain()
    answer = chain.invoke({
        "context": context,
        "question": message,
    })
    yield {"type": "token", "text": answer}
    yield {"type": "sources", "sources": [
        {"title": h.get("title"), "url": h.get("url")} for h in hits if h.get("url")
    ]}
    yield {"type": "done"}


def warm_model() -> None:
    """Warm up the model to avoid first-request latency."""
    pass