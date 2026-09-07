"""
Devanagari and Romanized text/date formatter for Nepali Calendar.
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .engine import BSDate

DEVANAGARI_DIGITS = {
    '0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
    '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'
}

ARABIC_DIGITS = {v: k for k, v in DEVANAGARI_DIGITS.items()}

BS_MONTHS_NE = [
    "वैशाख", "जेठ", "असार", "साउन", "भदौ", "असोज",
    "कार्तिक", "मंसिर", "पुस", "माघ", "फागुन", "चैत"
]

BS_MONTHS_EN = [
    "Baisakh", "Jestha", "Ashadh", "Shrawan", "Bhadra", "Ashwin",
    "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"
]

WEEKDAYS_NE = [
    "आइतबार", "सोमबार", "मंगलबार", "बुधबार", "बिहीबार", "शुक्रबार", "शनिबार"
]

WEEKDAYS_SHORT_NE = [
    "आइत", "सोम", "मंगल", "बुध", "बिही", "शुक्र", "शनि"
]

WEEKDAYS_EN = [
    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
]

WEEKDAYS_SHORT_EN = [
    "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"
]


def to_devanagari_num(num: int | str) -> str:
    """Converts integer or digit string into Devanagari numerals (e.g. 2083 -> २०८३)."""
    return "".join(DEVANAGARI_DIGITS.get(ch, ch) for ch in str(num))


def to_arabic_num(text: str) -> str:
    """Converts Devanagari numeral string back to Arabic digits."""
    return "".join(ARABIC_DIGITS.get(ch, ch) for ch in text)


def get_month_name(month: int, lang: str = "ne") -> str:
    """Returns month name in Nepali (ne) or English (en). Month is 1-indexed."""
    if month < 1 or month > 12:
        raise ValueError(f"Month {month} must be 1-12")
    return BS_MONTHS_NE[month - 1] if lang.lower() == "ne" else BS_MONTHS_EN[month - 1]


def get_weekday_name(weekday: int, lang: str = "ne", short: bool = False) -> str:
    """
    Returns weekday name (0=Sunday to 6=Saturday).
    lang: 'ne' or 'en', short: bool
    """
    if weekday < 0 or weekday > 6:
        raise ValueError(f"Weekday {weekday} must be 0-6")

    if lang.lower() == "ne":
        return WEEKDAYS_SHORT_NE[weekday] if short else WEEKDAYS_NE[weekday]
    else:
        return WEEKDAYS_SHORT_EN[weekday] if short else WEEKDAYS_EN[weekday]


def format_bs_date(bs_date: "BSDate", fmt: str, lang: str = "ne") -> str:
    """
    Formats a BSDate object using custom format string tokens:
    %Y - 4-digit Year (२०८३ / 2083)
    %y - 2-digit Year (८३ / 83)
    %M - Month Name (भदौ / Bhadra)
    %m - 2-digit Month Number (०५ / 05)
    %D - 2-digit Day Number (२२ / 22)
    %d - 1-digit Day Number (२२ / 22)
    %W - Full Weekday Name (सोमबार / Monday)
    %w - Short Weekday Name (सोम / Mon)
    %T - Tithi Name (तृतीया / Tritiya)
    %P - Paksha Name (शुक्ल पक्ष / Shukla Paksha)
    """
    from .engine import calculate_approx_tithi

    is_ne = lang.lower() == "ne"
    year_str = to_devanagari_num(bs_date.year) if is_ne else str(bs_date.year)
    year2_str = to_devanagari_num(bs_date.year % 100) if is_ne else f"{bs_date.year % 100:02d}"
    month_name = get_month_name(bs_date.month, lang)
    month_num = to_devanagari_num(f"{bs_date.month:02d}") if is_ne else f"{bs_date.month:02d}"
    day2_num = to_devanagari_num(f"{bs_date.day:02d}") if is_ne else f"{bs_date.day:02d}"
    day_num = to_devanagari_num(bs_date.day) if is_ne else str(bs_date.day)
    weekday_name = get_weekday_name(bs_date.weekday, lang, short=False)
    weekday_short = get_weekday_name(bs_date.weekday, lang, short=True)

    tithi_ne, tithi_en, paksha_ne = calculate_approx_tithi(bs_date)
    tithi_str = tithi_ne if is_ne else tithi_en
    paksha_str = paksha_ne if is_ne else ("Shukla Paksha" if "शुक्ल" in paksha_ne else "Krishna Paksha")

    res = fmt
    res = res.replace("%Y", year_str)
    res = res.replace("%y", year2_str)
    res = res.replace("%M", month_name)
    res = res.replace("%m", month_num)
    res = res.replace("%D", day2_num)
    res = res.replace("%d", day_num)
    res = res.replace("%W", weekday_name)
    res = res.replace("%w", weekday_short)
    res = res.replace("%T", tithi_str)
    res = res.replace("%P", paksha_str)

    return res
