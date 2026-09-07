# Omarchy Nepali Calendar Plugin

Official Bikram Sambat (वि.सं.) Nepali calendar suite for [Omarchy](https://github.com/basecamp/omarchy) (Arch Linux + Hyprland desktop environment).

Repository: [https://github.com/pradhyu/omarchy-nepali-calendar](https://github.com/pradhyu/omarchy-nepali-calendar)

## Available Plugins

### 🇳🇵 [Nepali Calendar (वि.सं.)](./omarchy-nepali-calendar)

A full-featured Bikram Sambat (BS) Nepali calendar suite natively integrated into Omarchy:
* **Waybar Widget**: Live BS date display, rich tooltips with Tithi, festivals, and public holidays (real-time toggle with `signal 11`).
* **CLI Utility (`npcal` / `omarchy-nepali-calendar`)**: Terminal calendar grid, today's date, date converter, age calculator, solar Panchanga, and clipboard copy.
* **Interactive TUI Modal**: Keyboard-navigable dual-line curses calendar with visual range selection (`v`/`V`), search modal (`/`), and in-app converter (`c`).
* **Multi-Line Event Display**: Structured multi-line card layouts for all festivals, tithis, and public holidays.
* **Walker Launcher Integration**: Quick AD $\leftrightarrow$ BS date conversion and date copying directly from dmenu.
* **Desktop Notifications**: Morning login briefing with today's BS date and holiday status.
* **Zero Dependencies**: 100% pure Python 3 standard library backend.

---

## Installation Guide

### Option 1: Automated Script Install (Recommended)

Run the non-destructive installer script:

```bash
git clone https://github.com/pradhyu/omarchy-nepali-calendar.git ~/git/omarchy-nepali-calendar
cd ~/git/omarchy-nepali-calendar/omarchy-nepali-calendar
chmod +x install.sh
./install.sh
```

The installer automatically:
1. Verifies Python 3 and `wl-clipboard` availability.
2. Symlinks `npcal`, `omarchy-nepali-calendar`, and `omarchy-nepali-calendar-convert` into `~/.local/bin/`.
3. Creates default configuration in `~/.config/omarchy/plugins/nepali-calendar/config.toml`.
4. Injects the `custom/nepali-calendar` module and styles into `~/.config/waybar/config.jsonc` and `~/.config/waybar/style.css` (with automatic backup).
5. Registers the post-boot login briefing notification hook in `~/.config/omarchy/hooks/post-boot.d/`.
6. Reloads Waybar to immediately activate the status bar widget.

---

### Option 2: Manual Installation Step-by-Step

For custom desktop configurations or advanced setups:

#### 1. Link Binaries to PATH
```bash
mkdir -p ~/.local/bin
ln -sf ~/git/omarchy-nepali-calendar/omarchy-nepali-calendar/bin/omarchy-nepali-calendar ~/.local/bin/omarchy-nepali-calendar
ln -sf ~/git/omarchy-nepali-calendar/omarchy-nepali-calendar/bin/omarchy-nepali-calendar-convert ~/.local/bin/omarchy-nepali-calendar-convert
ln -sf ~/git/omarchy-nepali-calendar/omarchy-nepali-calendar/bin/npcal ~/.local/bin/npcal
chmod +x ~/git/omarchy-nepali-calendar/omarchy-nepali-calendar/bin/*
```

#### 2. Initialize Configuration
```bash
mkdir -p ~/.config/omarchy/plugins/nepali-calendar
cp -n ~/git/omarchy-nepali-calendar/omarchy-nepali-calendar/default-config.toml ~/.config/omarchy/plugins/nepali-calendar/config.toml
```

#### 3. Configure Waybar Module
Add `"custom/nepali-calendar"` to `modules-center` in `~/.config/waybar/config.jsonc`:
```jsonc
"modules-center": [
  "custom/nepali-calendar",
  "clock"
],
```

Add the module definition inside `~/.config/waybar/config.jsonc`:
```jsonc
"custom/nepali-calendar": {
  "format": "{}",
  "return-type": "json",
  "exec": "omarchy-nepali-calendar waybar",
  "interval": 60,
  "signal": 11,
  "tooltip": true,
  "on-click": "omarchy-launch-floating-terminal-with-presentation 'omarchy-nepali-calendar tui'",
  "on-click-right": "omarchy-nepali-calendar toggle-lang && pkill -RTMIN+11 waybar",
  "on-click-middle": "omarchy-nepali-calendar copy && notify-send -u low 'Nepali Calendar' 'Copied BS date to clipboard!'"
},
```

#### 4. Add Waybar Styling
Append to `~/.config/waybar/style.css`:
```css
#custom-nepali-calendar {
  color: #ebdbb2;
  padding: 0 10px;
  font-weight: bold;
}
#custom-nepali-calendar.holiday {
  color: #fb4934;
}
```

#### 5. Register Post-Boot Login Hook (Optional)
```bash
mkdir -p ~/.config/omarchy/hooks/post-boot.d
ln -sf ~/git/omarchy-nepali-calendar/omarchy-nepali-calendar/hooks/post-boot.d/nepali-calendar-briefing.sh ~/.config/omarchy/hooks/post-boot.d/nepali-calendar-briefing.sh
chmod +x ~/.config/omarchy/hooks/post-boot.d/nepali-calendar-briefing.sh
```

#### 6. Reload Waybar
```bash
pkill -SIGUSR2 waybar || pkill -x waybar && waybar &
```

---

## Uninstallation

To cleanly remove the plugin and restore original configurations:

```bash
cd ~/git/omarchy-nepali-calendar/omarchy-nepali-calendar
./uninstall.sh
```

---

## Quick Usage & Commands

```bash
# Show current month calendar
npcal

# Show today's formatted date
npcal today

# Convert AD date to BS
npcal convert 2026-09-07

# Convert BS date to AD
npcal convert 2083-05-22

# Copy today's BS date to clipboard
npcal copy

# List upcoming festivals & holidays (multi-line cards)
npcal events

# View Kathmandu solar Panchanga (sunrise, sunset, rahu kaal)
npcal panchanga

# Check Nepal Time & Government Office Status
npcal clock

# Calculate exact age & next birthday countdown
npcal age 2050-04-15

# Detect long weekend streaks in current month
npcal long-weekends

# Search 3,280+ festivals by keyword/synonym
npcal search dashain

# Launch interactive full-screen/floating TUI modal
npcal tui
```

---

## Technical Specifications

See [SPEC.md](file:///home/pkshrestha/git/omarchy-plugins/SPEC.md) for detailed architecture, mathematical models, astronomical algorithms, and design documentation.
