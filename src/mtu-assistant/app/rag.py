"""Local retrieval-augmented answering.

Memory is a vector store (Chroma, or Postgres/pgvector). A graph database is
not used: questions look up similar page text, not relationships between
records. Chroma and pgvector store vectors; they do not create them.
Embeddings are computed locally in app/embed.py.

LangChain builds the prompt and runs the model. The model itself is hosted
here: Hugging Face Transformers by default, or Ollama on localhost when
LLM_BACKEND=ollama. Retrieved campus text is not sent to an external API.
"""
import datetime as dt
import os
import re
import threading
from collections.abc import Iterator

os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
os.environ.setdefault("LANGSMITH_TRACING", "false")
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

_TIME_RE = re.compile(r"\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)", re.I)
_RANGE_RE = re.compile(
    r"\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)\s*(?:[–—\-]|to)\s*\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)",
    re.I,
)
_PHONE_RE = re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b")
_DAY_RE = re.compile(
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    re.I,
)
_OTHER_SERVICE = re.compile(
    r"velodrome|coffee|caf[eé]|testing center|faculty excellence|michigan tech it\b",
    re.I,
)
# More specific places first. "library" is last so "library cafe" stays the cafe.
_SERVICE_PATTERNS = (
    ("cafe", re.compile(r"\b(cafes?|coffee|velodrome)\b", re.I)),
    ("testing", re.compile(r"testing center", re.I)),
    ("archives", re.compile(r"archive", re.I)),
    ("reference", re.compile(r"reference", re.I)),
    ("overnight", re.compile(r"overnight|24/7", re.I)),
    ("library", re.compile(r"\blibrary\b", re.I)),
)
_HEADING_FOR = {
    "cafe": re.compile(r"velodrome|coffee|caf[eé]", re.I),
    "testing": re.compile(r"testing", re.I),
    "archives": re.compile(r"archive", re.I),
    "reference": re.compile(r"reference|research", re.I),
    "overnight": re.compile(r"overnight|opie|24/7|24-hour", re.I),
    "library": re.compile(r"library services", re.I),
}
_STOP = {
    "what", "are", "the", "and", "for", "how", "do", "to", "a", "an", "is", "of",
    "on", "my", "can", "where", "when", "does", "with", "about", "that", "this",
    "from", "your", "have", "there",
}
_chain = None
_load_lock = threading.Lock()
_gen_lock = threading.Lock()
_tokenizer = None
_model = None


def runtime_info() -> dict:
    return {"llm_backend": settings.llm_backend, "llm_model": settings.llm_model}


def _prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM),
        (
            "human",
            "{history}Campus notes:\n\n{context}\n\n"
            "Student question: {question}\n\n"
            "Answer the student directly. State the specific facts. "
            "Do not tell them to look up the notes.",
        ),
    ])


def _canon(url: str) -> str:
    url = (url or "").split("#")[0].rstrip("/")
    if url.endswith("/index.html"):
        url = url[: -len("/index.html")]
    return url


def _is_fact_line(line: str) -> bool:
    return bool(
        _TIME_RE.search(line)
        or re.search(r"\b(closed|24/7|by appointment)\b", line, re.I)
    )


def _is_heading(line: str) -> bool:
    plain = re.sub(r"[|*]", " ", line).strip()
    return bool(plain) and not _is_fact_line(line) and len(plain) <= 90


def _split_sections(text: str) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []
    sections: list[str] = []
    buf: list[str] = []
    saw_fact = False
    for line in lines:
        if buf and saw_fact and _is_heading(line):
            sections.append("\n".join(buf))
            buf = [line]
            saw_fact = False
        else:
            buf.append(line)
            saw_fact = saw_fact or _is_fact_line(line)
    if buf:
        sections.append("\n".join(buf))
    kept = [s for s in sections if len(s) >= 40]
    return kept or ["\n".join(lines)]


def _fold(text: str) -> str:
    return (text or "").lower().replace("é", "e").replace("è", "e")


def _asked_service(message: str) -> str | None:
    folded = _fold(message)
    for name, pattern in _SERVICE_PATTERNS:
        if pattern.search(folded):
            return name
    return None


def _section_matches(service: str, text: str) -> bool:
    sample = "\n".join(_fold(text).splitlines()[:6])
    return bool(_HEADING_FOR[service].search(sample))


def _standing_hours(text: str) -> bool:
    return bool(_TIME_RE.search(text)) and not re.search(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b",
        text,
        re.I,
    )


