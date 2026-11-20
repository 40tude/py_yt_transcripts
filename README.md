# py_yt_transcripts

## Description

Fetches the transcript of a YouTube video and saves it as a Markdown file in `./assets/`.

Only the caption track is downloaded (via `yt-dlp`, in YouTube's `json3` format), never the video
or its audio. The tool uses the captions in the video's original language, preferring captions
written by the author over auto-generated ones. If the video has no captions, it prints a message
and stops.

The output file is named after the video title (`./assets/<title-slug>.md`). It contains a YAML
front matter (title, channel, URL, upload date, language) followed by the transcript, grouped into
paragraphs without timestamps.

## Installation

```powershell
uv sync
```

## Usage

```powershell
uv run py-yt-transcripts "https://www.youtube.com/watch?v=DpFwnhfhwt4"
```

## Testing

```powershell
uv run pytest
```

## Type Checking

```powershell
uv run mypy src tests
```

## License

MIT License - see [LICENSE](LICENSE.md) for details


## Contributing
This project is developed for personal and educational purposes. Feel free to explore and use it to enhance your own learning.

Given the nature of the project, external contributions are not actively sought nor encouraged. However, constructive feedback aimed at improving the project (in terms of speed, accuracy, comprehensiveness, etc.) is welcome. Please note that this project is being created as a hobby and is unlikely to be maintained once my initial goal has been achieved.
