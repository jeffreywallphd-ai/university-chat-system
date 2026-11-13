"""Event parsing for upcoming campus events.

Parses text from https://events.mtu.edu/ into structured event dicts.
Handles date parsing, skip lines, and category filtering."""

import re
import time
from datetime import date

from .config import settings

_MONTHS = {...}
_DATE_LINE = re.compile(...)
_SKIP_LINE = re.compile(...)
_EVENT_ASK = re.compile(...)
_OTHER_TOPIC = re.compile(...)


def _parse_events(text: str, limit: int = 18) -> list[dict]:
    """Parse raw event text into a list of event dictionaries."""
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip("|-")
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
    """Fetch live events from events.mtu.edu via HTTP."""
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
    """Return cached or freshly fetched upcoming events."""
    now = time.time()
    if settings._cache["items"] and now - settings._cache["at"] < 900:
        return settings._cache["items"]
    items = _live_events()
    if len(items) < 4:
        blob = "\n".join(settings._cache["blob"])
        items = _parse_events(blob) or items
    settings._cache["at"] = now
    settings._cache["items"] = items
    return items


def _format_events(events: list[dict]) -> str:
    sentences = []
    for event in events:
        place = f" at {event['place']}" if event.get("place") else ""
        sentences.append(f"{event['title']} is {event['when']}{place}.")
    if len(sentences) == 1:
        return sentences[0]
    return "Here are the ones coming up:\n" + "\n".join(sentences)