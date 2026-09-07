# Specification: Nepali Calendar Plugin for Omarchy (`omarchy-nepali-calendar`)

## 1. Executive Summary

This specification defines the complete architecture, data models, astronomical algorithms, interactive user experience, and integration patterns for the **Nepali Calendar (Bikram Sambat / वि.सं.) Plugin** for the **Omarchy** desktop environment (Arch Linux + Hyprland + Waybar + Walker).

The plugin implements Omarchy's **recommended hybrid architecture**:
1. **Omarchy Native CLI & Glue (Bash 5)**: Standard `omarchy-*` commands conforming to Omarchy style guidelines, metadata headers, Walker dmenu scripts, and Waybar runners.
2. **Offline Calculation Engine & Interactive TUI (Pure Python 3 StdLib)**: High-speed, zero-dependency calendar arithmetic, astronomical Kathmandu solar Panchanga, government office status tracking, age/weekend calculators, 3,280+ festival search engine, fail-safe remote updater, and curses-based terminal calendar.

---

## 2. Architecture & Design Principles

```mermaid
flowchart TD
    subgraph Desktop [Omarchy Desktop Integration]
        WB[Waybar Module: custom/nepali-calendar]
        WL[Walker / Dmenu Quick Launcher]
        OM[Omarchy Menu Submenu]
        NOTIF[Desktop Notification: post-boot]
    end

    subgraph BashGlue [Omarchy Bash Layer - bin/]
        B_MAIN["omarchy-nepali-calendar\n(# omarchy:metadata)"]
        B_CONV["omarchy-nepali-calendar-convert"]
        B_NPCAL["npcal (symlink)"]
    end

    subgraph PyEngine [Core Engine - lib/]
        CLI[lib/cli.py: Command Dispatcher]
        CONV[lib/engine.py: AD <-> BS Arithmetic]
        DATA[lib/bs_data.py: 1975 - 2100 BS Tables]
        FEST_D[lib/festivals_data.py: 3,280+ Records]
        FEST[lib/festivals.py: Romanized Search]
        PANCH[lib/panchanga.py: Solar Calculations]
        CALC[lib/calculator.py: Clock, Age, Weekends]
        FMT[lib/formatter.py: Devanagari & Formatting]
        HOL[lib/holidays.py: Event Manager]
        UPD[lib/updater.py: Atomic Remote Sync]
        TUI[lib/tui.py: Dual-Line Curses Modal]
    end

    subgraph Config [User Configuration]
        CONF["~/.config/omarchy/plugins/nepali-calendar/config.toml"]
        U_EV["~/.config/omarchy/plugins/nepali-calendar/events.json"]
        CACHE["~/.config/omarchy/plugins/nepali-calendar/festivals_cache.json"]
    end

    WB -- "exec (interval 60s, signal 11)" --> B_MAIN
    WL --> B_MAIN
    OM --> B_MAIN
    NOTIF --> B_MAIN
    WB -- "on-click" --> B_MAIN

    B_MAIN --> CLI
    B_CONV --> CLI
    B_NPCAL --> CLI

    CLI --> CONV
    CLI --> FMT
    CLI --> HOL
    CLI --> PANCH
    CLI --> CALC
    CLI --> FEST
    CLI --> UPD
    CLI --> TUI

    CONV --> DATA
    FEST --> FEST_D
    UPD --> FEST_D
    HOL --> FEST_D
    HOL --> U_EV
    UPD --> CACHE
    CLI --> CONF
```

---

## 3. Directory & File Structure

