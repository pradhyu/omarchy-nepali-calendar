"""
CLI Command Dispatcher for Nepali Calendar.
Handles all subcommands: today, cal, convert, copy, events, panchanga, clock,
age, shift, long-weekends, search, update-events, waybar, tui, toggle-lang.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import date, datetime
from typing import Optional

from .engine import (
    BSDate,
    ad_to_bs,
    bs_to_ad,
    get_days_in_bs_month,
    get_today_bs,
)
from .formatter import (
    format_bs_date,
    get_month_name,
    get_weekday_name,
    to_devanagari_num,
    WEEKDAYS_SHORT_NE,
    WEEKDAYS_SHORT_EN,
)
from .holidays import EventManager
from .panchanga import calculate_panchanga
from .calculator import (
    get_nepal_clock_status,
    calculate_age,
    shift_days,
    detect_long_weekends,
)
from .festivals import search_events
from .updater import check_and_update
from .config import load_config, toggle_language, EVENTS_FILE


def cmd_today(args, config, event_mgr):
    lang = args.lang or config.get("general", {}).get("language", "ne")
    tz = args.tz or config.get("general", {}).get("timezone", "local")
    fmt = args.format or config.get("general", {}).get("format_today", "%W, %D %M %Y (%T)")

    today_bs, _ = get_today_bs(tz)
    output = format_bs_date(today_bs, fmt, lang=lang)
    print(output)


def cmd_cal(args, config, event_mgr):
    lang = args.lang or config.get("general", {}).get("language", "ne")
    tz = config.get("general", {}).get("timezone", "local")
    today_bs, _ = get_today_bs(tz)

    year = args.year if args.year is not None else today_bs.year
    month = args.month if args.month is not None else today_bs.month

    if year < 1975 or year > 2100:
        print(f"Error: Year {year} is out of range (1975-2100 BS)", file=sys.stderr)
        sys.exit(1)
    if month < 1 or month > 12:
        print(f"Error: Month {month} must be 1-12", file=sys.stderr)
        sys.exit(1)

    month_name = get_month_name(month, lang)
    year_str = to_devanagari_num(year) if lang == "ne" else str(year)
    title = f"{month_name} {year_str} (वि.सं.)"

    # ANSI Colors
    C_SAT = "\033[1;31m"      # Red / bold for Saturday & holidays
    C_TODAY = "\033[1;32;7m"  # Green background / reverse for today
    C_RESET = "\033[0m"
    C_HEADER = "\033[1;36m"
    C_DIM = "\033[2m"

    # Header
    print(f"\n{C_HEADER}{title:^34}{C_RESET}")
    first_bs = BSDate(year, month, 1)
    first_ad = first_bs.to_ad()
    last_bs = BSDate(year, month, get_days_in_bs_month(year, month))
    last_ad = last_bs.to_ad()
    ad_range = f"{first_ad.strftime('%b %d')} – {last_ad.strftime('%b %d, %Y')} AD"
    print(f"{C_DIM}{ad_range:^34}{C_RESET}")

    # Weekday columns
    headers = WEEKDAYS_SHORT_NE if lang == "ne" else WEEKDAYS_SHORT_EN
    hdr_line = ""
    for idx, d in enumerate(headers):
        color = C_SAT if idx == 6 else C_HEADER
        hdr_line += f"{color}{d:>4}{C_RESET} "
    print(hdr_line)
    print("─" * 35)

    # Days
    start_weekday = first_bs.weekday  # 0=Sunday
    max_days = get_days_in_bs_month(year, month)

    line = "     " * start_weekday
    col = start_weekday

    for day in range(1, max_days + 1):
        day_bs = BSDate(year, month, day)
        day_str = to_devanagari_num(f"{day:2d}") if lang == "ne" else f"{day:2d}"

        is_today = (year == today_bs.year and month == today_bs.month and day == today_bs.day)
        is_sat = (col == 6)
        is_hol = event_mgr.is_public_holiday(day_bs)

        if is_today:
            cell = f"{C_TODAY} {day_str} {C_RESET}"
        elif is_sat or is_hol:
            cell = f"{C_SAT} {day_str} {C_RESET}"
        else:
            cell = f" {day_str} "

        line += cell
        col += 1
        if col > 6:
            print(line)
            line = ""
            col = 0

    if line.strip():
        print(line)
    print()


def cmd_convert(args, config, event_mgr):
    date_str = args.date.strip()
    try:
        parts = [int(p) for p in date_str.replace("/", "-").split("-")]
        if len(parts) != 3:
            raise ValueError
    except Exception:
        print(f"Error: Invalid date format '{date_str}'. Expected YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    y, m, d = parts[0], parts[1], parts[2]
    to_bs = args.to_bs
    to_ad = args.to_ad

    if not to_bs and not to_ad:
        if y >= 2045:
            to_ad = True
        else:
            to_bs = True

    if to_bs:
        ad_d = date(y, m, d)
        bs_d = ad_to_bs(ad_d)
        ne_str = format_bs_date(bs_d, "%W, %D %M %Y (%T)", lang="ne")
        en_str = format_bs_date(bs_d, "%W, %D %M %Y (%T)", lang="en")
        print(f"AD Date: {ad_d.strftime('%Y-%m-%d (%A)')}")
        print(f"BS Date: {bs_d.year:04d}-{bs_d.month:02d}-{bs_d.day:02d}")
        print(f"नेपाली:  {ne_str}")
        print(f"English: {en_str}")
    else:
        bs_d = BSDate(y, m, d)
        ad_d = bs_d.to_ad()
        print(f"BS Date: {bs_d.year:04d}-{bs_d.month:02d}-{bs_d.day:02d}")
        print(f"AD Date: {ad_d.strftime('%Y-%m-%d (%A)')}")


def cmd_copy(args, config, event_mgr):
    lang = config.get("general", {}).get("language", "ne")
    tz = config.get("general", {}).get("timezone", "local")
    fmt = args.format or config.get("general", {}).get("format_copy", "%Y-%m-%D")

    today_bs, _ = get_today_bs(tz)
    date_text = format_bs_date(today_bs, fmt, lang=lang)

    try:
        subprocess.run(["wl-copy"], input=date_text.encode("utf-8"), check=True)
        print(f"Copied '{date_text}' to Wayland clipboard.")
    except FileNotFoundError:
        try:
            subprocess.run(["xclip", "-selection", "clipboard"], input=date_text.encode("utf-8"), check=True)
            print(f"Copied '{date_text}' to X11 clipboard.")
        except Exception:
            print(date_text)


def cmd_events(args, config, event_mgr):
    lang = config.get("general", {}).get("language", "ne")
    tz = config.get("general", {}).get("timezone", "local")
    today_bs, _ = get_today_bs(tz)

    limit = args.upcoming or 10
    upcoming = event_mgr.get_upcoming_events(today_bs, limit=limit)

    for b_date, ev in upcoming:
        day_str = to_devanagari_num(b_date.day) if lang == "ne" else str(b_date.day)
        m_name = get_month_name(b_date.month, lang)
        w_name = get_weekday_name(b_date.weekday, lang, short=False)
        y_str = to_devanagari_num(b_date.year) if lang == "ne" else str(b_date.year)
        ad_date = b_date.to_ad()
        flag = "🚩 [Public Holiday]" if ev.is_holiday else "✨ [Festival/Event]"

        print(f"  ┌─ 📅 {w_name}, {day_str} {m_name} {y_str} (AD: {ad_date.strftime('%b %d, %Y')})")
        print(f"  │  Festival: {ev.get_title(lang)}  {flag}")
        if ev.tithi:
            print(f"  │  Tithi:    {ev.tithi}")
        print("  └────────────────────────────────────────────────────────────")
    print()


def cmd_panchanga(args, config, event_mgr):
    tz = config.get("general", {}).get("timezone", "local")
    today_bs, _ = get_today_bs(tz)
    tithi_str = event_mgr.get_tithi_for_date(today_bs)
    panch = calculate_panchanga(today_bs, tithi_str)

    print("\n🇳🇵 Kathmandu Solar Panchanga (वि.सं.):")
    print(f"  Date:       {today_bs.year:04d}-{today_bs.month:02d}-{today_bs.day:02d} ({get_weekday_name(today_bs.weekday, 'ne')})")
    print(f"  Tithi:      {panch.tithi}")
    print(f"  Sun Sign:   {panch.sun_rashi}")
    print(f"  Sunrise:    {panch.sunrise}")
    print(f"  Sunset:     {panch.sunset} (Day Length: {panch.day_length})")
    print(f"  Rahu Kaal:  {panch.rahu_kaal}\n")


def cmd_clock(args, config, event_mgr):
    status = get_nepal_clock_status(event_mgr)
    print("\n🇳🇵 Nepal Standard Time & Office Status:")
    print(f"  Time:        {status.nepal_time_str}")
    print(f"  Date:        {status.current_bs.year:04d}-{status.current_bs.month:02d}-{status.current_bs.day:02d}")
    print(f"  Status:      {status.status_label_ne} / {status.status_label_en}")
    print(f"  Local Delta: {status.time_diff_str}\n")


def cmd_age(args, config, event_mgr):
    dob_str = args.dob.strip()
    try:
        parts = [int(p) for p in dob_str.replace("/", "-").split("-")]
        if len(parts) != 3:
            raise ValueError
        dob_bs = BSDate(parts[0], parts[1], parts[2])
    except Exception:
        print(f"Error: Invalid date of birth '{dob_str}'. Expected BS YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    res = calculate_age(dob_bs)
    print(f"\n🎂 Age Calculation for DOB: {dob_bs.year:04d}-{dob_bs.month:02d}-{dob_bs.day:02d} (BS):")
    print(f"  Age:           {res.years} Years, {res.months} Months, {res.days} Days")
    print(f"  Total Days:    {res.total_days} Days Lived")
    print(f"  Birth Weekday: {res.birth_weekday_ne} ({res.birth_weekday_en})")
    print(f"  Next Birthday: in {res.next_birthday_in_days} Days\n")


def cmd_shift(args, config, event_mgr):
    date_str = args.date.strip()
    days = args.days
    try:
        parts = [int(p) for p in date_str.replace("/", "-").split("-")]
        bs_d = BSDate(parts[0], parts[1], parts[2])
    except Exception:
        print(f"Error: Invalid date '{date_str}'. Expected YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    new_d = shift_days(bs_d, days)
    print(f"{bs_d.year:04d}-{bs_d.month:02d}-{bs_d.day:02d} + ({days} days) -> {new_d.year:04d}-{new_d.month:02d}-{new_d.day:02d} ({get_weekday_name(new_d.weekday, 'ne')})")


def cmd_long_weekends(args, config, event_mgr):
    tz = config.get("general", {}).get("timezone", "local")
    today_bs, _ = get_today_bs(tz)

    year = args.year or today_bs.year
    month = args.month or today_bs.month

    results = detect_long_weekends(year, month, event_mgr)
    m_name = get_month_name(month, "ne")

    print(f"\n🏖️ Long Weekend Streaks for {m_name} {year} BS:")
    if not results:
        print("  No long weekend streaks (>= 2 days off) in this month.\n")
        return

    for streak in results:
        hol_str = f" ({', '.join(streak.holiday_names)})" if streak.holiday_names else ""
        print(f"  • {streak.days_count} Days Off: {streak.start_str} to {streak.end_str}{hol_str}")
    print()


def cmd_search(args, config, event_mgr):
    query = args.query
    results = search_events(query)

    print(f"\n🔍 Search Results for '{query}':")
    if not results:
        print("  No matching festivals found.\n")
        return

    for idx, r in enumerate(results[:12]):
        y_str = to_devanagari_num(r.bs_date.year)
        d_str = to_devanagari_num(r.bs_date.day)
        m_str = get_month_name(r.bs_date.month, "ne")
        flag = "🚩 [Holiday]" if r.is_holiday else ""
        tithi_str = f"({r.tithi})" if r.tithi else ""
        print(f"  {idx+1:2d}. {d_str} {m_str} {y_str} (AD {r.ad_date.strftime('%b %d, %Y')}): {r.festival} {tithi_str} {flag}")
    print()


def cmd_update_events(args, config, event_mgr):
    print("⏳ Synchronizing latest festivals from remote TSV...")
    ok, count, msg = check_and_update(force=True)
    if ok:
        print(f"✨ {msg}")
    else:
        print(f"⚠️ {msg}")


def cmd_waybar(args, config, event_mgr):
    lang = config.get("general", {}).get("language", "ne")
    tz = config.get("general", {}).get("timezone", "local")
    bar_fmt = config.get("general", {}).get("format_bar", "🇳🇵 %Y %M %D")

    today_bs, today_ad = get_today_bs(tz)
    text = format_bs_date(today_bs, bar_fmt, lang=lang)
    alt_text = f"{today_bs.year:04d}-{today_bs.month:02d}-{today_bs.day:02d}"

    # Panchanga details
    tithi_str = event_mgr.get_tithi_for_date(today_bs)
    panch = calculate_panchanga(today_bs, tithi_str)
    clock_status = get_nepal_clock_status(event_mgr)

    weekday_name = get_weekday_name(today_bs.weekday, lang)
    day_str = to_devanagari_num(today_bs.day) if lang == "ne" else str(today_bs.day)
    m_name = get_month_name(today_bs.month, lang)
    yr_str = to_devanagari_num(today_bs.year) if lang == "ne" else str(today_bs.year)

    tooltip_lines = [
        f"{weekday_name}, {day_str} {m_name} {yr_str} (वि.सं.)",
        f"AD: {today_ad.strftime('%Y-%m-%d (%A)')}",
        f"🇳🇵 Nepal Time: {clock_status.nepal_time_str} {clock_status.status_label_ne if lang == 'ne' else clock_status.status_label_en}",
        f"✨ तिथि: {tithi_str}",
        f"☀️ Sunrise: {panch.sunrise} | Sunset: {panch.sunset} ({panch.day_length})",
        f"🪐 राशि: {panch.sun_rashi} | ⚠️ राहु काल: {panch.rahu_kaal}"
    ]

    # Today's events
    todays_events = event_mgr.get_events_for_date(today_bs)
    if todays_events:
        tooltip_lines.append("")
        for ev in todays_events:
            if ev.title_ne:
                tag = "🚩 [सार्वजनिक बिदा]" if ev.is_holiday else "✨ [पर्व]"
                tooltip_lines.append(f"{tag} {ev.get_title(lang)}")

    # Upcoming events
    upcoming_count = config.get("waybar", {}).get("upcoming_events_count", 3)
    upcoming = event_mgr.get_upcoming_events(today_bs, limit=upcoming_count)
    if upcoming:
        tooltip_lines.append("\nआगामी पर्व/बिदा:" if lang == "ne" else "\nUpcoming Events:")
        for b_date, ev in upcoming:
            if b_date.day == today_bs.day and b_date.month == today_bs.month:
                continue
            d_str = to_devanagari_num(b_date.day) if lang == "ne" else str(b_date.day)
            mn = get_month_name(b_date.month, lang)
            tooltip_lines.append(f"• {d_str} {mn}: {ev.get_title(lang)}")

    # CSS class
    css_class = "normal"
    if today_bs.weekday == 6:
        css_class = "saturday"
    elif event_mgr.is_public_holiday(today_bs):
        css_class = "holiday"

    payload = {
        "text": text,
        "alt": alt_text,
        "tooltip": "\n".join(tooltip_lines),
        "class": css_class
    }

    print(json.dumps(payload, ensure_ascii=False))


def cmd_toggle_lang(args, config, event_mgr):
    new_lang = toggle_language()
    print(f"Language switched to: {'नेपाली (Devanagari)' if new_lang == 'ne' else 'English (Romanized)'}")


def cmd_tui(args, config, event_mgr):
    from .tui import CalendarTUI
    app = CalendarTUI()
    app.run()


def main():
    parser = argparse.ArgumentParser(
        prog="omarchy-nepali-calendar",
        description="Bikram Sambat (BS) Nepali Calendar & Panchanga for Omarchy"
    )
    subparsers = parser.add_subparsers(dest="command")

    # today
    p_today = subparsers.add_parser("today", help="Print formatted today's BS date")
    p_today.add_argument("--lang", choices=["ne", "en"], help="Language (ne/en)")
    p_today.add_argument("--tz", choices=["local", "npt", "NPT"], help="Timezone mode")
    p_today.add_argument("--format", help="Custom format string")

    # cal
    p_cal = subparsers.add_parser("cal", help="Display monthly calendar grid")
    p_cal.add_argument("month", nargs="?", type=int, help="Month (1-12)")
    p_cal.add_argument("year", nargs="?", type=int, help="Year (1975-2100)")
    p_cal.add_argument("--lang", choices=["ne", "en"], help="Language (ne/en)")

    # convert
    p_conv = subparsers.add_parser("convert", help="Convert date between AD and BS")
    p_conv.add_argument("date", help="Date string YYYY-MM-DD")
    p_conv.add_argument("--to-bs", action="store_true", help="Force convert AD to BS")
    p_conv.add_argument("--to-ad", action="store_true", help="Force convert BS to AD")

    # copy
    p_copy = subparsers.add_parser("copy", help="Copy today's BS date to clipboard")
    p_copy.add_argument("--format", help="Custom format string")

    # events
    p_events = subparsers.add_parser("events", help="List upcoming festivals & holidays")
    p_events.add_argument("--upcoming", type=int, default=10, help="Number of upcoming events")

    # panchanga
    subparsers.add_parser("panchanga", help="View Kathmandu solar Panchanga for today")

    # clock
    subparsers.add_parser("clock", help="View live Nepal Standard Time & Office status")

    # age
    p_age = subparsers.add_parser("age", help="Calculate exact age in BS")
    p_age.add_argument("dob", help="Date of Birth in BS YYYY-MM-DD")

    # shift
    p_shift = subparsers.add_parser("shift", help="Shift BS date by N days")
    p_shift.add_argument("date", help="BS Date YYYY-MM-DD")
    p_shift.add_argument("days", type=int, help="Days to shift (+/-)")

    # long-weekends
    p_lw = subparsers.add_parser("long-weekends", help="Detect long weekend streaks in a month")
    p_lw.add_argument("month", nargs="?", type=int, help="Month (1-12)")
    p_lw.add_argument("year", nargs="?", type=int, help="Year (1975-2100)")

    # search
    p_search = subparsers.add_parser("search", help="Search festivals by Romanized/Nepali keyword")
    p_search.add_argument("query", help="Keyword (e.g. dashain, tihar, teej, shivaratri)")

    # update-events
    subparsers.add_parser("update-events", help="Sync latest festivals from remote TSV repository")

    # waybar
    subparsers.add_parser("waybar", help="Output Waybar JSON payload")

    # toggle-lang
    subparsers.add_parser("toggle-lang", help="Toggle language between ne and en")

    # tui
    subparsers.add_parser("tui", help="Launch interactive curses calendar modal")

    args = parser.parse_args()

    config = load_config()
    event_mgr = EventManager(EVENTS_FILE if EVENTS_FILE.exists() else None)

    if not args.command:
        class DefaultArgs:
            month = None
            year = None
            lang = None
        cmd_cal(DefaultArgs(), config, event_mgr)
        return

    commands = {
        "today": cmd_today,
        "cal": cmd_cal,
        "convert": cmd_convert,
        "copy": cmd_copy,
        "events": cmd_events,
        "panchanga": cmd_panchanga,
        "clock": cmd_clock,
        "age": cmd_age,
        "shift": cmd_shift,
        "long-weekends": cmd_long_weekends,
        "search": cmd_search,
        "update-events": cmd_update_events,
        "waybar": cmd_waybar,
        "toggle-lang": cmd_toggle_lang,
        "tui": cmd_tui
    }

    if args.command in commands:
        commands[args.command](args, config, event_mgr)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
