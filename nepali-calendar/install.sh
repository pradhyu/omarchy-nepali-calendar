#!/bin/bash
# Installer script for Omarchy Nepali Calendar Plugin

set -e

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/omarchy/plugins/nepali-calendar"
HOOKS_DIR="$HOME/.config/omarchy/hooks/post-boot.d"
WAYBAR_CONFIG="$HOME/.config/waybar/config.jsonc"
WAYBAR_STYLE="$HOME/.config/waybar/style.css"

echo "========================================="
echo " Installing Omarchy Nepali Calendar (वि.सं.)"
echo "========================================="

# 1. Dependency checks
echo "[1/6] Checking system dependencies..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: Python 3 is required."
  exit 1
fi

if ! command -v wl-copy >/dev/null 2>&1; then
  echo "Notice: 'wl-clipboard' is recommended for clipboard support."
fi

# 2. Deploy Binaries
echo "[2/6] Linking binaries to $BIN_DIR..."
mkdir -p "$BIN_DIR"
ln -sf "$PLUGIN_DIR/bin/omarchy-nepali-calendar" "$BIN_DIR/omarchy-nepali-calendar"
ln -sf "$PLUGIN_DIR/bin/omarchy-nepali-calendar-convert" "$BIN_DIR/omarchy-nepali-calendar-convert"
ln -sf "$PLUGIN_DIR/bin/npcal" "$BIN_DIR/npcal"
chmod +x "$PLUGIN_DIR/bin/"* "$PLUGIN_DIR/main.py"

# 3. Setup Configuration
echo "[3/6] Setting up user configuration..."
mkdir -p "$CONFIG_DIR"
if [[ ! -f "$CONFIG_DIR/config.toml" ]]; then
  cp "$PLUGIN_DIR/default-config.toml" "$CONFIG_DIR/config.toml"
  echo "  Created default config at $CONFIG_DIR/config.toml"
else
  echo "  Existing config preserved at $CONFIG_DIR/config.toml"
fi

# 4. Integrate with Waybar (Non-destructive JSONC)
echo "[4/6] Configuring Waybar module..."
if [[ -f "$WAYBAR_CONFIG" ]]; then
  if grep -q "custom/nepali-calendar" "$WAYBAR_CONFIG"; then
    echo "  Module already present in $WAYBAR_CONFIG"
  else
    # Create backup
    cp "$WAYBAR_CONFIG" "$WAYBAR_CONFIG.bak.$(date +%s)"
    
    # Use python script to insert module safely next to "clock"
    python3 -c "
import re

with open('$WAYBAR_CONFIG', 'r', encoding='utf-8') as f:
    content = f.read()

# Insert into modules-center next to clock
if '\"custom/nepali-calendar\"' not in content:
    content = re.sub(
        r'(\"modules-center\"\s*:\s*\[)([^\]]*?)(\"clock\"|\"custom/weather\")',
        r'\1\2\"custom/nepali-calendar\", \3',
        content,
        count=1
    )

# Add module definition before the last closing brace
module_def = '''
  \"custom/nepali-calendar\": {
    \"format\": \"{}\",
    \"return-type\": \"json\",
    \"exec\": \"omarchy-nepali-calendar waybar\",
    \"interval\": 60,
    \"signal\": 11,
    \"tooltip\": true,
    \"on-click\": \"omarchy-launch-floating-terminal-with-presentation 'omarchy-nepali-calendar tui'\",
    \"on-click-right\": \"omarchy-nepali-calendar toggle-lang && pkill -RTMIN+11 waybar\",
    \"on-click-middle\": \"omarchy-nepali-calendar copy && notify-send -u low 'Nepali Calendar' 'Copied BS date to clipboard!'\"
  },
'''

if '\"custom/nepali-calendar\":' not in content:
    idx = content.rfind('}')
    if idx != -1:
        content = content[:idx].rstrip() + ',\n' + module_def + '\n}'

with open('$WAYBAR_CONFIG', 'w', encoding='utf-8') as f:
    f.write(content)
"
    echo "  Added custom/nepali-calendar module to $WAYBAR_CONFIG"
  fi
fi

# Append Waybar CSS styling
if [[ -f "$WAYBAR_STYLE" ]]; then
  if ! grep -q "custom-nepali-calendar" "$WAYBAR_STYLE"; then
    cat "$PLUGIN_DIR/waybar/style.css" >> "$WAYBAR_STYLE"
    echo "  Appended styles to $WAYBAR_STYLE"
  fi
fi

# 5. Setup post-boot notification hook
echo "[5/6] Registering post-boot notification hook..."
mkdir -p "$HOOKS_DIR"
ln -sf "$PLUGIN_DIR/hooks/post-boot.d/nepali-calendar-briefing.sh" "$HOOKS_DIR/nepali-calendar-briefing.sh"
chmod +x "$PLUGIN_DIR/hooks/post-boot.d/nepali-calendar-briefing.sh"

# 6. Restart Waybar
echo "[6/6] Reloading Waybar..."
if command -v omarchy-restart-waybar >/dev/null 2>&1; then
  omarchy-restart-waybar >/dev/null 2>&1 || true
else
  pkill -x waybar 2>/dev/null || true
  nohup waybar >/dev/null 2>&1 &
fi

echo ""
echo "✨ Installation complete! You can now run:"
echo "   • npcal (or omarchy-nepali-calendar)"
echo "   • npcal today"
echo "   • npcal cal"
echo "   • npcal convert 2026-09-07"
echo "   • npcal tui (interactive modal)"
echo ""