def _query_terms(message: str) -> set[str]:
    return {
        w for w in re.findall(r"[a-z]{4,}", message.lower())
        if w not in _STOP
    }


def _heading_text(text: str) -> str:
    return re.sub(r"[|*]", " ", text.splitlines()[0]).strip()


def _line_keys(text: str) -> set[str]:
    keys = set()
    for line in text.splitlines():
        key = re.sub(r"[^a-z0-9]+", "", line.lower())
        if len(key) >= 8:
            keys.add(key)
    return keys


def _usable_section(text: str) -> bool:
    stripped = text.rstrip()
    if len(stripped) < 80:
        return False
    if re.search(r"\b(with|the|and|or|to|a|an|for|of)$", stripped, re.I):
        return False
    return True


def _retrieve(message: str, k: int, category: str | None) -> list[dict]:
    hits = store.search(message, k=k, category=category)
    if not hits and category:
        hits = store.search(message, k=k, category=None)
    return hits


def _select_notes(message: str, hits: list[dict], limit: int = 3) -> list[dict]:
    """Keep the sections that match the question, not every schedule on the page."""
    seen: set[tuple[str, str]] = set()
    candidates: list[dict] = []
    for hit in hits:
        text = (hit.get("text") or "").strip()
        url = hit.get("url") or ""
        if not text:
            continue
        for section in _split_sections(text):
            key = (_canon(url), section[:160])
            if key in seen:
                continue
            seen.add(key)
            candidates.append({
                "title": (hit.get("title") or url or "Campus page").strip(),
                "url": url,
                "text": section,
                "score": 0.0,
            })
    if not candidates:
        return []

    vectors = embed([message] + [c["text"][:800] for c in candidates])
    query = vectors[0]
    terms = _query_terms(message)
    ranked: list[tuple[float, dict]] = []
    for note, vec in zip(candidates, vectors[1:]):
        score = sum(a * b for a, b in zip(query, vec))
        heading = _heading_text(note["text"]).lower()
        if terms and any(term in heading for term in terms):
            score += 0.06
        service = _asked_service(message)
        if service and not _section_matches(service, note["text"]):
            keep_overnight = service == "library" and re.search(r"24/7|overnight", note["text"], re.I)
            if not keep_overnight:
                score -= 0.25
        elif _OTHER_SERVICE.search(heading) and not _OTHER_SERVICE.search(message):
            score -= 0.12
        if _standing_hours(note["text"]) and not re.search(
            r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|break|holiday)\b",
            message,
            re.I,
        ):
            score += 0.08
        body = note["text"].lower()
        if (
            re.search(r"\bregist", message, re.I)
            and not re.search(r"\b(drop|withdraw)", message, re.I)
            and body.count("drop") > body.count("regist")
        ):
            score -= 0.12
        note["score"] = round(score, 4)
        ranked.append((score, note))
    ranked.sort(key=lambda item: item[0], reverse=True)
    service = _asked_service(message)
    pool = ranked
    if service:
        ranked = [item for item in pool if _section_matches(service, item[1]["text"])]
        if not ranked:
            return []
    best = ranked[0][0]
    if best < (0.35 if service else 0.48):
        return []

    picked: list[dict] = []
    covered: set[str] = set()
    for score, note in ranked:
        if not _usable_section(note["text"]):
            continue
        keys = _line_keys(note["text"])
        if keys and keys <= covered:
            continue
        gap = 0.45 if service else 0.07
        if picked and score < best - gap:
            break
        picked.append(note)
        covered |= keys
        if len(picked) >= limit:
            break
    if service in (None, "library", "overnight") and re.search(
        r"\b(hours?|library|open|overnight)\b", message, re.I
    ):
        have = {n["text"][:80] for n in picked}
        for score, note in pool:
            if score < 0.45 or len(picked) >= limit + 1:
                break
            if note["text"][:80] in have or not _usable_section(note["text"]):
                continue
            if not re.search(r"24/7|overnight", note["text"], re.I):
                continue
            if not any(_canon(note["url"]) == _canon(p["url"]) for p in picked):
                continue
            picked.append(note)
            have.add(note["text"][:80])

    if service:
        return picked
    headed = [n for n in picked if any(term in _heading_text(n["text"]).lower() for term in terms)]
    if terms and headed:
        urls = {_canon(n["url"]) for n in headed}
        picked = [
            n for n in picked
            if n in headed or (
                _canon(n["url"]) in urls
                and not _OTHER_SERVICE.search(_heading_text(n["text"]))
            )
        ]
    return picked