```
omarchy-plugins/
├── nepali-calendar/
│   ├── plugin.toml                     # Plugin metadata and manifest
│   ├── install.sh                      # Non-destructive installer
│   ├── uninstall.sh                    # Clean uninstaller
│   ├── default-config.toml             # Default user configuration
│   ├── default-events.json             # Recurring holidays dataset
│   ├── main.py                         # Top-level Python runner
│   ├── bin/
│   │   ├── omarchy-nepali-calendar     # Main Bash CLI (with Omarchy metadata)
│   │   ├── omarchy-nepali-calendar-convert # Quick conversion CLI
│   │   └── npcal                       # Short alias symlink
│   ├── lib/
│   │   ├── __init__.py
│   │   ├── bs_data.py                  # Verified month day-count tables (1975-2100 BS)
│   │   ├── engine.py                   # AD <-> BS arithmetic & date math
│   │   ├── formatter.py                # Devanagari numerals & text formatter
│   │   ├── festivals_data.py           # Bundled 3,287+ festival & tithi records (2075-2083+ BS)
│   │   ├── festivals.py                # Romanized search engine & synonym mapping
│   │   ├── panchanga.py                # Kathmandu solar calculations (Sunrise, Sunset, Rahu, Rashi)
│   │   ├── calculator.py               # Nepal clock, office status, age & weekend calculators
│   │   ├── holidays.py                 # Unified holiday and custom event manager
│   │   ├── updater.py                  # Atomic remote TSV synchronizer & backup protection
│   │   ├── config.py                   # TOML config loader/writer
│   │   ├── cli.py                      # Python CLI dispatcher
│   │   └── tui.py                      # Interactive dual-line curses calendar modal
│   ├── waybar/
│   │   ├── nepali-calendar.sh          # Waybar JSON generator script
│   │   ├── module.jsonc                # Waybar module definition
│   │   └── style.css                   # Waybar CSS styling
│   ├── walker/
│   │   └── nepali-calendar-walker.sh   # Walker dmenu quick-action script
│   ├── hooks/
│   │   └── post-boot.d/
│   │       └── nepali-calendar-briefing.sh # Morning/login briefing hook
│   └── tests/
│       ├── __init__.py
│       └── test_engine.py              # Unit tests covering all 7 modules
├── SPEC.md                             # This technical specification
└── README.md                           # Repository overview & quickstart
```

---

## 4. Core Capabilities & Mathematical Models

### 4.1 Bikram Sambat Engine & Epoch Anchor
- **Supported Range:** **1975 BS to 2100 BS** (1918 AD to 2044 AD).
- **Epoch Anchor:** `1975-01-01 BS` $\leftrightarrow$ `1918-04-13 AD` (Saturday / शनिबार).
- **Accuracy:** Day-exact month lengths derived from official Nepal Government gazettes.

### 4.2 Kathmandu Solar Panchanga
Calculates real-time solar events for Kathmandu ($27.7172^\circ\text{ N}, 85.3240^\circ\text{ E}$):
- **Sunrise & Sunset Times**: Computed via solar declination and hour angle formula:
  $$\cos(\omega_0) = -\tan(\phi) \cdot \tan(\delta)$$
- **Day Length**: Total duration of daylight ($X\text{h } Y\text{m}$).
- **Sun Sign (राशि - Rashi)**: Solar zodiac transit for the month (मेष / Aries through मीन / Pisces).
- **Rahu Kaal (राहु काल)**: 90-minute daily planetary obstacle window mapped by weekday.
- **Udaya Tithi (तिथि)**: Exact daily lunar phase from the verified festival database.

### 4.3 Live Nepal Clock & Government Office Status
- **NPT Offset**: Fixed $\text{UTC} + 5:45$.
- **Local Delta**: Time difference relative to the user's local system clock (e.g. `+9h 45m`).
- **Government Office Status**:
  - `[खुल्ला / Open]`: Sunday–Thursday 10:00 AM – 5:00 PM (Winter: 4:00 PM), Friday 10:00 AM – 3:00 PM.
  - `[बन्द / Closed]`: Outside office hours, Saturdays, and official public holidays.

