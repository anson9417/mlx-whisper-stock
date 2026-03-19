# mlx-whisper-stock

Codex skill for transcribing stock-market audio or video with `mlx-whisper` in a `uv`-managed workspace.

## Install

```bash
git clone <repo-url>
cd mlx-whisper-stock
./install.sh
```

## Use

Mention `$mlx-whisper-stock` in Codex, or copy the scripts into a workspace and run:

```bash
./scripts/bootstrap_workspace.sh /path/to/workspace
./scripts/transcribe_stock_srt.sh INPUT.mp4 OUTPUT_NAME words.csv
```
