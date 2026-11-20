"""Pure functions: caption track selection, json3 parsing, Markdown rendering.

Nothing in this module touches the network, so all of it is unit-testable.
"""

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

PARAGRAPH_TARGET_CHARS = 600
_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")
_IGNORED_TRACKS = {"live_chat"}


@dataclass(frozen=True)
class Track:
    """A caption track chosen for download."""

    language: str
    url: str
    automatic: bool


def _json3_url(formats: list[dict[str, Any]]) -> str | None:
    for fmt in formats:
        if fmt.get("ext") == "json3" and fmt.get("url"):
            return str(fmt["url"])
    return None


def _base(lang: str) -> str:
    return lang.split("-")[0].lower()


def select_track(info: dict[str, Any]) -> Track | None:
    """Pick the caption track in the video's original language.

    Manual captions win over auto-generated ones. Auto-generated tracks also
    include machine translations; the original one carries a ``-orig`` suffix.
    """
    manual: dict[str, list[dict[str, Any]]] = {
        k: v for k, v in (info.get("subtitles") or {}).items() if k not in _IGNORED_TRACKS
    }
    auto: dict[str, list[dict[str, Any]]] = info.get("automatic_captions") or {}

    # Videos with dubbed audio tracks have one "-orig" track per audio language,
    # so the original is only inferred from it when there is exactly one.
    orig_keys = [k for k in auto if k.endswith("-orig")]
    language: str | None = info.get("language") or (
        orig_keys[0].removesuffix("-orig") if len(orig_keys) == 1 else None
    )

    if language:
        orig_key = next(
            (k for k in orig_keys if _base(k.removesuffix("-orig")) == _base(language)), None
        )
        candidates = [k for k in manual if k == language] + [
            k for k in manual if k != language and _base(k) == _base(language)
        ]
        for key in candidates:
            if url := _json3_url(manual[key]):
                return Track(key, url, automatic=False)
        for auto_key in (orig_key, language):
            if auto_key and auto_key in auto and (url := _json3_url(auto[auto_key])):
                return Track(auto_key.removesuffix("-orig"), url, automatic=True)
        return None

    # Language unknown: fall back to the first manual track.
    for key, formats in manual.items():
        if url := _json3_url(formats):
            return Track(key, url, automatic=False)
    return None


def parse_json3(raw: str) -> str:
    """Turn a YouTube json3 caption payload into one plain-text string."""
    data = json.loads(raw)
    pieces: list[str] = []
    for event in data.get("events", []):
        for seg in event.get("segs") or []:
            pieces.append(seg.get("utf8", ""))
        pieces.append(" ")
    text = "".join(pieces)
    text = re.sub(r"\[[^\]]*\]", " ", text)  # [Music], [Applause]...
    return re.sub(r"\s+", " ", text).strip()


def _split_long(sentence: str, limit: int) -> list[str]:
    """Split text without punctuation at word boundaries."""
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for word in sentence.split():
        if current and size + len(word) + 1 > limit:
            chunks.append(" ".join(current))
            current, size = [], 0
        current.append(word)
        size += len(word) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks


def group_paragraphs(text: str, target: int = PARAGRAPH_TARGET_CHARS) -> list[str]:
    """Group sentences into paragraphs of roughly ``target`` characters."""
    paragraphs: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(text):
        for part in _split_long(sentence, target) if len(sentence) > target else [sentence]:
            if not part:
                continue
            current = f"{current} {part}" if current else part
            if len(current) >= target:
                paragraphs.append(current)
                current = ""
    if current:
        paragraphs.append(current)
    return paragraphs


def slugify(title: str) -> str:
    """ASCII, lowercase, hyphen-separated file name stem."""
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    return slug[:80].rstrip("-") or "transcript"


def _format_date(upload_date: str | None) -> str:
    if upload_date and re.fullmatch(r"\d{8}", upload_date):
        return f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    return ""


def render_markdown(info: dict[str, Any], language: str, paragraphs: list[str]) -> str:
    """Build the Markdown document with its YAML front matter."""
    title = str(info.get("title") or "Untitled")
    channel = str(info.get("channel") or info.get("uploader") or "")
    url = str(info.get("webpage_url") or "")
    front_matter = [
        "---",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        f"channel: {json.dumps(channel, ensure_ascii=False)}",
        f"url: {url}",
        f"date: {_format_date(info.get('upload_date'))}",
        f"language: {language}",
        "---",
    ]
    body = "\n\n".join(paragraphs)
    return "\n".join(front_matter) + f"\n\n# {title}\n\n{body}\n"
