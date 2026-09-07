"""
Unit Test Suite for Nepali Calendar Engine.
Verifies conversion accuracy, bidirectional integrity, formatting, Panchanga,
Nepal Clock, Age Calculation, Festival Search, and Long Weekend Detection.
"""

import unittest
from datetime import date

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.engine import (
    BSDate,
    ad_to_bs,
    bs_to_ad,
    get_days_in_bs_month,
)
from lib.formatter import (
    to_devanagari_num,
    to_arabic_num,
    format_bs_date,
    get_month_name,
)
from lib.holidays import EventManager
from lib.panchanga import calculate_panchanga
from lib.calculator import calculate_age, shift_days, detect_long_weekends, get_nepal_clock_status
from lib.festivals import search_events


class TestNepaliCalendarEngine(unittest.TestCase):
    def test_anchor_conversions(self):
        # Anchor 1: 1975-01-01 BS = 1918-04-13 AD
        d1_ad = date(1918, 4, 13)
        d1_bs = ad_to_bs(d1_ad)
        self.assertEqual(d1_bs.year, 1975)
        self.assertEqual(d1_bs.month, 1)
        self.assertEqual(d1_bs.day, 1)
        self.assertEqual(bs_to_ad(1975, 1, 1), d1_ad)

        # Anchor 2: 2000-01-01 BS = 1943-04-14 AD
        d2_ad = date(1943, 4, 14)
        d2_bs = ad_to_bs(d2_ad)
        self.assertEqual(d2_bs.year, 2000)
        self.assertEqual(d2_bs.month, 1)
        self.assertEqual(d2_bs.day, 1)
        self.assertEqual(bs_to_ad(2000, 1, 1), d2_ad)

        # Anchor 3: 2080-01-01 BS = 2023-04-14 AD
        d3_ad = date(2023, 4, 14)
        d3_bs = ad_to_bs(d3_ad)
        self.assertEqual(d3_bs.year, 2080)
        self.assertEqual(d3_bs.month, 1)
        self.assertEqual(d3_bs.day, 1)
        self.assertEqual(bs_to_ad(2080, 1, 1), d3_ad)

        # Anchor 4: 2081-01-01 BS = 2024-04-13 AD
        d4_ad = date(2024, 4, 13)
        d4_bs = ad_to_bs(d4_ad)
        self.assertEqual(d4_bs.year, 2081)
        self.assertEqual(d4_bs.month, 1)
        self.assertEqual(d4_bs.day, 1)
        self.assertEqual(bs_to_ad(2081, 1, 1), d4_ad)

        # Anchor 5: 2083-05-22 BS = 2026-09-07 AD
        d5_ad = date(2026, 9, 7)
        d5_bs = ad_to_bs(d5_ad)
        self.assertEqual(d5_bs.year, 2083)
        self.assertEqual(d5_bs.month, 5)
        self.assertEqual(d5_bs.day, 22)
        self.assertEqual(bs_to_ad(2083, 5, 22), d5_ad)

    def test_bidirectional_roundtrip(self):
        # Test every 15 days from 1975 to 2043 AD
        cur = date(1975, 4, 15)
        end = date(2043, 12, 31)
        while cur < end:
            bs = ad_to_bs(cur)
            back_ad = bs.to_ad()
            self.assertEqual(cur, back_ad, f"Roundtrip failed for {cur} -> {bs} -> {back_ad}")
            cur = date.fromordinal(cur.toordinal() + 15)

    def test_panchanga(self):
        bs = BSDate(2083, 5, 22)
        panch = calculate_panchanga(bs, "एकादशी")
        self.assertEqual(panch.tithi, "एकादशी")
        self.assertEqual(panch.sun_rashi, "सिंह (Leo)")
        self.assertTrue("AM" in panch.sunrise)
        self.assertTrue("PM" in panch.sunset)
        self.assertTrue("–" in panch.rahu_kaal)

    def test_age_calculator(self):
        dob = BSDate(2055, 8, 12)
        as_of = BSDate(2083, 5, 22)
        res = calculate_age(dob, as_of)
        self.assertEqual(res.years, 27)
        self.assertEqual(res.months, 9)
        self.assertEqual(res.days, 10)
        self.assertTrue(res.total_days > 10000)
        self.assertEqual(res.birth_weekday_ne, "शनिबार")

    def test_date_shift(self):
        bs = BSDate(2083, 5, 22)
        shifted = shift_days(bs, 10)
        self.assertEqual(shifted.year, 2083)
        self.assertEqual(shifted.month, 6)
        self.assertEqual(shifted.day, 1)

    def test_festival_search(self):
        # Test Romanized synonym search
        dashain_results = search_events("dashain")
        self.assertTrue(len(dashain_results) > 0)
        # Should contain Ghatasthapana or Vijaya Dashami
        found_tika = any("दशैको टिका" in r.festival or "विजया" in r.festival for r in dashain_results)
        self.assertTrue(found_tika)

        tihar_results = search_events("tihar")
        self.assertTrue(len(tihar_results) > 0)

    def test_nepal_clock_and_weekends(self):
        mgr = EventManager()
        clock = get_nepal_clock_status(mgr)
        self.assertTrue("NPT" in clock.nepal_time_str)
        self.assertTrue(clock.status_label_ne in ("[खुल्ला]", "[बन्द]"))

        weekends = detect_long_weekends(2083, 6, mgr)
        self.assertTrue(isinstance(weekends, list))


if __name__ == "__main__":
    unittest.main()
