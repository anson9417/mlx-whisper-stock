# mlx-whisper-stock

Codex skill for transcribing stock-market audio or video with `mlx-whisper` in a `uv`-managed workspace.

## What it does

- Bootstrap a local `uv` workspace and virtual environment
- Install `mlx-whisper` and required dependencies
- Transcribe media into `.srt` subtitles with `mlx-community/whisper-large-v3-turbo`
- Keep Chinese output in Traditional Chinese
- Preserve spoken English instead of translating it into Chinese
- Apply typo replacements from `words.csv`
- Remove filler words and clean common subtitle noise
- Reflow subtitles so each subtitle entry is a single line with at most 20 characters
- Drop empty or one-character subtitle lines after cleanup

## Repository layout

```text
mlx-whisper-stock/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
│   ├── bootstrap_workspace.sh
│   ├── transcribe_stock_srt.sh
│   └── reflow_srt_entries.py
├── install.sh
└── LICENSE
```

## Install the skill

```bash
git clone git@github.com:anson9417/mlx-whisper-stock.git
cd mlx-whisper-stock
./install.sh
```

This installs the skill into:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/mlx-whisper-stock
```

## Use in Codex

Mention `$mlx-whisper-stock` when you want Codex to:

- transcribe a stock-market video or audio file
- create `.srt` subtitles with `mlx-whisper`
- apply `words.csv` typo replacement rules
- remove filler words from subtitles
- reflow subtitles into one line per subtitle entry

## Use the scripts directly

Bootstrap a workspace:

```bash
./scripts/bootstrap_workspace.sh /path/to/workspace
```

Transcribe and post-process subtitles:

```bash
./scripts/transcribe_stock_srt.sh INPUT.mp4 OUTPUT_NAME words.csv
```

Re-run only subtitle cleanup on an existing `.srt`:

```bash
uv run python ./scripts/reflow_srt_entries.py INPUT.srt words.csv
```

## Requirements

- macOS with Apple Silicon is the intended target for `mlx-whisper`
- `uv` available in `PATH`
- `ffmpeg` installed if your media workflow needs it

## License

MIT
