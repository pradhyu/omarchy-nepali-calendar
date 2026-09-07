"""
Festival and Public Holiday Manager for Nepali Calendar.
Integrates 3,280+ daily event records, solar panchang, and user custom events.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from .festivals import get_event_for_date
from .updater import load_cached_events

if TYPE_CHECKING:
    from .engine import BSDate


@dataclass
class CalendarEvent:
    title_ne: str
    title_en: str
    is_holiday: bool
    tithi: str = ""
    category: str = "general"
    month: int = 1
    day: int = 1
    year: Optional[int] = None

    def get_title(self, lang: str = "ne") -> str:
        return self.title_ne if lang.lower() == "ne" else (self.title_en or self.title_ne)


class EventManager:
    def __init__(self, custom_events_path: Optional[Path] = None):
        load_cached_events()
        self.custom_events: List[CalendarEvent] = []
        if custom_events_path and custom_events_path.exists():
            self._load_custom_events(custom_events_path)

    def _load_custom_events(self, path: Path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for ev in data.get("events", []):
                date_str = ev.get("date_bs", "")
                parts = date_str.split("-")
                if len(parts) == 3:
                    yr = None if parts[0] == "*" else int(parts[0])
                    m = int(parts[1])
                    d = int(parts[2])
                    title = ev.get("title", "")
                    self.custom_events.append(CalendarEvent(
                        title_ne=title,
                        title_en=title,
                        is_holiday=ev.get("is_holiday", False),
                        category=ev.get("category", "custom"),
                        month=m,
                        day=d,
                        year=yr
                    ))
        except Exception:
            pass

    def get_events_for_date(self, bs_date: "BSDate") -> List[CalendarEvent]:
        """Returns all events matching the given BSDate."""
        res = []

        # 1. Check primary 3,280+ database
        ev_data = get_event_for_date(bs_date)
        if ev_data:
            fest = ev_data.get("festival", "")
            tithi = ev_data.get("tithi", "")
            is_hol = ev_data.get("is_holiday", False)
            if fest or tithi:
                res.append(CalendarEvent(
                    title_ne=fest,
                    title_en=fest,
                    is_holiday=is_hol,
                    tithi=tithi,
                    category="festival",
                    month=bs_date.month,
                    day=bs_date.day,
                    year=bs_date.year
                ))

        # 2. Check user custom events
        for ev in self.custom_events:
            if ev.month == bs_date.month and ev.day == bs_date.day:
                if ev.year is None or ev.year == bs_date.year:
                    res.append(ev)

        return res

    def get_tithi_for_date(self, bs_date: "BSDate") -> str:
        """Returns the specific Tithi string for this date."""
        ev_data = get_event_for_date(bs_date)
        if ev_data and ev_data.get("tithi"):
            return ev_data["tithi"]
        from .engine import calculate_approx_tithi
        t_ne, _, _ = calculate_approx_tithi(bs_date)
        return t_ne

    def is_public_holiday(self, bs_date: "BSDate") -> bool:
        """Returns True if the day is a Saturday or has a public holiday event."""
        if bs_date.weekday == 6:  # Saturday
            return True
        for ev in self.get_events_for_date(bs_date):
            if ev.is_holiday:
                return True
        return False

    def get_upcoming_events(self, from_date: "BSDate", limit: int = 5) -> List[tuple["BSDate", CalendarEvent]]:
        """Returns upcoming events starting from from_date."""
        from .engine import get_days_in_bs_month, BSDate

        upcoming = []
        cur_y, cur_m, cur_d = from_date.year, from_date.month, from_date.day

        days_checked = 0
        while days_checked < 60 and len(upcoming) < limit:
            try:
                check_date = BSDate(cur_y, cur_m, cur_d)
                events = self.get_events_for_date(check_date)
                for ev in events:
                    if ev.title_ne and len(upcoming) < limit:
                        upcoming.append((check_date, ev))

                # Increment date
                max_d = get_days_in_bs_month(cur_y, cur_m)
                cur_d += 1
                if cur_d > max_d:
                    cur_d = 1
                    cur_m += 1
                    if cur_m > 12:
                        cur_m = 1
                        cur_y += 1
                days_checked += 1
            except Exception:
                break

        return upcoming
