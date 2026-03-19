#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${CODEX_HOME:-$HOME/.codex}/skills/mlx-whisper-stock"

mkdir -p "$(dirname "$TARGET_DIR")"
rm -rf "$TARGET_DIR"
cp -R "$SCRIPT_DIR" "$TARGET_DIR"

echo "Installed mlx-whisper-stock to: $TARGET_DIR"
