"""Command-line entry point: fetch metadata and captions, write Markdown."""

import argparse
import sys
from pathlib import Path
from typing import Any

import yt_dlp

from py_yt_transcripts.transcript import (
    group_paragraphs,
    parse_json3,
    render_markdown,
    select_track,
    slugify,
)

OUTPUT_DIR = Path("assets")


def _fetch(url: str) -> tuple[dict[str, Any], str | None, str | None]:
    """Return (info, language, json3 payload). Nothing but text is downloaded."""
    options = {"skip_download": True, "quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(options) as ydl:
        info: dict[str, Any] = ydl.extract_info(url, download=False)
        track = select_track(info)
        if track is None:
            return info, None, None
        raw: bytes = ydl.urlopen(track.url).read()
        return info, track.language, raw.decode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="py-yt-transcripts",
        description="Save the transcript of a YouTube video as Markdown in ./assets/.",
    )
    parser.add_argument("url", help="YouTube video URL")
    args = parser.parse_args(argv)

    try:
        info, language, raw = _fetch(args.url)
    except yt_dlp.utils.DownloadError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if language is None or raw is None:
        print("No transcript available for this video.", file=sys.stderr)
        return 1

    text = parse_json3(raw)
    if not text:
        print("The transcript is empty.", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / f"{slugify(str(info.get('title') or ''))}.md"
    path.write_text(render_markdown(info, language, group_paragraphs(text)), encoding="utf-8")
    print(f"Saved: {path}")
    return 0
