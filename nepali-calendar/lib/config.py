"""
Configuration manager for Nepali Calendar plugin.
Uses Python 3.11+ standard library tomllib with fallback defaults.
"""

import os
from pathlib import Path
from typing import Any, Dict

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # Fallback if older Python


CONFIG_DIR = Path.home() / ".config" / "omarchy" / "plugins" / "nepali-calendar"
CONFIG_FILE = CONFIG_DIR / "config.toml"
EVENTS_FILE = CONFIG_DIR / "events.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "general": {
        "language": "ne",
        "timezone": "local",
        "format_bar": "🇳🇵 %Y %M %D",
        "format_copy": "%Y-%m-%D",
        "format_today": "%W, %D %M %Y (%T)"
    },
    "waybar": {
        "show_icon": True,
        "icon": "🇳🇵",
        "show_tithi": True,
        "upcoming_events_count": 3,
        "highlight_holidays": True,
        "signal_id": 11
    },
    "notifications": {
        "daily_briefing": True,
        "notify_on_holiday": True
    },
    "ui": {
        "saturday_color": "#e06c75",
        "holiday_color": "#e5c07b",
        "today_color": "#98c379"
    }
}


def load_config() -> Dict[str, Any]:
    """Loads configuration from ~/.config/omarchy/plugins/nepali-calendar/config.toml."""
    config = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "rb") as f:
                user_conf = tomllib.load(f)
            # Deep merge user config
            for sec, vals in user_conf.items():
                if sec in config and isinstance(vals, dict):
                    config[sec].update(vals)
                else:
                    config[sec] = vals
        except Exception:
            pass
    return config


def toggle_language() -> str:
    """Toggles language between 'ne' and 'en' in config.toml and returns new language."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    conf = load_config()
    cur_lang = conf.get("general", {}).get("language", "ne")
    new_lang = "en" if cur_lang == "ne" else "ne"
    conf["general"]["language"] = new_lang

    # Write updated config
    format_today_val = conf["general"].get("format_today", "%W, %D %M %Y (%T)")
    lines = [
        "[general]",
        f'language = "{new_lang}"',
        f'timezone = "{conf["general"].get("timezone", "local")}"',
        f'format_bar = "{conf["general"].get("format_bar", "🇳🇵 %Y %M %D")}"',
        f'format_copy = "{conf["general"].get("format_copy", "%Y-%m-%D")}"',
        f'format_today = "{format_today_val}"',
        "",
        "[waybar]",
        f'show_icon = {str(conf["waybar"].get("show_icon", True)).lower()}',
        f'icon = "{conf["waybar"].get("icon", "🇳🇵")}"',
        f'show_tithi = {str(conf["waybar"].get("show_tithi", True)).lower()}',
        f'upcoming_events_count = {conf["waybar"].get("upcoming_events_count", 3)}',
        f'highlight_holidays = {str(conf["waybar"].get("highlight_holidays", True)).lower()}',
        f'signal_id = {conf["waybar"].get("signal_id", 9)}',
        "",
        "[notifications]",
        f'daily_briefing = {str(conf["notifications"].get("daily_briefing", True)).lower()}',
        f'notify_on_holiday = {str(conf["notifications"].get("notify_on_holiday", True)).lower()}',
        "",
        "[ui]",
        f'saturday_color = "{conf["ui"].get("saturday_color", "#e06c75")}"',
        f'holiday_color = "{conf["ui"].get("holiday_color", "#e5c07b")}"',
        f'today_color = "{conf["ui"].get("today_color", "#98c379")}"',
        ""
    ]

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return new_lang
