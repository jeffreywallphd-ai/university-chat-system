"""Upcoming public events from the Michigan Tech calendar."""
import re
import time
from datetime import date

from .config import settings
from . import store

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}
_DATE_LINE = re.compile(
    r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
    r"(\d{1,2}),\s+(\d{4})",
    re.I,
)
_SKIP_LINE = re.compile(
    r"^(home|events|free|pay as|prices vary|skip\b|featured events)",
    re.I,
)
_EVENT_ASK = re.compile(r"\b(events?|happening|upcoming|calendar)\b", re.I)
_OTHER_TOPIC = re.compile(r"\b(library|tutor|regist|hours?|open)\b", re.I)
_cache: dict = {"at": 0.0, "items": []}


def _parse_events(text: str, limit: int = 18) -> list[dict]:
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip(" |-")
        if not line or _SKIP_LINE.match(line) or line.lower().startswith("skip "):
            continue
        lines.append(line)
    today = date.today()
    found: list[dict] = []
    seen: set[str] = set()
    for i, line in enumerate(lines[:-1]):
        when = lines[i + 1]
        match = _DATE_LINE.match(when)
        if not match or _DATE_LINE.match(line):
            continue
        try:
            when_day = date(int(match.group(3)), _MONTHS[match.group(1).lower()], int(match.group(2)))
        except (KeyError, ValueError):
            continue
        if when_day < today or len(line) < 3 or len(line) > 110:
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        place = ""
        if i + 2 < len(lines) and not _DATE_LINE.match(lines[i + 2]):
            nxt = lines[i + 2]
            follows_title = i + 3 < len(lines) and _DATE_LINE.match(lines[i + 3])
            if not follows_title and len(nxt) <= 90 and not _SKIP_LINE.match(nxt):
                place = nxt
        found.append({"title": line, "when": when, "place": place, "date": when_day.isoformat()})
        if len(found) >= limit:
            break
    return found


def _live_events() -> list[dict]:
    import httpx
    import trafilatura

    try:
        response = httpx.get(
            "https://events.mtu.edu/",
            headers={"User-Agent": settings.user_agent},
            timeout=20,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return []
    text = trafilatura.extract(response.text, url="https://events.mtu.edu/", include_links=False) or ""
    if text:
        from .scraper import Doc
        store.upsert_doc(Doc(
            "https://events.mtu.edu/",
            "Michigan Tech Events Calendar",
            text,
            "events",
            "mtu-events",
        ))
    return _parse_events(text)


def upcoming_events() -> list[dict]:
    now = time.time()
    if _cache["items"] and now - _cache["at"] < 900:
        return _cache["items"]
    items = _live_events()
    if len(items) < 4:
        blob = "\n".join(store.list_texts("events", limit=8))
        items = _parse_events(blob) or items
    _cache["at"] = now
    _cache["items"] = items
    return items


def _format_events(events: list[dict]) -> str:
    sentences = []
    for event in events:
        place = f" at {event['place']}" if event.get("place") else ""
        sentences.append(f"{event['title']} is {event['when']}{place}.")
    if len(sentences) == 1:
        return sentences[0]
    return "Here are the ones coming up:\n" + "\n".join(sentences)


def answer_about(message: str) -> str | None:
    """Use the calendar itself when the question is about an event or the schedule of events."""
    events = upcoming_events()
    if not events:
        return None
    question = re.sub(r"\s+", " ", message).strip().lower()
    if _OTHER_TOPIC.search(question) and not _EVENT_ASK.search(question):
        return None
    if "career fair" in question:
        both = [
            event for event in events
            if "career" in event["title"].lower() and "fair" in event["title"].lower()
        ]
        if both and len(both) <= 6:
            both.sort(key=lambda event: event.get("date") or "")
            return _format_events(both)
        return None
    skip = {
        "what", "when", "where", "tell", "about", "from", "with", "this", "that",
        "have", "does", "coming", "campus", "michigan", "tech", "student", "center",
        "there", "your", "game", "games",
    }
    q_words = {w for w in re.findall(r"[a-z0-9']+", question) if len(w) >= 4 and w not in skip}
    matched = []
    for event in events:
        title = event["title"].lower()
        if title in question or (len(question) >= 8 and question in title):
            matched.append(event)
            continue
        if any(word in title for word in q_words):
            matched.append(event)
    if matched and len(matched) <= 6:
        matched.sort(key=lambda event: event.get("date") or "")
        return _format_events(matched)
    if _EVENT_ASK.search(question) and not _OTHER_TOPIC.search(question):
        ordered = sorted(events, key=lambda event: event.get("date") or "")
        return _format_events(ordered[:8])
    return None