def _history_text(history) -> str:
    if not history:
        return ""
    lines = []
    for turn in list(history)[-6:]:
        who = "Student" if turn.role == "user" else "NovusPal"
        lines.append(f"{who}: {turn.content[:700]}")
    return "Conversation so far:\n" + "\n".join(lines) + "\n\n"


def _context(notes: list[dict]) -> str:
    return "\n\n".join(f"Note {i} — {n['title']}\n{n['text']}" for i, n in enumerate(notes, 1))


def _load_transformers():
    global _tokenizer, _model
    if _model is not None:
        return _tokenizer, _model
    with _load_lock:
        if _model is None:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            _tokenizer = AutoTokenizer.from_pretrained(settings.llm_model)
            _model = AutoModelForCausalLM.from_pretrained(
                settings.llm_model,
                dtype=torch.float32,
            )
            _model.eval()
            if _tokenizer.pad_token_id is None:
                _tokenizer.pad_token = _tokenizer.eos_token
    return _tokenizer, _model


def warm_model() -> None:
    try:
        if settings.llm_backend == "transformers":
            _load_transformers()
        else:
            _get_chain()
    except Exception:
        import logging
        logging.getLogger("novuspal").exception("local model warmup failed")


class _LocalChatModel(Runnable):
    """Instruct model loaded with Transformers. Generation stays on this machine."""

    def invoke(self, input, config=None, **kwargs) -> str:  # noqa: A002
        return "".join(self.stream(input, config, **kwargs))

    def stream(self, input, config=None, **kwargs) -> Iterator[str]:  # noqa: A002
        from transformers import TextIteratorStreamer

        tokenizer, model = _load_transformers()
        messages = []
        for message in input.to_messages():
            role = {"system": "system", "human": "user", "ai": "assistant"}.get(message.type, "user")
            messages.append({"role": role, "content": message.content})
        prompt_text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        streamer = TextIteratorStreamer(
            tokenizer, skip_prompt=True, skip_special_tokens=True
        )
        encoded = tokenizer(prompt_text, return_tensors="pt")
        gen_kwargs = dict(
            **encoded,
            streamer=streamer,
            max_new_tokens=settings.max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
        )

        def _run() -> None:
            import torch
            with torch.no_grad():
                model.generate(**gen_kwargs)

        threading.Thread(target=_run, daemon=True).start()
        for piece in streamer:
            if piece:
                yield piece


def _build_chain():
    prompt = _prompt()
    if settings.llm_backend == "ollama":
        from langchain_ollama import ChatOllama

        llm = ChatOllama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=0,
            num_predict=settings.max_new_tokens,
        )
        return prompt | llm | StrOutputParser()
    if settings.llm_backend != "transformers":
        raise RuntimeError(
            f"Unknown LLM_BACKEND {settings.llm_backend!r}. Use transformers or ollama."
        )
    return prompt | _LocalChatModel() | StrOutputParser()


def _get_chain():
    global _chain
    if _chain is None:
        with _load_lock:
            if _chain is None:
                _chain = _build_chain()
    return _chain


def _norm_fact(text: str) -> str:
    text = text.lower().replace("–", "-").replace("—", "-").replace(".", "")
    text = re.sub(r"\ba\.?m\.?\b", "am", text)
    text = re.sub(r"\bp\.?m\.?\b", "pm", text)
    return re.sub(r"\s+", "", text)


def _format_section(text: str) -> str:
    lines = []
    for raw in text.splitlines():
        parts = [re.sub(r"\s+", " ", part).strip(" |*") for part in raw.split("|")]
        parts = [part for part in parts if part]
        if not parts:
            continue
        if len(parts) == 1:
            if re.fullmatch(r"hours\.\.\.?", parts[0], re.I):
                continue
            lines.append(parts[0])
        else:
            lines.append(f"{parts[0]}: {' — '.join(parts[1:])}")
    return "\n".join(lines)


def _as_date(month: str, day: str, year: int | None = None) -> dt.date | None:
    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    try:
        return dt.date(year or dt.date.today().year, months[month[:3].lower()], int(day))
    except (KeyError, ValueError):
        return None


