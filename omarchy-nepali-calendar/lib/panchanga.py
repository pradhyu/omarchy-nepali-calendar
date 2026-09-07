"""
Kathmandu Solar Panchanga Calculator for Nepali Calendar.
Computes Sunrise, Sunset, Day Length, Sun Sign (Rashi), and Rahu Kaal windows.
"""

import math
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import BSDate

RASHI_NEPALI = [
    "मेष (Aries)",
    "वृष (Taurus)",
    "मिथुन (Gemini)",
    "कर्कट (Cancer)",
    "सिंह (Leo)",
    "कन्या (Virgo)",
    "तुला (Libra)",
    "वृश्चिक (Scorpio)",
    "धनु (Sagittarius)",
    "मकर (Capricorn)",
    "कुम्भ (Aquarius)",
    "मीन (Pisces)",
]

RAHU_KAAL_WINDOWS = [
    "04:30 PM – 06:00 PM",  # Sunday (0)
    "07:30 AM – 09:00 AM",  # Monday (1)
    "03:00 PM – 04:30 PM",  # Tuesday (2)
    "12:00 PM – 01:30 PM",  # Wednesday (3)
    "01:30 PM – 03:00 PM",  # Thursday (4)
    "10:30 AM – 12:00 PM",  # Friday (5)
    "09:00 AM – 10:30 AM",  # Saturday (6)
]


@dataclass
class PanchangaInfo:
    sunrise: str
    sunset: str
    day_length: str
    sun_rashi: str
    rahu_kaal: str
    tithi: str


def calculate_panchanga(bs_date: "BSDate", tithi_str: Optional[str] = None) -> PanchangaInfo:
    """Calculates solar Panchanga events for Kathmandu (27.7172° N, 85.3240° E)."""
    month = max(1, min(12, bs_date.month))
    sun_rashi = RASHI_NEPALI[month - 1]
    wday = max(0, min(6, bs_date.weekday))
    rahu = RAHU_KAAL_WINDOWS[wday]

    # Solar Sunrise & Sunset approximation for Kathmandu (27.7172° N)
    day_of_year = (month - 1) * 30 + bs_date.day
    rad = day_of_year * (2.0 * math.pi / 365.0)

    declination = 0.409 * math.sin(rad - 1.39)
    lat = 27.7172 * math.pi / 180.0

    val = -math.tan(lat) * math.tan(declination)
    val = max(-1.0, min(1.0, val))
    hour_angle = math.acos(val)
    day_length_hours = (2.0 * hour_angle * 180.0 / math.pi) / 15.0

    solar_noon_hours = 12.18  # Kathmandu local mean time adjustment (85.32°E vs 86.25°E standard)
    rise_hours = solar_noon_hours - (day_length_hours / 2.0)
    set_hours = solar_noon_hours + (day_length_hours / 2.0)

    rise_h = int(rise_hours)
    rise_m = int((rise_hours - rise_h) * 60)
    set_h = int(set_hours)
    set_m = int((set_hours - set_h) * 60)
    len_h = int(day_length_hours)
    len_m = int((day_length_hours - len_h) * 60)

    sunrise_str = f"{rise_h:02d}:{rise_m:02d} AM"
    sunset_str = f"{(set_h - 12 if set_h > 12 else set_h):02d}:{set_m:02d} PM"
    length_str = f"{len_h}h {len_m}m"

    return PanchangaInfo(
        sunrise=sunrise_str,
        sunset=sunset_str,
        day_length=length_str,
        sun_rashi=sun_rashi,
        rahu_kaal=rahu,
        tithi=tithi_str or "सामान्य तिथि"
    )
