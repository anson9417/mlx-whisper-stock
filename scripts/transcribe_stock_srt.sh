#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo "Usage: $0 INPUT_MEDIA OUTPUT_NAME WORDS_CSV [LANGUAGE]" >&2
  exit 1
fi

INPUT_MEDIA="$1"
OUTPUT_NAME="$2"
WORDS_CSV="$3"
LANGUAGE="${4:-auto}"
MODEL="${MLX_WHISPER_MODEL:-mlx-community/whisper-large-v3-turbo}"
WORKDIR="${MLX_WHISPER_WORKDIR:-$PWD}"

INPUT_PATH="$(python - <<'PY' "$INPUT_MEDIA"
from pathlib import Path
import sys
print(Path(sys.argv[1]).expanduser().resolve())
PY
)"

WORDS_PATH="$(python - <<'PY' "$WORDS_CSV"
from pathlib import Path
import sys
print(Path(sys.argv[1]).expanduser().resolve())
PY
)"

if [[ ! -f "$INPUT_PATH" ]]; then
  echo "Input file not found: $INPUT_MEDIA" >&2
  exit 1
fi

if [[ ! -f "$WORDS_PATH" ]]; then
  echo "words.csv not found: $WORDS_CSV" >&2
  exit 1
fi

cd "$WORKDIR"

if [[ ! -f "pyproject.toml" ]]; then
  echo "Workspace not initialized: $WORKDIR" >&2
  echo "Run ./scripts/bootstrap_workspace.sh \"$WORKDIR\" first." >&2
  exit 1
fi

ARGS=(
  uv run mlx_whisper
  --model "$MODEL"
  --output-dir .
  --output-name "$OUTPUT_NAME"
  --output-format srt
  --task transcribe
  --condition-on-previous-text False
  --hallucination-silence-threshold 1.5
  --initial-prompt "請將中文內容輸出為繁體中文；若原音包含英文，請保留英文原文，不要翻譯成中文。"
)

if [[ "$LANGUAGE" != "auto" ]]; then
  ARGS+=(--language "$LANGUAGE")
fi

ARGS+=("$INPUT_PATH")

"${ARGS[@]}"

uv run python "$(dirname "$0")/reflow_srt_entries.py" "${OUTPUT_NAME}.srt" "$WORDS_PATH"
