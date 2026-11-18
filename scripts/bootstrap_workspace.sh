#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-$PWD}"
PYTHON_VERSION="${MLX_WHISPER_PYTHON:-3.12}"

mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required but was not found in PATH." >&2
  exit 1
fi

uv python install "$PYTHON_VERSION"

if [[ ! -f pyproject.toml ]]; then
  uv init --bare --python "$PYTHON_VERSION"
fi

uv python pin "$PYTHON_VERSION"

uv run python - <<'PY'
from pathlib import Path
import re

path = Path("pyproject.toml")
text = path.read_text(encoding="utf-8")

if 'name = "mlx-whisper"' in text:
    text = text.replace('name = "mlx-whisper"', 'name = "mlx-whisper-workspace"', 1)

if 'dependencies = [' not in text:
    text = text.rstrip() + '\n\ndependencies = []\n'

path.write_text(text, encoding="utf-8")
PY

uv sync >/dev/null 2>&1 || true

# 套件名稱:匯入名稱。opencc 用於將字幕轉為繁體中文，缺少時 reflow 腳本會直接報錯。
for dep in "mlx-whisper:mlx_whisper" "opencc:opencc"; do
  package="${dep%%:*}"
  module="${dep##*:}"
  if ! uv run python -c "import ${module}" >/dev/null 2>&1; then
    uv add "$package"
  fi
done

uv sync
echo "Workspace ready at: $TARGET_DIR"