def _stale_section(text: str) -> bool:
    """A schedule whose every timed row names a date already past."""
    today = dt.date.today()
    dated = False
    for line in text.splitlines():
        if not (_TIME_RE.search(line) or re.search(r"\b(closed|24/7)\b", line, re.I)):
            continue
        found = [
            _as_date(match.group(1), match.group(2))
            for match in re.finditer(
                r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})\b",
                line,
                re.I,
            )
        ]
        found = [item for item in found if item]
        if not found:
            return False
        dated = True
        if any(item >= today for item in found):
            return False
    return dated


def _parse_hours(text: str) -> tuple[str, list[tuple[str, str]], str]:
    title = ""
    rows: list[tuple[str, str]] = []
    extra: list[str] = []
    for line in _format_section(text).splitlines():
        match = re.match(r"^(.+?):\s+(.+)$", line)
        factual = bool(
            match and (_TIME_RE.search(line) or re.search(r"\b(closed|24/7)\b", line, re.I))
        )
        if factual and match:
            rows.append((match.group(1).strip(), re.sub(r"\s+", " ", match.group(2)).strip()))
            continue
        if re.fullmatch(r"hours for all service points|hours\.\.\.?", line, re.I):
            continue
        if not rows and not title:
            title = line
        elif rows:
            extra.append(line)
    return title, rows, " ".join(extra)


def _soon(text: str, within_days: int = 21) -> bool:
    today = dt.date.today()
    upcoming = []
    for match in re.finditer(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})\b",
        text,
        re.I,
    ):
        found = _as_date(match.group(1), match.group(2))
        if found and found >= today:
            upcoming.append(found)
    if not upcoming:
        return False
    return min(upcoming) <= today + dt.timedelta(days=within_days)


def _who(message: str, title: str) -> str:
    names = {
        "cafe": "Velodrome Coffee Company",
        "library": "The library",
        "overnight": "Opie and the second floor",
        "reference": "Research and reference",
        "archives": "The archives",
        "testing": "The testing center",
    }
    service = _asked_service(message) or _asked_service(title)
    if service in names:
        return names[service]
    cleaned = re.sub(r"\s+", " ", title).strip(" *")
    return cleaned or "That service"


def _hours_sentence(name: str, rows: list[tuple[str, str]]) -> str:
    bits = []
    for days, hours in rows:
        if re.fullmatch(r"closed", hours, re.I):
            bits.append(f"closed {days}")
        else:
            bits.append(f"{days} {hours}")
    if not bits:
        return ""
    listed = bits[0] if len(bits) == 1 else ", ".join(bits[:-1]) + ", and " + bits[-1]
    if len(rows) == 1 and "24/7" in rows[0][1]:
        hours = rows[0][1]
        verb = "are" if re.search(r"\band\b", name) else "is"
        return f"{name} {verb} {hours[0].lower()}{hours[1:]}."
    if all(not bit.startswith("closed") for bit in bits):
        return f"{name} is open {listed}."
    return f"{name} keeps these hours: {listed}."


_WEEK = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def _row_covers(label: str, day: str) -> bool:
    label = label.lower()
    if day in label:
        return True
    found = [name for name in _WEEK if name in label]
    if len(found) < 2 or not re.search(r"[-–—]", label):
        return False
    return _WEEK.index(found[0]) <= _WEEK.index(day) <= _WEEK.index(found[-1])


def _mentions_day(text: str, day: str) -> bool:
    short = day[:3]
    return bool(re.search(rf"\b({day}|{short})\b\.?", text, re.I))


