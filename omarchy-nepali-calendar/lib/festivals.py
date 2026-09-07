"""
Festival Query & Search Engine for Nepali Calendar.
Provides Romanized keyword translation, synonym expansion, and priority-sorted festival searching.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from .engine import BSDate, bs_to_ad, get_today_bs
from .festivals_data import EVENTS
from .formatter import to_devanagari_num, get_month_name, get_weekday_name

# Common English/Romanized festival keywords mapping to Nepali terms
FESTIVAL_SYNONYMS: Dict[str, List[str]] = {
    "dashain": ["दशैं", "दशमी", "विजया", "बिजया", "घटस्थापना", "फूलपाती", "फुलपाती", "महाअष्टमी", "महानवमी", "कोजाग्रत"],
    "tihar": ["तिहार", "दिपावली", "दीपावली", "लक्ष्मी", "भाइटीका", "भाइ टीका", "काग तिहार", "कुकुर तिहार", "गोवर्धन", "म्ह"],
    "deepawali": ["दिपावली", "दीपावली", "लक्ष्मी", "तिहार"],
    "diwali": ["दिपावली", "दीपावली", "लक्ष्मी", "तिहार"],
    "teej": ["तीज", "हरितालिका", "दरखाने", "ऋषिपञ्चमी", "ऋषि पञ्चमी"],
    "holi": ["होली", "फागु", "चीरदाह"],
    "chath": ["छठ", "छइठ"],
    "chhath": ["छठ", "छइठ"],
    "maghe": ["माघे", "माघ संक्रान्ति"],
    "sankranti": ["संक्रान्ति", "संक्रान्ती"],
    "saune": ["साउने", "साउन संक्रान्ती"],
    "shivaratri": ["शिवरात्री", "महाशिवरात्री", "शिवरात्रि"],
    "shivarathri": ["शिवरात्री", "महाशिवरात्री", "शिवरात्रि"],
    "buddha": ["बुद्ध", "उभौली"],
    "jayanti": ["जयन्ती", "जयन्ति"],
    "lhosar": ["ल्होसार", "ल्होछार", "सोनाम", "ग्याल्पो", "तमु"],
    "losar": ["ल्होसार", "ल्होछार", "सोनाम", "ग्याल्पो", "तमु"],
    "janai": ["जनै", "रक्षाबन्धन", "ऋषितर्पणी"],
    "purnima": ["पुर्णिमा", "पूर्णिमा", "पुन्ही"],
    "aushi": ["औशी", "औँसी"],
    "amavasya": ["औशी", "औँसी"],
    "ekadashi": ["एकादशी"],
    "krishna": ["श्रीकृष्ण", "जन्माष्टमी"],
    "janmashtami": ["जन्माष्टमी", "श्रीकृष्ण"],
    "ram": ["राम", "नवमी"],
    "gaijatra": ["गाईजात्रा", "सापारू", "गाई जात्रा"],
    "indrajatra": ["इन्द्रजात्रा", "इन्द्र जात्रा", "येँयाः"],
    "ghodejatra": ["घोडेजात्रा", "घोडे जात्रा"],
    "ratriyatri": ["रथयात्रा"],
    "newyear": ["नव बर्ष", "नववर्ष", "नयाँ वर्ष"],
}

# Fixed annual events fallback
FIXED_ANNUAL_EVENTS = {
    "01-01": {"festival": "नववर्ष आरम्भ (New Year)", "tithi": "", "is_holiday": True},
    "03-15": {"festival": "राष्ट्रिय धान दिवस (Dhan Diwas)", "tithi": "", "is_holiday": False},
    "04-01": {"festival": "साउने संक्रान्ति (Saune Sankranti)", "tithi": "", "is_holiday": False},
    "04-15": {"festival": "खीर खाने दिन", "tithi": "", "is_holiday": False},
    "06-03": {"festival": "संविधान दिवस (Constitution Day)", "tithi": "", "is_holiday": True},
    "10-01": {"festival": "माघे संक्रान्ति (Maghe Sankranti)", "tithi": "", "is_holiday": True},
    "10-16": {"festival": "शहीद दिवस (Martyrs Day)", "tithi": "", "is_holiday": False},
    "11-07": {"festival": "राष्ट्रिय प्रजातन्त्र दिवस (Democracy Day)", "tithi": "", "is_holiday": True},
    "11-24": {"festival": "अन्तर्राष्ट्रिय महिला दिवस (Women's Day)", "tithi": "", "is_holiday": True},
    "12-01": {"festival": "चैते दशैं / घोडेजात्रा", "tithi": "", "is_holiday": False},
}


@dataclass
class SearchResult:
    bs_date: BSDate
    ad_date: Any
    festival: str
    tithi: str
    is_holiday: bool
    priority: int


def get_event_for_date(bs_date: BSDate) -> Optional[Dict[str, Any]]:
    """Look up festival/tithi for a given BSDate."""
    key = f"{bs_date.year:04d}-{bs_date.month:02d}-{bs_date.day:02d}"
    if key in EVENTS:
        return EVENTS[key]

    md_key = f"{bs_date.month:02d}-{bs_date.day:02d}"
    if md_key in FIXED_ANNUAL_EVENTS:
        return FIXED_ANNUAL_EVENTS[md_key]

    return None


def search_events(query: str, ref_date: Optional[BSDate] = None) -> List[SearchResult]:
    """
    Search festivals matching query string (supports Nepali, English & Romanized transliterations).
    Returns priority-sorted search results.
    """
    if not query or not query.strip():
        return []

    q_lower = query.strip().lower()
    if not ref_date:
        ref_date, _ = get_today_bs("local")

    target_keywords = [q_lower]
    for term, syns in FESTIVAL_SYNONYMS.items():
        if q_lower in term or term in q_lower:
            for s in syns:
                target_keywords.append(s.lower())

    results = []
    for date_k, ev in EVENTS.items():
        fest = ev.get("festival", "")
        tithi = ev.get("tithi", "")
        if not fest and not tithi:
            continue

        fest_lower = fest.lower()
        tithi_lower = tithi.lower()

        matches = False
        for kw in target_keywords:
            if kw in fest_lower or kw in tithi_lower:
                matches = True
                break

        if matches:
            parts = [int(p) for p in date_k.split("-")]
            y, m, d = parts[0], parts[1], parts[2]
            try:
                b_date = BSDate(y, m, d)
                a_date = b_date.to_ad()

                # Priority Ranking:
                # 1: Current year, upcoming from today
                # 2: Current year, past
                # 3: Future years
                # 4: Past years
                if y == ref_date.year:
                    if (m > ref_date.month) or (m == ref_date.month and d >= ref_date.day):
                        prio = 1
                    else:
                        prio = 2
                elif y > ref_date.year:
                    prio = 3 + (y - ref_date.year)
                else:
                    prio = 10 + (ref_date.year - y)

                results.append(SearchResult(
                    bs_date=b_date,
                    ad_date=a_date,
                    festival=fest,
                    tithi=tithi,
                    is_holiday=ev.get("is_holiday", False),
                    priority=prio
                ))
            except Exception:
                continue

    # Sort by priority, then chronological order
    results.sort(key=lambda r: (r.priority, r.bs_date.year, r.bs_date.month, r.bs_date.day))
    return results