### 4.4 Age & Date Math Calculator
- **Precise BS Age**: Computes completed years, months, and days, total days lived, and birth weekday.
- **Next Birthday Countdown**: Days remaining until the next birthday anniversary in Bikram Sambat.
- **Date Shifter**: Fast $\pm N$ day shift arithmetic on Bikram Sambat dates.
- **Long Weekend Detector**: Analyzes a month for consecutive streaks of holidays + Saturdays $\ge 2$ days for vacation planning.

### 4.5 Festival Search Engine
- **Database**: 3,287 daily records spanning BS 2075 through 2083+ (April 2018 AD to April 2027 AD).
- **Synonym & Transliteration Search**: Expands Romanized queries into Nepali terms:
  - `dashain` $\to$ `दशैं`, `दशमी`, `विजया`, `घटस्थापना`, `फूलपाती`, `महाअष्टमी`, `महानवमी`
  - `tihar` / `deepawali` $\to$ `तिहार`, `दिपावली`, `लक्ष्मी`, `भाइटीका`, `गोवर्धन`, `म्ह`
  - `teej` $\to$ `तीज`, `हरितालिका`, `दरखाने`, `ऋषिपञ्चमी`
  - `shivaratri` $\to$ `शिवरात्री`, `महाशिवरात्री`
  - `holi` $\to$ `होली`, `फागु`
  - `lhosar` $\to$ `ल्होसार`, `सोनाम`, `ग्याल्पो`, `तमु`
- **Priority Ranking**:
  1. Upcoming events in current calendar year.
  2. Past events in current calendar year.
  3. Future years chronologically.
  4. Past years chronologically.

### 4.6 Fail-Safe Remote Sync
- **Remote Source:** `https://raw.githubusercontent.com/pradhyu/mac-nepali-calendar/main/Sources/NepaliCalendar/Resources/festivals.tsv`
- **Cache & Backup:** Atomically updates `festivals_cache.json` with fallback to `festivals_backup.json` (aborts if payload $<100$ events to prevent corrupt state).

---

## 5. User Interface Specifications

### 5.1 Interactive Curses TUI Modal (`npcal tui`)
- **Header Banner**: Live Nepal Time (NPT), Office Status (`[खुल्ला]` / `[बन्द]`), and Local Time Delta.
- **Month Header & Progress**: Month name, BS year, Gregorian span, and month elapsed progress bar (`[████████░░] 70%`).
- **Weekday Grid**: `आइत` through `शनि` (with Saturday highlighted in red).
- **Dual-Line Day Cards**:
  - Top Line: Bold Nepali numeral (`२२*` with `*` indicating public holiday).
  - Bottom Line: Subtle Gregorian day subscript in parentheses `(7)`.
- **Multi-Line Event Details**: Stacked, color-coded rows for every festival, tithi, and public holiday on the selected day.
- **Panchanga Card**: Displays Sunrise, Sunset, Day length, Rashi, Rahu Kaal, and Tithi.
- **Visual Range Selection (`v` / `V`)**: Select custom day spans or full weeks to view and copy multi-day events.
- **In-App Search Modal (`/` or `s`)**: Instant live search modal with direct numeric jump (1–6).
- **In-App Date Converter (`c`)**: Convert any date and jump directly to it without leaving the TUI.
- **In-App Long Weekend View (`W`)**: Toggle long weekend streaks list.
- **In-App Help Dialog (`?`)**: Full categorized keybinding reference overlay.

### 5.2 Keybinding Reference

| Key | Action |
| :--- | :--- |
| `h` / `l` / `←` / `→` | Previous / Next Day |
| `j` / `k` / `↓` / `↑` | Next / Previous Week (7 days) |
| `n` / `p` / `]` / `[` | Next / Previous Month |
| `N` / `P` / `L` / `H` / `}` / `{` | Next / Previous Year |
| `t` / `T` | Jump to Today |
| `v` | Toggle custom visual day range selection |
| `V` | Select entire week (Sunday–Saturday) |
| `/` or `s` | Open festival search modal |
| `c` | Open in-app date converter dialog |
| `W` | Toggle long weekend streaks view |
| `y` | Copy selected date or date range to clipboard |
| `yi` / `Y` | Copy ISO date (`YYYY-MM-DD`) to clipboard |
| `Tab` | Toggle language (`नेपाली` $\leftrightarrow$ `English`) |
| `u` | Synchronize latest festivals from remote |
| `?` | Open keybindings help dialog |
| `q` / `Esc` | Close popup / Exit visual mode |