def _schedule_answer(message: str, notes: list[dict], focus: str | None = None) -> str | None:
    heard = focus or message
    if not re.search(r"\b(hours?|open|closed|overnight)\b", heard, re.I):
        return None
    current = [n for n in notes if not _stale_section(n["text"])]
    parsed = []
    for note in current:
        title, rows, extra = _parse_hours(note["text"])
        if len(rows) >= 2 or any("24/7" in hours for _, hours in rows):
            parsed.append((note, title, rows, extra))
    if not parsed:
        return None
    service = _asked_service(message)
    day_match = re.search(
        r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        message,
        re.I,
    )
    day = day_match.group(1).lower() if day_match else ""
    standing = [item for item in parsed if _standing_hours(item[0]["text"]) and item is not None]
    overnight = [
        item for item in parsed
        if re.search(r"overnight|24/7|24-hour", _fold(_heading_text(item[0]["text"])))
    ]
    dated = [item for item in parsed if item not in standing and item not in overnight]
    standing = [item for item in standing if item not in overnight]
    parts: list[str] = []
    focus = overnight if service == "overnight" else standing or dated
    if focus:
        note, title, rows, extra = focus[0]
        if day:
            rows = [row for row in rows if _row_covers(row[0], day)]
        sentence = _hours_sentence(_who(message, title), rows)
        if sentence:
            parts.append(sentence)
        if service == "overnight" and extra and re.search(r"how|enter|access|get in", message, re.I):
            parts.append(extra.split(". ")[0].strip() + ("" if extra.endswith(".") else "."))
    if service != "overnight":
        for note, _title, rows, _extra in dated:
            if not (_soon(note["text"]) or re.search(r"break|holiday|nov|dec|jan", message, re.I)):
                continue
            shown = rows
            if day:
                shown = [
                    row for row in rows
                    if _mentions_day(f"{row[0]} {row[1]}", day)
                ]
                if not shown:
                    continue
            change = "; ".join(f"{days}, {hours}" for days, hours in shown)
            parts.append(f"Those hours change on these dates: {change}.")
            break
        if service == "library" and overnight and not day:
            _note, _title, rows, _extra = overnight[0]
            detail = rows[0][1] if rows else "Open 24/7 with valid HuskyCard"
            parts.append(f"Opie and the second floor are {detail[0].lower()}{detail[1:]}.")
    spoken = "\n".join(part for part in parts if part).strip()
    return spoken or None


def _facts_match(answer: str, notes: list[dict]) -> bool:
    source = "\n".join(n["text"] for n in notes)
    source_norm = _norm_fact(source)
    source_lines = [_norm_fact(line) for line in source.splitlines()]
    for match in list(_RANGE_RE.finditer(answer)) + list(_PHONE_RE.finditer(answer)):
        if _norm_fact(match.group(0)).replace("to", "-") not in source_norm:
            return False
    for sentence in re.split(r"[.\n]", answer):
        days = [day.lower() for day in _DAY_RE.findall(sentence)]
        times = [_norm_fact(item.group(0)) for item in _RANGE_RE.finditer(sentence)]
        if not days or not times:
            continue
        if not any(
            all(day in line for day in days) and all(tm in line for tm in times)
            for line in source_lines
        ):
            return False
    return True


def _sources(notes: list[dict]) -> list[dict]:
    found = []
    seen = set()
    for note in notes:
        url = note.get("url") or ""
        key = _canon(url)
        if not url or key in seen:
            continue
        seen.add(key)
        found.append({"n": len(found) + 1, "title": note["title"], "url": url})
    return found


def _lookup_message(message: str, history) -> str:
    """Fold a short follow-up into the previous question so retrieval stays on topic."""
    previous = ""
    for turn in reversed(list(history or [])):
        role = turn.role if hasattr(turn, "role") else turn.get("role")
        content = turn.content if hasattr(turn, "content") else turn.get("content", "")
        if role == "user" and content:
            previous = content
            break
    if not previous or len(message.split()) > 8:
        return message
    previous_place = _asked_service(previous)
    this_place = _asked_service(message)
    if this_place and this_place != previous_place:
        return message
    followup = re.search(
        r"^(and|also|what about|how about|then)\b"
        r"|^(on )?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
        r"|\b(it|that one|those|them)\b",
        message,
        re.I,
    )
    if followup or not _terms(message):
        return f"{previous}. {message}"
    return message


