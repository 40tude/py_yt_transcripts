import json
from typing import Any

from py_yt_transcripts.transcript import (
    group_paragraphs,
    parse_json3,
    render_markdown,
    select_track,
    slugify,
)


def _fmt(tag: str) -> list[dict[str, Any]]:
    return [
        {"ext": "vtt", "url": f"https://x/{tag}.vtt"},
        {"ext": "json3", "url": f"https://x/{tag}.json3"},
    ]


def test_select_prefers_manual_in_original_language() -> None:
    info = {
        "language": "fr",
        "subtitles": {"en": _fmt("m-en"), "fr-FR": _fmt("m-fr")},
        "automatic_captions": {"fr-orig": _fmt("a-fr")},
    }
    track = select_track(info)
    assert track is not None
    assert (track.language, track.url, track.automatic) == ("fr-FR", "https://x/m-fr.json3", False)


def test_select_ignores_manual_translation_uses_auto_original() -> None:
    info = {
        "language": "fr",
        "subtitles": {"en": _fmt("m-en"), "live_chat": _fmt("chat")},
        "automatic_captions": {"en": _fmt("a-en"), "fr-orig": _fmt("a-fr")},
    }
    track = select_track(info)
    assert track is not None
    assert (track.language, track.url, track.automatic) == ("fr", "https://x/a-fr.json3", True)


def test_select_infers_language_from_orig_suffix() -> None:
    info = {"automatic_captions": {"de": _fmt("a-de"), "en-orig": _fmt("a-en")}}
    track = select_track(info)
    assert track is not None
    assert track.language == "en"


def test_select_picks_orig_matching_language_with_dubbed_audio() -> None:
    info = {
        "language": "en-US",
        "automatic_captions": {
            "ar-orig": _fmt("a-ar"),
            "en": _fmt("a-en-translated"),
            "en-orig": _fmt("a-en"),
            "fr-orig": _fmt("a-fr"),
        },
    }
    track = select_track(info)
    assert track is not None
    assert (track.language, track.url) == ("en", "https://x/a-en.json3")


def test_select_returns_none_without_captions() -> None:
    assert select_track({"language": "en", "subtitles": {}, "automatic_captions": {}}) is None


def test_parse_json3_joins_segments_and_drops_noise() -> None:
    raw = json.dumps(
        {
            "events": [
                {"tStartMs": 0},
                {"tStartMs": 10, "segs": [{"utf8": "Hello"}, {"utf8": " world."}]},
                {"tStartMs": 20, "segs": [{"utf8": "\n"}]},
                {"tStartMs": 30, "segs": [{"utf8": "[Music]"}]},
                {"tStartMs": 40, "segs": [{"utf8": "Second"}, {"utf8": " line"}]},
            ]
        }
    )
    assert parse_json3(raw) == "Hello world. Second line"


def test_group_paragraphs_breaks_at_sentence_end() -> None:
    text = "One two three. Four five six. Seven eight."
    assert group_paragraphs(text, target=20) == [
        "One two three. Four five six.",
        "Seven eight.",
    ]


def test_group_paragraphs_splits_unpunctuated_text() -> None:
    text = " ".join(["word"] * 50)
    paragraphs = group_paragraphs(text, target=40)
    assert len(paragraphs) > 1
    assert " ".join(paragraphs) == text


def test_slugify() -> None:
    assert slugify("L'été à Paris: 10 choses!") == "l-ete-a-paris-10-choses"
    assert slugify("!!!") == "transcript"


def test_render_markdown() -> None:
    info = {
        "title": 'Bonds "explained"',
        "channel": "Chan",
        "webpage_url": "https://www.youtube.com/watch?v=abc",
        "upload_date": "20261012",
    }
    md = render_markdown(info, "en", ["Para one.", "Para two."])
    assert md == (
        "---\n"
        'title: "Bonds \\"explained\\""\n'
        'channel: "Chan"\n'
        "url: https://www.youtube.com/watch?v=abc\n"
        "date: 2026-10-12\n"
        "language: en\n"
        "---\n\n"
        '# Bonds "explained"\n\n'
        "Para one.\n\nPara two.\n"
    )
