#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo "Usage: $0 INPUT_MEDIA OUTPUT_NAME WORDS_CSV [LANGUAGE]" >&2
  exit 1
fi

INPUT_MEDIA="$1"
OUTPUT_NAME="$2"
WORDS_CSV="$3"
LANGUAGE="${4:-zh}"
MODEL="${MLX_WHISPER_MODEL:-mlx-community/whisper-large-v3-turbo}"
PROMPT="${MLX_WHISPER_PROMPT:-股票財經節目，可能包含專業術語和公司資訊。請特別注意數字和專有名詞的準確性。請將結果轉錄為繁體中文，包含適當的標點符號。}"
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
  --temperature 0
  --condition-on-previous-text False
  --hallucination-silence-threshold 1.5
  --initial-prompt "$PROMPT"
)

ARGS+=(--language "$LANGUAGE")

ARGS+=("$INPUT_PATH")

"${ARGS[@]}"

uv run python "$(dirname "$0")/reflow_srt_entries.py" "${OUTPUT_NAME}.srt" "$WORDS_PATH"
