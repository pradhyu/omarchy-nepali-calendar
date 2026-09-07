"""
Bikram Sambat (BS) Conversion Engine
Provides arithmetic date conversions between Gregorian (AD) and Bikram Sambat (BS).
"""

from datetime import date, datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Tuple, Optional

from .bs_data import (
    BS_MONTH_DAYS,
    START_BS_YEAR,
    END_BS_YEAR,
    ANCHOR_AD_YEAR,
    ANCHOR_AD_MONTH,
    ANCHOR_AD_DAY,
    ANCHOR_BS_YEAR,
)


@dataclass(frozen=True)
class BSDate:
    year: int
    month: int
    day: int

    def __post_init__(self):
        if self.year < START_BS_YEAR or self.year > END_BS_YEAR:
            raise ValueError(f"BS year {self.year} out of supported range ({START_BS_YEAR}-{END_BS_YEAR})")
        if self.month < 1 or self.month > 12:
            raise ValueError(f"BS month {self.month} must be between 1 and 12")
        max_days = get_days_in_bs_month(self.year, self.month)
        if self.day < 1 or self.day > max_days:
            raise ValueError(f"BS day {self.day} invalid for {self.year}/{self.month:02d} (max {max_days})")

    def to_ad(self) -> date:
        return bs_to_ad(self.year, self.month, self.day)

    @property
    def weekday(self) -> int:
        """Returns 0 for Sunday (आइतबार) through 6 for Saturday (शनिबार)."""
        ad = self.to_ad()
        return (ad.weekday() + 1) % 7

    def strftime(self, fmt: str) -> str:
        from .formatter import format_bs_date
        return format_bs_date(self, fmt)


def get_days_in_bs_month(year: int, month: int) -> int:
    """Returns number of days in the specified BS year and month (1-12)."""
    if year not in BS_MONTH_DAYS:
        raise ValueError(f"Year {year} not in BS dataset ({START_BS_YEAR}-{END_BS_YEAR})")
    if month < 1 or month > 12:
        raise ValueError(f"Month {month} must be between 1 and 12")
    return BS_MONTH_DAYS[year][month - 1]


def bs_to_ad(bs_year: int, bs_month: int, bs_day: int) -> date:
    """Converts a Bikram Sambat date to a Gregorian (AD) datetime.date."""
    if bs_year not in BS_MONTH_DAYS:
        raise ValueError(f"BS year {bs_year} out of supported range ({START_BS_YEAR}-{END_BS_YEAR})")

    anchor_ad = date(ANCHOR_AD_YEAR, ANCHOR_AD_MONTH, ANCHOR_AD_DAY)
    total_days = 0

    # Add days for completed BS years
    for y in range(ANCHOR_BS_YEAR, bs_year):
        total_days += sum(BS_MONTH_DAYS[y])

    # Add days for completed BS months in target year
    for m in range(1, bs_month):
        total_days += BS_MONTH_DAYS[bs_year][m - 1]

    # Add remaining days
    total_days += (bs_day - 1)

    return anchor_ad + timedelta(days=total_days)


def ad_to_bs(ad_date: date) -> BSDate:
    """Converts a Gregorian (AD) datetime.date to a BSDate."""
    anchor_ad = date(ANCHOR_AD_YEAR, ANCHOR_AD_MONTH, ANCHOR_AD_DAY)
    if ad_date < anchor_ad:
        raise ValueError(f"AD date {ad_date} is before supported BS anchor {anchor_ad}")

    total_days = (ad_date - anchor_ad).days

    cur_year = ANCHOR_BS_YEAR
    while cur_year <= END_BS_YEAR:
        year_days = sum(BS_MONTH_DAYS[cur_year])
        if total_days < year_days:
            break
        total_days -= year_days
        cur_year += 1

    if cur_year > END_BS_YEAR:
        raise ValueError(f"AD date {ad_date} exceeds supported BS range (up to {END_BS_YEAR} BS)")

    cur_month = 1
    for m_idx in range(12):
        m_days = BS_MONTH_DAYS[cur_year][m_idx]
        if total_days < m_days:
            cur_month = m_idx + 1
            break
        total_days -= m_days

    cur_day = total_days + 1
    return BSDate(cur_year, cur_month, cur_day)


def get_today_bs(tz_mode: str = "local") -> Tuple[BSDate, date]:
    """
    Returns (BSDate, AD_date) for today.
    tz_mode: 'local' (system clock) or 'NPT' (Nepal Standard Time UTC+05:45).
    """
    if tz_mode.upper() == "NPT":
        npt_tz = timezone(timedelta(hours=5, minutes=45))
        now = datetime.now(npt_tz).date()
    else:
        now = datetime.now().date()

    return ad_to_bs(now), now


def calculate_approx_tithi(bs_date: BSDate) -> Tuple[str, str, str]:
    """
    Computes approximate Udaya Tithi and Paksha based on astronomical lunar phase.
    Returns (tithi_name_ne, tithi_name_en, paksha_ne).
    """
    # Base reference epoch for lunar phase
    # Known Purnima reference: 2081-05-03 BS = 2024-08-19 AD (Shukla Purnima, Raksha Bandhan)
    ref_ad = date(2024, 8, 19)
    cur_ad = bs_date.to_ad()
    diff_days = (cur_ad - ref_ad).days

    # Synodic month length = 29.530588 days
    lunar_phase = (diff_days % 29.530588) / 29.530588
    # 30 tithis per synodic month (0-14: Krishna Paksha, 15-29: Shukla Paksha)
    tithi_index = int(lunar_phase * 30) % 30

    tithi_names_ne = [
        "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पञ्चमी",
        "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
        "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पूर्णिमा",
        "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पञ्चमी",
        "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
        "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "औंसी"
    ]

    tithi_names_en = [
        "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
        "Shasthi", "Saptami", "Ashtami", "Navami", "Dashami",
        "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
        "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
        "Shasthi", "Saptami", "Ashtami", "Navami", "Dashami",
        "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Aaunsi"
    ]

    is_shukla = tithi_index < 15
    paksha_ne = "शुक्ल पक्ष" if is_shukla else "कृष्ण पक्ष"
    paksha_en = "Shukla Paksha" if is_shukla else "Krishna Paksha"

    return tithi_names_ne[tithi_index], tithi_names_en[tithi_index], paksha_ne
