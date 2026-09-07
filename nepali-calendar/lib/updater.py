"""
Fail-Safe Atomic Remote Festival Updater for Nepali Calendar.
Fetches updates from remote TSV repository with validation and backup protection.
"""

import json
import os
import urllib.request
from pathlib import Path
from typing import Tuple, Dict, Any

from .config import CONFIG_DIR
from .festivals_data import EVENTS

REMOTE_TSV_URL = "https://raw.githubusercontent.com/pradhyu/mac-nepali-calendar/main/Sources/NepaliCalendar/Resources/festivals.tsv"
CACHE_FILE = CONFIG_DIR / "festivals_cache.json"
BACKUP_FILE = CONFIG_DIR / "festivals_backup.json"


def load_cached_events():
    """Loads custom/updated festivals from user cache into runtime EVENTS dictionary."""
    file_to_load = None
    if CACHE_FILE.exists():
        file_to_load = CACHE_FILE
    elif BACKUP_FILE.exists():
        file_to_load = BACKUP_FILE

    if not file_to_load:
        return

    try:
        with open(file_to_load, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "events" in data:
            for k, v in data["events"].items():
                EVENTS[k] = v
    except Exception:
        pass


def parse_tsv(text: str) -> Tuple[Dict[str, Dict[str, Any]], int]:
    """Parses TSV lines: <YYYY-MM-DD>\t<Festival>\t<Tithi>\t<is_holiday>."""
    events = {}
    count = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 4:
            date_k = parts[0].strip()
            fest = parts[1].strip()
            tithi = parts[2].strip()
            is_hol = (parts[3].strip() == "1")
            events[date_k] = {
                "festival": fest,
                "tithi": tithi,
                "is_holiday": is_hol
            }
            count += 1
    return events, count


def check_and_update(force: bool = False) -> Tuple[bool, int, str]:
    """
    Asynchronously or synchronously fetches latest festivals from remote TSV.
    Returns (success, event_count, message).
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        req = urllib.request.Request(
            REMOTE_TSV_URL,
            headers={"User-Agent": "Omarchy-Nepali-Calendar/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")

        if not content or len(content) < 200:
            return False, 0, "Remote festival file is empty or unreachable. Existing data kept."

        parsed_events, count = parse_tsv(content)
        if count < 100:
            return False, 0, "Remote festival file contained insufficient data (<100 events). Update aborted."

        # Backup existing cache if present
        if CACHE_FILE.exists():
            try:
                import shutil
                shutil.copyfile(CACHE_FILE, BACKUP_FILE)
            except Exception:
                pass

        # Merge into runtime
        for k, v in parsed_events.items():
            EVENTS[k] = v

        # Write to cache atomically
        temp_cache = CONFIG_DIR / "festivals_cache.json.tmp"
        with open(temp_cache, "w", encoding="utf-8") as f:
            json.dump({"events": parsed_events, "version": "remote-sync"}, f, ensure_ascii=False, indent=2)
        temp_cache.replace(CACHE_FILE)

        return True, count, f"Successfully synchronized {count} festivals from remote!"

    except Exception as e:
        return False, 0, f"Network or parsing error during sync: {e}"
