"""
Calculator utilities for Nepal Clock, Government Office Status, Age, Date Shift, and Long Weekends.
"""

from datetime import datetime, timezone, timedelta, date
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .engine import BSDate, bs_to_ad, ad_to_bs, get_days_in_bs_month, get_today_bs
from .formatter import to_devanagari_num, get_month_name, get_weekday_name


@dataclass
class NepalClockStatus:
    nepal_time_str: str
    is_open: bool
    status_label_ne: str
    status_label_en: str
    time_diff_str: str
    current_bs: BSDate


@dataclass
class AgeResult:
    years: int
    months: int
    days: int
    total_days: int
    birth_weekday_ne: str
    birth_weekday_en: str
    next_birthday_in_days: int


@dataclass
class LongWeekendStreak:
    days_count: int
    start_str: str
    end_str: str
    holiday_names: List[str]


def get_nepal_clock_status(event_mgr=None) -> NepalClockStatus:
    """Computes real-time Nepal Standard Time (UTC+05:45) and government office status."""
    utc_now = datetime.now(timezone.utc)
    npt_tz = timezone(timedelta(hours=5, minutes=45))
    npt_now = utc_now.astimezone(npt_tz)
    local_now = datetime.now()

    # Time delta relative to local system time
    local_offset = local_now.astimezone().utcoffset() or timedelta(0)
    npt_offset = timedelta(hours=5, minutes=45)
    diff_seconds = (npt_offset - local_offset).total_seconds()
    diff_h = int(diff_seconds // 3600)
    diff_m = int((abs(diff_seconds) % 3600) // 60)
    sign = "+" if diff_seconds >= 0 else "-"
    time_diff_str = f"{sign}{abs(diff_h)}h {diff_m:02d}m"

    # Today in BS
    today_bs = ad_to_bs(npt_now.date())
    wday = today_bs.weekday  # 0=Sun, 5=Fri, 6=Sat

    hour = npt_now.hour
    minute = npt_now.minute
    ampm = "PM" if hour >= 12 else "AM"
    disp_h = hour % 12 or 12
    nepal_time_str = f"{disp_h:02d}:{minute:02d} {ampm} NPT"

    # Office Status Rules:
    # Sunday - Thursday: 10:00 AM - 5:00 PM (Winter: 4:00 PM)
    # Friday: 10:00 AM - 3:00 PM
    # Saturday & Public Holidays: CLOSED
    is_holiday = False
    if event_mgr:
        is_holiday = event_mgr.is_public_holiday(today_bs)

    is_open = False
    if not is_holiday and wday != 6:
        # Check winter months (Kartik 16 to Magh 15 approx, or month 7, 8, 9, 10)
        is_winter = today_bs.month in (7, 8, 9, 10)
        close_hour = 16 if is_winter else 17

        if 0 <= wday <= 4:  # Sun - Thu
            if 10 <= hour < close_hour:
                is_open = True
        elif wday == 5:  # Friday
            if 10 <= hour < 15:
                is_open = True

    status_ne = "खुल्ला" if is_open else "बन्द"
    status_en = "Open" if is_open else "Closed"

    return NepalClockStatus(
        nepal_time_str=nepal_time_str,
        is_open=is_open,
        status_label_ne=f"[{status_ne}]",
        status_label_en=f"[{status_en}]",
        time_diff_str=time_diff_str,
        current_bs=today_bs
    )


def calculate_age(dob_bs: BSDate, as_of_bs: Optional[BSDate] = None) -> AgeResult:
    """Calculates exact age in Bikram Sambat years, months, and days."""
    if not as_of_bs:
        as_of_bs, _ = get_today_bs("local")

    dob_ad = dob_bs.to_ad()
    as_of_ad = as_of_bs.to_ad()

    y_diff = as_of_bs.year - dob_bs.year
    m_diff = as_of_bs.month - dob_bs.month
    d_diff = as_of_bs.day - dob_bs.day

    if d_diff < 0:
        m_diff -= 1
        prev_m = 12 if as_of_bs.month == 1 else (as_of_bs.month - 1)
        prev_y = (as_of_bs.year - 1) if as_of_bs.month == 1 else as_of_bs.year
        days_in_prev = get_days_in_bs_month(prev_y, prev_m)
        d_diff += days_in_prev

    if m_diff < 0:
        y_diff -= 1
        m_diff += 12

    total_days = (as_of_ad - dob_ad).days

    # Next birthday countdown
    next_bday_y = as_of_bs.year
    if dob_bs.month < as_of_bs.month or (dob_bs.month == as_of_bs.month and dob_bs.day < as_of_bs.day):
        next_bday_y += 1

    max_days_next = get_days_in_bs_month(next_bday_y, dob_bs.month)
    valid_day = min(dob_bs.day, max_days_next)
    next_bday_bs = BSDate(next_bday_y, dob_bs.month, valid_day)
    next_bday_ad = next_bday_bs.to_ad()
    next_bday_in_days = max(0, (next_bday_ad - as_of_ad).days)

    birth_wday_ne = get_weekday_name(dob_bs.weekday, "ne")
    birth_wday_en = get_weekday_name(dob_bs.weekday, "en")

    return AgeResult(
        years=y_diff,
        months=m_diff,
        days=d_diff,
        total_days=total_days,
        birth_weekday_ne=birth_wday_ne,
        birth_weekday_en=birth_wday_en,
        next_birthday_in_days=next_bday_in_days
    )


def shift_days(bs_date: BSDate, days: int) -> BSDate:
    """Shifts a BS date by N days (+/-)."""
    ad = bs_date.to_ad()
    shifted_ad = ad + timedelta(days=days)
    return ad_to_bs(shifted_ad)


def detect_long_weekends(year: int, month: int, event_mgr) -> List[LongWeekendStreak]:
    """Detects long weekend streaks (consecutive holidays + Saturdays >= 2 days) in a month."""
    max_days = get_days_in_bs_month(year, month)
    streaks = []
    current_streak = []

    for day in range(1, max_days + 1):
        d_bs = BSDate(year, month, day)
        is_off = (d_bs.weekday == 6) or event_mgr.is_public_holiday(d_bs)

        if is_off:
            current_streak.append(d_bs)
        else:
            if len(current_streak) >= 2:
                streaks.append(list(current_streak))
            current_streak = []

    if len(current_streak) >= 2:
        streaks.append(list(current_streak))

    results = []
    for streak in streaks:
        first = streak[0]
        last = streak[-1]
        first_str = f"{to_devanagari_num(first.day)} {get_month_name(first.month, 'ne')} ({get_weekday_name(first.weekday, 'ne', short=True)})"
        last_str = f"{to_devanagari_num(last.day)} {get_month_name(last.month, 'ne')} ({get_weekday_name(last.weekday, 'ne', short=True)})"

        holiday_names = []
        for d in streak:
            events = event_mgr.get_events_for_date(d)
            for ev in events:
                if ev.title_ne:
                    holiday_names.append(ev.title_ne)

        results.append(LongWeekendStreak(
            days_count=len(streak),
            start_str=first_str,
            end_str=last_str,
            holiday_names=holiday_names
        ))

    return results
