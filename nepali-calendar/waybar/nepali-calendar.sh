#!/bin/bash
# Wrapper script for Waybar custom/nepali-calendar module

SOURCE="${BASH_SOURCE[0]}"
while [[ -L "$SOURCE" ]]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")/.." >/dev/null 2>&1 && pwd)"

exec python3 "$SCRIPT_DIR/main.py" waybar
