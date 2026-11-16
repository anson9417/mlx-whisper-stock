---
name: mlx-whisper-stock
description: Use when Codex needs to transcribe stock-market audio or video with mlx-whisper in a uv-managed workspace, generate `.srt` subtitles, apply `words.csv` typo replacements, remove filler words, keep Chinese in Traditional Chinese, preserve spoken English, and reflow subtitles so each subtitle entry is a single line with at most 20 characters.
---

# MLX Whisper Stock

Use `uv` for the entire workflow.

## Workflow

1. Confirm the media file and `words.csv` exist in the workspace.
2. Prefer the existing `.venv`; if the workspace is not initialized, run `scripts/bootstrap_workspace.sh`.
3. Generate the base `.srt` with `scripts/transcribe_stock_srt.sh`.
4. Apply typo replacement and subtitle cleanup with `scripts/reflow_srt_entries.py`.
5. Remove temporary files before finishing. Keep only the source media, final `.srt`, `words.csv`, and project files.

## Rules

- Default model: `mlx-community/whisper-large-v3-turbo`.
- Default language: `zh`.
- Keep Chinese output in Traditional Chinese.
- Keep spoken English in English; do not translate it into Chinese.
- Apply every `words.csv` replacement row exactly as written.
- Delete filler text when it appears in subtitles: `喔`, `啊`, `哇`, `呢`, `然後`, `的話`, `哦`, `嗯`, `這樣一個`, `呀`, `哎`, `?`, `的部分`, `耶`, `啦`.
- If a subtitle line starts with `那`, remove that leading character unless the line starts with one of these prefixes:
  `那麼`, `那個`, `那些`, `那一`, `那邊`, `那種`, `那天`, `那時候`, `那片`, `那張`, `那檔`, `那是`, `那隻`, `那次`, `那篇`, `那2次`.
- Reflow the final `.srt` so each subtitle entry contains exactly one text line.
- Limit each subtitle line to 20 characters.
- If a line exceeds 20 characters, split it into new subtitle entries and redistribute the original timing proportionally.
- If an entry becomes empty or only one character after cleanup, drop it.

## Commands

Bootstrap the workspace:

```bash
./scripts/bootstrap_workspace.sh /path/to/workspace
```

Run the full transcription flow from the workspace:

```bash
./scripts/transcribe_stock_srt.sh INPUT.mp4 OUTPUT_NAME words.csv
```

Run only the cleanup and reflow step on an existing subtitle file:

```bash
uv run python ./scripts/reflow_srt_entries.py INPUT.srt words.csv
```

## Resources

### scripts/

- `bootstrap_workspace.sh`: create or repair a uv-managed workspace with `mlx-whisper`.
- `transcribe_stock_srt.sh`: run `mlx_whisper` with stock-subtitle defaults and emit `.srt`.
- `reflow_srt_entries.py`: apply `words.csv`, delete filler text, drop one-character lines, and reflow subtitles into one line per entry with a 20-character limit.
