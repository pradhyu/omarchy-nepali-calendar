# 🇳🇵 Nepali Calendar Plugin for Omarchy (`omarchy-nepali-calendar`)

A native Bikram Sambat (वि.सं.) Nepali calendar suite tailored for Omarchy (Arch Linux + Hyprland + Waybar + Walker).

Repository: [https://github.com/pradhyu/omarchy-nepali-calendar](https://github.com/pradhyu/omarchy-nepali-calendar)

## Features

- **Live Waybar Integration**: Real-time status bar widget displaying BS date (`🇳🇵 २०८३ भदौ २२`), holiday badges, and rich tooltips with Tithi, Sunrise/Sunset, and upcoming festivals.
- **Interactive Dual-Line Curses TUI (`npcal tui`)**:
  - Dual-line day cells (Nepali numeral + Gregorian day subscript).
  - Multi-line festival & event cards.
  - Visual range & week selection (`v` / `V`) with clipboard copy.
  - In-app modal search (`/`) and date converter (`c`).
  - Long weekend streak viewer (`W`).
  - Nepal Time (NPT UTC+5:45) & Government Office Status (`[खुल्ला]` / `[बन्द]`).
- **Comprehensive CLI Toolkit (`npcal` / `omarchy-nepali-calendar`)**:
  - `today`, `cal`, `convert`, `copy`, `events`, `panchanga`, `clock`, `age`, `shift`, `long-weekends`, `search`, `update-events`, `toggle-lang`, `tui`.
- **Astronomical Kathmandu Panchanga**: Exact Solar Sunrise, Sunset, Day Length, Sun Sign (Rashi), Rahu Kaal, and Lunar Udaya Tithi.
- **Festival Search Engine**: 3,287+ records with Romanized synonym expansion (`dashain`, `tihar`, `teej`, etc.).
- **Walker Launcher Quick Actions**: AD $\leftrightarrow$ BS converter and date copier directly from dmenu.
- **Post-Boot Login Briefing**: Morning desktop notifications with today's festival and office status.
- **Zero Dependencies**: 100% pure Python 3 standard library backend (immune to Arch Linux PEP 668 restrictions).

---

## Installation

### Option 1: Automated Script (Recommended)

```bash
git clone https://github.com/pradhyu/omarchy-nepali-calendar.git ~/git/omarchy-nepali-calendar
cd ~/git/omarchy-nepali-calendar/omarchy-nepali-calendar
chmod +x install.sh
./install.sh
```

### Option 2: Manual Installation Step-by-Step

#### 1. Link Binaries to PATH
```bash
mkdir -p ~/.local/bin
ln -sf "$(pwd)/bin/omarchy-nepali-calendar" ~/.local/bin/omarchy-nepali-calendar
ln -sf "$(pwd)/bin/omarchy-nepali-calendar-convert" ~/.local/bin/omarchy-nepali-calendar-convert
ln -sf "$(pwd)/bin/npcal" ~/.local/bin/npcal
chmod +x bin/*
```

#### 2. Setup Configuration
```bash
mkdir -p ~/.config/omarchy/plugins/nepali-calendar
cp -n default-config.toml ~/.config/omarchy/plugins/nepali-calendar/config.toml
```

#### 3. Configure Waybar
Add `"custom/nepali-calendar"` to `modules-center` in `~/.config/waybar/config.jsonc`:
```jsonc
"modules-center": [
  "custom/nepali-calendar",
  "clock"
],
```

Add module definition inside `~/.config/waybar/config.jsonc`:
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

Append styling to `~/.config/waybar/style.css`:
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

#### 4. Register Notification Hook
```bash
mkdir -p ~/.config/omarchy/hooks/post-boot.d
ln -sf "$(pwd)/hooks/post-boot.d/nepali-calendar-briefing.sh" ~/.config/omarchy/hooks/post-boot.d/nepali-calendar-briefing.sh
chmod +x hooks/post-boot.d/nepali-calendar-briefing.sh
```

#### 5. Reload Waybar
```bash
pkill -SIGUSR2 waybar || pkill -x waybar && waybar &
```

---

## Uninstallation

```bash
cd ~/git/omarchy-nepali-calendar/omarchy-nepali-calendar
chmod +x uninstall.sh
./uninstall.sh
```

---

## Command Reference

| Command | Description |
| :--- | :--- |
| `npcal` | Display current month calendar grid |
| `npcal today` | Print today's formatted BS date |
| `npcal cal [month] [year]` | View calendar for specific month/year |
| `npcal convert <date>` | Convert between AD and BS |
| `npcal copy` | Copy today's BS date to clipboard |
| `npcal events` | List upcoming festivals in multi-line cards |
| `npcal panchanga` | Display Kathmandu solar timings & Rahu Kaal |
| `npcal clock` | Display Nepal Time & Government Office Status |
| `npcal age <DOB_BS>` | Calculate exact age & next birthday countdown |
| `npcal shift <date> <±days>` | Date math addition/subtraction |
| `npcal long-weekends` | Find consecutive days off for trip planning |
| `npcal search <query>` | Search 3,280+ festivals by keyword/synonym |
| `npcal update-events` | Sync latest festivals from remote |
| `npcal toggle-lang` | Toggle between Nepali and English |
| `npcal tui` | Open interactive curses terminal calendar modal |

---

## TUI Keybindings

| Key | Action |
| :--- | :--- |
| `h` / `j` / `k` / `l` | Navigate Day / Week |
| `n` / `p` | Next / Previous Month |
| `N` / `P` | Next / Previous Year |
| `t` | Jump to Today |
| `v` / `V` | Visual range / Full week selection |
| `/` or `s` | Open festival search modal |
| `c` | Open in-app date converter |
| `W` | Toggle long weekend streaks |
| `y` / `Y` | Copy date or date range to clipboard |
| `Tab` | Toggle language (`ne` $\leftrightarrow$ `en`) |
| `?` | Show help modal |
| `q` | Quit |