def _url_bias(message: str, url: str) -> float:
    question = message.lower()
    path = url.lower()
    bias = 0.0
    subjects = (
        "math", "chemistry", "physics", "computing", "writing", "biology",
        "geology", "engineering", "business",
    )
    named = [subject for subject in subjects if re.search(rf"\b{subject}\b", question)]
    if named:
        if any(subject in path for subject in named):
            bias += 0.22
        elif "/learning-centers" in path:
            bias -= 0.08
    elif re.search(r"tutor|learning center", question) and "/learning-centers" in path:
        bias += 0.08
    if re.search(r"\bstud(y|ying)\b", question):
        if "/library/about" in path and "map" not in path:
            bias += 0.14
        elif "/library/" in path and not any(part in path for part in ("off-campus", "/gis/", "archives", "/map/")):
            bias += 0.05
        if "midterm" in path:
            bias -= 0.12
        if "off-campus" in path:
            bias -= 0.08
    if re.search(r"caf|coffee|velodrome", question) and ("hour" in path or "velodrome" in path):
        bias += 0.22
    elif re.search(r"\bhours?\b", question) and "hour" in path:
        bias += 0.2
    if re.search(r"regist", question) and not re.search(r"drop|withdraw", question):
        if path.rstrip("/").endswith("/registration") or path.endswith("/registration/index.html"):
            bias += 0.06
        if "add-drop" in path:
            bias -= 0.1
    if re.search(r"hous|residence hall|dorm|roommate", question) and "/residential-living/" in path:
        bias += 0.2
    if re.search(r"career fair", question):
        plain = path.rstrip("/")
        if plain.endswith("/career/fair") or plain.endswith("/career/fair/index.html"):
            bias += 0.35
        elif "/career/fair/employers" in path:
            bias -= 0.25
    elif re.search(r"career|internship|\bresume\b", question) and "/career/" in path:
        bias += 0.2
    if re.search(r"\btuition\b", question) and "tuition" in path:
        bias += 0.2
    if re.search(r"financial aid|scholarship|\bfafsa\b", question) and "/finaid/" in path:
        bias += 0.2
    if re.search(r"\bwifi\b|password|it help|huskymail", question) and "/it/" in path:
        bias += 0.18
    if re.search(r"counsel|well-being|wellbeing|mental health", question) and "/well-being/" in path:
        bias += 0.2
    if re.search(r"police|public safety|emergency", question) and "/publicsafety/" in path:
        bias += 0.2
    if re.search(r"\bgym\b|recreation|intramural|fitness", question) and "recreation" in path:
        bias += 0.18
    return bias


def _best_page(message: str, hits: list[dict]) -> dict | None:
    best = None
    best_score = -1.0
    seen: set[str] = set()
    for hit in hits:
        url = hit.get("url") or ""
        key = _canon(url)
        if not url or key in seen:
            continue
        seen.add(key)
        score = float(hit.get("score") or 0) + _url_bias(message, url)
        if score > best_score:
            best_score = score
            best = hit
    if not best or best_score < 0.45:
        return None
    return best


def _terms(text: str) -> set[str]:
    generic = {
        "student", "students", "campus", "available", "learning", "center",
        "phone", "number", "where", "about", "class", "classes", "help",
        "need", "there", "michigan", "what", "when", "your", "with", "from",
        "that", "this", "have", "does",
    }
    terms = set()
    for word in re.findall(r"[a-z]{4,}", text.lower()):
        if word in generic:
            continue
        terms.add(word if len(word) < 6 else word[:5])
    return terms


def _page_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip(" |-")
        if len(line) >= 25:
            lines.append(line)
    return lines


_DAY_OR_MONTH = re.compile(
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"january|february|march|april|may|june|july|august|september|october|november|december)\b",
    re.I,
)
_DATELIKE = re.compile(
    _DAY_OR_MONTH.pattern + r"|"
    r"\b(noon|midnight|\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?))\b",
    re.I,
)


def _when_answer(question: str, text: str) -> str:
    """A date listed under a short heading, spoken as one sentence."""
    if not re.search(r"\b(when|what day|what date)\b", question, re.I):
        return ""
    wanted = _terms(question)
    if not wanted:
        return ""
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip(" |-")
        if line:
            lines.append(line)
    today = dt.date.today()
    best_at = -1
    best_score = 0.0
    for index, line in enumerate(lines):
        if len(line) > 70 or (_TIME_RE.search(line) and not _DAY_OR_MONTH.search(line)):
            continue
        score = _line_rank(wanted, line)
        window = lines[index + 1:index + 4]
        if score <= best_score or not any(_DAY_OR_MONTH.search(item) for item in window):
            continue
        blob = " ".join([line, *window])
        years = [int(year) for year in re.findall(r"\b(20\d{2})\b", blob)]
        if years and max(years) < today.year:
            continue
        best_score = score
        best_at = index
    if best_at < 0:
        return ""
    heading = lines[best_at]
    details = []
    for line in lines[best_at + 1:best_at + 4]:
        if len(line) > 70 and not _DATELIKE.search(line):
            break
        if _DATELIKE.search(line) or (details and len(line) <= 50):
            details.append(line)
            continue
        break
    when = [line for line in details if _DATELIKE.search(line)]
    place = next((line for line in details if line not in when), "")
    if not when:
        return ""
    where = f" at the {place}" if place else ""
    return f"{heading} is {', '.join(when)}{where}."


