# Omarchy Plugins

Community and custom plugins for [Omarchy](https://github.com/basecamp/omarchy) (Arch Linux + Hyprland desktop environment).

## Available Plugins

### 🇳🇵 [Nepali Calendar (वि.सं.)](./nepali-calendar)

A full-featured Bikram Sambat (BS) Nepali calendar suite natively integrated into Omarchy:
* **Waybar Widget**: Live BS date display, rich tooltips with Tithi, festivals, and public holidays.
* **CLI Utility (`npcal` / `omarchy-nepali-calendar`)**: Terminal calendar grid, today's date, date converter, and clipboard copy.
* **Interactive TUI**: Keyboard-navigable curses calendar modal (`h/j/k/l`, `t`, `n/p`, `q`).
* **Walker Launcher Integration**: Quick AD $\leftrightarrow$ BS date conversion and date copying directly from dmenu.
* **Desktop Notifications**: Morning login briefing with today's BS date and holiday status.
* **Zero Dependencies**: 100% pure Python 3 standard library.

#### Quick Install

```bash
cd nepali-calendar
./install.sh
```

#### Quick Usage

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

# Launch interactive floating TUI calendar
npcal tui
```

---

## Technical Specifications

See [SPEC.md](file:///home/pkshrestha/git/omarchy-plugins/SPEC.md) for detailed architecture and design documentation.
# omarchy-nepali-calendar
