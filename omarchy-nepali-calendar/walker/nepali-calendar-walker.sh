#!/bin/bash
# Walker / dmenu interactive helper for Nepali Calendar

NPCAL="omarchy-nepali-calendar"
if ! command -v "$NPCAL" >/dev/null 2>&1; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  NPCAL="$SCRIPT_DIR/bin/omarchy-nepali-calendar"
fi

TODAY_NE=$("$NPCAL" today --lang ne --format "%W, %D %M %Y (%T)")
TODAY_EN=$("$NPCAL" today --lang en --format "%W, %D %M %Y (%T)")

OPTIONS="📋 Copy Today (नेपाली): $TODAY_NE\n📋 Copy Today (English): $TODAY_EN\n📅 Open Interactive Calendar (TUI)\n🔍 Search Festivals & Events\n🪐 Kathmandu Solar Panchanga\n🕐 Nepal Clock & Office Status\n🎂 Calculate Age (BS)\n🏖️ Detect Long Weekends\n🔄 Convert AD/BS Date\n✨ Sync Festivals from Remote\n🌐 Toggle Language"

SELECTED=$(echo -e "$OPTIONS" | omarchy-launch-walker --dmenu --width 480 --minheight 1 --maxheight 450 -p "Nepali Calendar…" 2>/dev/null)

case "$SELECTED" in
  *"Copy Today (नेपाली)"*)
    "$NPCAL" copy --format "%Y-%m-%D"
    notify-send -u low "Nepali Calendar" "Copied BS Date: $TODAY_NE"
    ;;
  *"Copy Today (English)"*)
    "$NPCAL" today --lang en --format "%Y-%m-%d" | wl-copy
    notify-send -u low "Nepali Calendar" "Copied BS Date: $TODAY_EN"
    ;;
  *"Open Interactive Calendar"*)
    omarchy-launch-floating-terminal-with-presentation "$NPCAL tui"
    ;;
  *"Search Festivals"*)
    QUERY=$(echo "" | omarchy-launch-walker --dmenu --width 400 -p "Search Festival (e.g. dashain, tihar, teej)…" 2>/dev/null)
    if [[ -n $QUERY ]]; then
      RESULTS=$("$NPCAL" search "$QUERY" 2>&1)
      omarchy-launch-floating-terminal-with-presentation "$NPCAL search '$QUERY'; read -p 'Press enter to exit...'"
    fi
    ;;
  *"Kathmandu Solar Panchanga"*)
    omarchy-launch-floating-terminal-with-presentation "$NPCAL panchanga; read -p 'Press enter to exit...'"
    ;;
  *"Nepal Clock"*)
    omarchy-launch-floating-terminal-with-presentation "$NPCAL clock; read -p 'Press enter to exit...'"
    ;;
  *"Calculate Age"*)
    DOB=$(echo "" | omarchy-launch-walker --dmenu --width 350 -p "Enter DOB in BS (YYYY-MM-DD)…" 2>/dev/null)
    if [[ -n $DOB ]]; then
      omarchy-launch-floating-terminal-with-presentation "$NPCAL age '$DOB'; read -p 'Press enter to exit...'"
    fi
    ;;
  *"Detect Long Weekends"*)
    omarchy-launch-floating-terminal-with-presentation "$NPCAL long-weekends; read -p 'Press enter to exit...'"
    ;;
  *"Convert AD/BS Date"*)
    QUERY=$(echo "" | omarchy-launch-walker --dmenu --width 350 -p "Enter Date (YYYY-MM-DD)…" 2>/dev/null)
    if [[ -n $QUERY ]]; then
      omarchy-launch-floating-terminal-with-presentation "$NPCAL convert '$QUERY'; read -p 'Press enter to exit...'"
    fi
    ;;
  *"Sync Festivals"*)
    "$NPCAL" update-events | while read -r line; do notify-send -u normal "Nepali Calendar" "$line"; done
    ;;
  *"Toggle Language"*)
    "$NPCAL" toggle-lang
    pkill -RTMIN+11 waybar 2>/dev/null || true
    ;;
esac