def _money_answer(question: str, text: str) -> str:
    """One row from an expenses table, with the resident columns named on the page."""
    if not re.search(r"\b(tuition|cost|fee|fees)\b", question, re.I):
        return ""
    if "michigan residents" not in text.lower() or "non-michigan" not in text.lower():
        return ""
    label_word = "tuition" if re.search(r"tuition", question, re.I) else ""
    for raw in text.splitlines():
        cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
        cells = [cell for cell in cells if cell and not re.fullmatch(r"-+", cell)]
        if len(cells) < 3:
            continue
        label = re.sub(r"\d+(?:,\d+)?$", "", cells[0]).strip()
        if label_word and label_word not in label.lower():
            continue
        if not label_word and "total" not in label.lower():
            continue
        resident, nonresident = cells[1], cells[2]
        if not re.search(r"\d", resident):
            continue
        if not resident.startswith("$"):
            resident = f"${resident}"
        if not nonresident.startswith("$"):
            nonresident = f"${nonresident}"
        sentence = (
            f"{label} is {resident} for Michigan residents and "
            f"{nonresident} for non-Michigan residents."
        )
        if "12 to 18 credits" in text and label_word == "tuition":
            sentence += " Students taking 12 to 18 credits per semester are charged that plateau rate."
        return sentence
    return ""


def _line_rank(wanted: set[str], line: str) -> float:
    stems = set(wanted)
    for stem in wanted:
        if stem.endswith("s") and len(stem) > 4:
            stems.add(stem[:-1])
    line_stems = set(_terms(line))
    for stem in list(line_stems):
        if stem.endswith("s") and len(stem) > 4:
            line_stems.add(stem[:-1])
    overlap = len(stems & line_stems)
    if overlap == 0:
        return 0
    if re.match(r"(to|or|and|so|but)\b", line.strip(), re.I):
        overlap -= 1.2
    if re.search(r"does not discriminate|graphic image", line, re.I):
        overlap -= 0.7
    if re.search(r"\d", line):
        overlap += 0.4
    if re.search(r"\b[A-Z][a-z]+ Hall\b", line):
        overlap += 0.8
    return overlap


def _excerpt(question: str, text: str) -> str:
    """One short passage from the page. Nothing is added."""
    wanted = _terms(question)
    lines = _page_lines(text)
    if not wanted or not lines:
        return ""
    kept: list[tuple[float, int, str]] = []
    seen: set[str] = set()
    for index, line in enumerate(lines):
        rank = _line_rank(wanted, line)
        if rank <= 0:
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        kept.append((rank, index, line))
    if not kept:
        return ""
    kept.sort(key=lambda item: (-item[0], item[1]))
    start = kept[0][1]
    chosen = [lines[start]]
    for index in range(start + 1, min(start + 3, len(lines))):
        if not (wanted & _terms(lines[index])):
            break
        if chosen[-1][-1:] in ".!?":
            break
        if lines[index].lower() in {line.lower() for line in chosen}:
            continue
        chosen.append(lines[index])
    if re.search(r"\b(phone|call|number)\b", question, re.I):
        for index in range(max(0, start - 2), min(len(lines), start + 4)):
            if _PHONE_RE.search(lines[index]) and lines[index] not in chosen:
                chosen.append(lines[index])
                break
    body = re.sub(r"\s+", " ", " ".join(chosen)).strip()
    if body and body[-1] not in ".!?":
        cut = max(body.rfind("."), body.rfind("!"), body.rfind("?"))
        body = body[:cut + 1] if cut >= 40 else body + "."
    return body


def _ranked_pages(message: str, hits: list[dict]) -> list[dict]:
    ranked: list[tuple[float, dict]] = []
    seen: set[str] = set()
    for hit in hits:
        url = hit.get("url") or ""
        key = _canon(url)
        if not url or key in seen:
            continue
        seen.add(key)
        score = float(hit.get("score") or 0) + _url_bias(message, url)
        ranked.append((score, hit))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [hit for score, hit in ranked if score >= 0.45][:4]


def _refresh_page(hit: dict) -> None:
    """Fetch the page again and replace its database text when the page changed."""
    url = hit.get("url") or ""
    if not url.startswith("http"):
        return
    from .scraper import fetch_page

    doc = fetch_page(url, hit.get("category") or "general", hit.get("source") or "page")
    if doc and doc.text:
        store.upsert_doc(doc)


