#!/bin/bash
# Desktop notification briefing hook for Omarchy login/boot

SOURCE="${BASH_SOURCE[0]}"
while [[ -L "$SOURCE" ]]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")/../.." >/dev/null 2>&1 && pwd)"

DATE_STR=$(python3 "$SCRIPT_DIR/main.py" today --format "%W, %D %M %Y (%T)" 2>/dev/null)

if [[ -n $DATE_STR ]]; then
  notify-send -u normal -a "Omarchy" "🗓️ आजको नेपाली मिति" "$DATE_STR"
fi
