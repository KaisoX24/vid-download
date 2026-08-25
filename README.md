# vid-download

Download video and audio from the terminal, powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp). Supports single or batch downloads, parallel workers, live progress bars, and both a guided interactive mode and fully scriptable CLI flags.

## Installation

```
pip install vid-download (module)
git clone https://github.com/KaisoX24/vid-download.git
```

```
cd vid-download
uv sync
```

On first run, the tool checks for two required external tools — Deno (needed to solve some sites' JS challenges) and ffmpeg (needed for format conversion/merging) — and offers to install whichever is missing automatically.

## Usage

### Interactive mode

Run with no arguments for a fully guided flow — it'll ask how many files, prompt for each URL, and ask format/resolution/bitrate per file:

```
vid-download
```

### Direct mode

Pass one or more URLs directly. Any flag you don't set falls back to an interactive prompt for just that value — you don't have to specify everything at once.

```
vid-download https://youtu.be/example
```

```
vid-download https://youtu.be/one https://youtu.be/two --format mp3 --bitrate 320k
```

Multiple URLs download in parallel and are automatically zipped into a single archive when finished (unless `--no-zip` is passed).

### Flags

| Flag | Short | Default | Description |
|---|---|---|---|
| `--format` | `-f` | prompt | `mp4` or `mp3`. Applies to every URL passed if set; otherwise asked per URL. |
| `--resolution` | `-r` | `Best` | `Best` / `480P` / `720P` / `1080P`. Used for mp4 only. |
| `--bitrate` | `-b` | `192k` | `128k` / `192k` / `256k` / `320k`. Used for mp3 only. |
| `--output` | `-o` | prompt | Save directory. Created automatically if it doesn't exist. |
| `--workers` | `-w` | `min(len(urls), 8)` | Maximum parallel downloads. |
| `--zip` / `--no-zip` | | on for batches | Force or suppress zipping a multi-URL download. |
| `--yes` | `-y` | off | Skip all prompts — anything not explicitly flagged uses a default instead. |
| `--retries` | | `0` | Retry count for rate-limited or transient failures. Permanent failures (not found, forbidden) are never retried. |
| `--continue-on-error` / `--stop-on-error` | | continue | Whether one failed URL should stop the rest of a batch. |

### Fully unattended example

```
vid-download https://youtu.be/example -f mp4 -r 720P -o ~/Videos -y
```

## Requirements

- Python 3.10+
- Deno and ffmpeg — auto-installed on first run if missing (Windows via winget, macOS via Homebrew, Linux via your system package manager)

## License

MIT
