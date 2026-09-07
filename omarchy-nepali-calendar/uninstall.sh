#!/bin/bash
# Uninstaller script for Omarchy Nepali Calendar Plugin

set -e

BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/omarchy/plugins/nepali-calendar"
HOOKS_DIR="$HOME/.config/omarchy/hooks/post-boot.d"
WAYBAR_CONFIG="$HOME/.config/waybar/config.jsonc"
WAYBAR_STYLE="$HOME/.config/waybar/style.css"

echo "==========================================="
echo " Uninstalling Omarchy Nepali Calendar"
echo "==========================================="

# 1. Remove Binaries
echo "[1/4] Removing binary symlinks..."
rm -f "$BIN_DIR/omarchy-nepali-calendar"
rm -f "$BIN_DIR/omarchy-nepali-calendar-convert"
rm -f "$BIN_DIR/npcal"

# 2. Remove Hook
echo "[2/4] Removing post-boot hook..."
rm -f "$HOOKS_DIR/nepali-calendar-briefing.sh"

# 3. Clean Waybar config & style
echo "[3/4] Cleaning Waybar configuration..."
if [[ -f "$WAYBAR_CONFIG" ]]; then
  python3 -c "
import re

with open('$WAYBAR_CONFIG', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove from module list
content = re.sub(r'\"custom/nepali-calendar\",?\s*', '', content)

# Remove module definition
content = re.sub(r'\"custom/nepali-calendar\":\s*\{[^}]*\},?', '', content)

with open('$WAYBAR_CONFIG', 'w', encoding='utf-8') as f:
    f.write(content)
"
fi

if [[ -f "$WAYBAR_STYLE" ]]; then
  sed -i '/Nepali Calendar Waybar Module Styling/,+12d' "$WAYBAR_STYLE" 2>/dev/null || true
fi

# 4. Optional Purge
if [[ $1 == "--purge" ]]; then
  echo "[4/4] Purging user configuration and events..."
  rm -rf "$CONFIG_DIR"
else
  echo "[4/4] Keeping user configuration in $CONFIG_DIR (use --purge to delete)"
fi

# Reload Waybar
if command -v omarchy-restart-waybar >/dev/null 2>&1; then
  omarchy-restart-waybar >/dev/null 2>&1 || true
fi

echo "✨ Uninstallation completed successfully."