def _only_past(text: str) -> bool:
    """True when every date in the text is already over."""
    years = [int(year) for year in re.findall(r"\b(20\d{2})\b", text)]
    year = max(years) if years else dt.date.today().year
    found = []
    for match in re.finditer(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})\b",
        text,
        re.I,
    ):
        item = _as_date(match.group(1), match.group(2), year)
        if item:
            found.append(item)
    return bool(found) and max(found) < dt.date.today()


def _section_reply(question: str, page: dict) -> str:
    """The one stored section that matches the question. No wording is added."""
    notes = _select_notes(question, [page], limit=1)
    if not notes:
        return ""
    service = _asked_service(question)
    sample = "\n".join(_fold(notes[0]["text"]).splitlines()[:8])
    heading = _fold(_heading_text(notes[0]["text"]))
    if service == "library" and "library services" not in sample:
        return ""
    if service and service != "library" and not _HEADING_FOR[service].search(heading):
        return ""
    section = _format_section(notes[0]["text"]).strip()
    if not section or _only_past(section):
        return ""
    if re.search(r"\b(when|what day|what date)\b", question, re.I):
        lines = section.splitlines()
        for index, line in enumerate(lines):
            window = "\n".join(lines[index:index + 4])
            if len(line) <= 80 and _line_rank(_terms(question), line) > 0 and (
                _DAY_OR_MONTH.search(window) or _TIME_RE.search(window)
            ):
                section = "\n".join(lines[index:index + 4]).strip()
                break
        else:
            if not (_DAY_OR_MONTH.search(section) or _TIME_RE.search(section)):
                return ""
        if _only_past(section):
            return ""
    return section


def stream_chat(message: str, category: str | None, top_k: int, history) -> Iterator[dict]:
    yield {"type": "status"}
    asked = _lookup_message(message, history)
    calendar = answer_about(asked)
    if calendar:
        yield {"type": "token", "text": calendar}
        yield {"type": "sources", "sources": [{
            "n": 1,
            "title": "Michigan Tech Events Calendar",
            "url": "https://events.mtu.edu/",
        }]}
        yield {"type": "done"}
        return

    hits = _retrieve(asked, max(top_k * 2, 8), category)
    if _asked_service(asked) == "cafe":
        hits = hits + _retrieve("Velodrome coffee hours", 4, "library")
        for url in (
            "https://www.mtu.edu/library/about/hours/",
            "https://www.mtu.edu/library/about/hours/index.html",
        ):
            title, full = store.page_text(url)
            if not full:
                continue
            hits.append({
                "url": url,
                "title": title,
                "text": full,
                "category": "library",
                "source": "library",
                "score": 0.9,
            })
            break
    if re.search(r"career fair", asked, re.I):
        hits = hits + _retrieve("Career Fair February", 8, "career")
    pages = _ranked_pages(asked, hits)
    if re.search(r"career fair", asked, re.I):
        fair_pages = []
        seen = {_canon(page.get("url") or "") for page in pages}
        for hit in hits:
            url = hit.get("url") or ""
            plain = url.rstrip("/")
            key = _canon(url)
            if key in seen:
                continue
            if plain.endswith("/career/fair") or plain.endswith("/career/fair/index.html"):
                fair_pages.append(hit)
                seen.add(key)
        pages = fair_pages + pages
        for url in (
            "https://www.mtu.edu/career/fair/",
            "https://www.mtu.edu/career/fair/index.html",
        ):
            title, full = store.page_text(url)
            if not full:
                continue
            pages.insert(0, {
                "url": url,
                "title": title,
                "text": full,
                "category": "career",
                "source": "career",
                "score": 1,
            })
            break
    refusal = "I don't have such information."
    if not pages:
        yield {"type": "token", "text": refusal}
        yield {"type": "done"}
        return

    import logging
    log = logging.getLogger("novuspal")
    for page in pages:
        try:
            _refresh_page(page)
        except Exception:
            log.exception("page refresh failed for %s", page.get("url"))
        title, full = store.page_text(page["url"])
        if not full:
            full = page.get("text") or ""
            title = page.get("title") or title
        one = {
            "title": title or page.get("title") or "Campus page",
            "url": page["url"],
            "text": full,
            "score": page.get("score") or 0,
            "category": page.get("category") or "",
            "source": page.get("source") or "",
        }
        section = _section_reply(asked, one)
        if not section:
            continue
        yield {"type": "token", "text": section}
        yield {"type": "sources", "sources": _sources([one])}
        yield {"type": "done"}
        return

    yield {"type": "token", "text": refusal}
    yield {"type": "done"}