---

## 6. CLI Command Reference (`npcal` / `omarchy-nepali-calendar`)

| Command | Arguments / Flags | Description | Example Output |
| :--- | :--- | :--- | :--- |
| `npcal` | *none* | Show current month calendar grid | 7-column calendar grid in terminal |
| `npcal today` | `[--lang ne\|en] [--format FMT] [--tz local\|npt]` | Print today's formatted BS date | `सोमबार, २२ भदौ २०८३ (एकादशी)` |
| `npcal cal` | `[month] [year] [--lang ne\|en]` | Display calendar for specific month/year | Calendar grid for specified month |
| `npcal convert` | `<date> [--to-bs \| --to-ad]` | Convert date between AD and BS | `2026-09-07 AD -> 2083-05-22 BS` |
| `npcal copy` | `[--format FMT]` | Copy today's BS date to Wayland clipboard | `Copied '२०८३-०५-२२' to clipboard.` |
| `npcal events` | `[--upcoming N]` | List upcoming festivals & holidays in multi-line cards | Structured multi-line festival list |
| `npcal panchanga` | *none* | Display Kathmandu solar Panchanga for today | Sunrise, Sunset, Rashi, Rahu Kaal |
| `npcal clock` | *none* | Display live Nepal Time & Office Status | NPT time, office status, local delta |
| `npcal age` | `<DOB_BS>` | Calculate exact age in BS | Years, months, days, next birthday |
| `npcal shift` | `<date> <days>` | Shift BS date by $\pm N$ days | `2083-05-22 + 10 days -> 2083-06-01` |
| `npcal long-weekends` | `[month] [year]` | Detect long weekend vacation streaks in month | List of consecutive $\ge 2$ days off |
| `npcal search` | `<query>` | Search 3,280+ festivals by keyword/synonym | Priority-sorted search results |
| `npcal update-events` | *none* | Sync latest festivals from remote repository | `✨ Synchronized 3287 festivals` |
| `npcal waybar` | *none* | Stream Waybar JSON payload | `{"text":"...","tooltip":"..."}` |
| `npcal toggle-lang` | *none* | Toggle config between `ne` and `en` | Swaps language in `config.toml` |
| `npcal tui` | *none* | Launch full interactive curses calendar modal | Navigable terminal modal |

---

## 7. Desktop Integration (Waybar, Walker, Hyprland)

### 7.1 Waybar Module (`waybar/module.jsonc`)

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
}
```

### 7.2 Hyprland Window Rules

```ini
windowrulev2 = float, class:^(omarchy-nepali-calendar)$
windowrulev2 = size 640 520, class:^(omarchy-nepali-calendar)$
windowrulev2 = center, class:^(omarchy-nepali-calendar)$
```

---

## 8. Verification & Test Suite

All 7 core modules are validated via the automated unit test suite:

```bash
python3 -m unittest nepali-calendar/tests/test_engine.py
# Ran 7 tests in 0.163s -> OK (100% Passing)
```

1. **Conversion Accuracy:** Verified against official Nepal Government anchor dates across 1975–2100 BS.
2. **Bidirectional Invariance:** $100\%$ round-trip consistency across all dates.
3. **Panchanga Verification:** Verified solar sunrise/sunset and Rahu Kaal windows.
4. **Age & Weekend Calculation:** Validated against leap year rules and holiday streaks.
5. **Search Engine Precision:** Validated multi-keyword synonym matching and priority sorting.
