"""
Interactive Curses TUI Calendar for Nepali Calendar.
Includes: Live Nepal Clock banner, 2-line day cells with AD subscripts, Month Progress bar,
Panchanga panel, Visual Range Mode (v/V), In-App Festival Search (/ or s),
In-App Date Converter (c), In-App Help Modal (?), Long Weekend Inspector (W),
Copy (y/yi), and Remote Sync (u).
"""

import curses
import subprocess
from datetime import date
from typing import Optional, List

from .engine import (
    BSDate,
    ad_to_bs,
    bs_to_ad,
    get_days_in_bs_month,
    get_today_bs,
)
from .formatter import (
    get_month_name,
    get_weekday_name,
    to_devanagari_num,
    WEEKDAYS_SHORT_NE,
    WEEKDAYS_SHORT_EN,
)
from .holidays import EventManager
from .panchanga import calculate_panchanga
from .calculator import get_nepal_clock_status, calculate_age, detect_long_weekends
from .festivals import search_events
from .updater import check_and_update
from .config import load_config, EVENTS_FILE


class CalendarTUI:
    def __init__(self, start_date: Optional[BSDate] = None):
        self.config = load_config()
        self.lang = self.config.get("general", {}).get("language", "ne")
        self.tz = self.config.get("general", {}).get("timezone", "local")
        self.today_bs, self.today_ad = get_today_bs(self.tz)

        if start_date:
            self.cur_year = start_date.year
            self.cur_month = start_date.month
            self.selected_day = start_date.day
        else:
            self.cur_year = self.today_bs.year
            self.cur_month = self.today_bs.month
            self.selected_day = self.today_bs.day

        self.event_mgr = EventManager(EVENTS_FILE if EVENTS_FILE.exists() else None)
        
        # Visual range selection state
        self.visual_mode = False  # False, 'day', 'week'
        self.visual_start_day = None

        # Toggles
        self.show_long_weekends = False

        # Notification / status line message
        self.status_msg = ""

    def run(self):
        curses.wrapper(self._main)

    def _main(self, stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)
        curses.use_default_colors()

        # Initialize colors
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_GREEN, -1)   # Today
            curses.init_pair(2, curses.COLOR_RED, -1)     # Saturday / Holiday
            curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Tithi / Panchanga
            curses.init_pair(4, curses.COLOR_CYAN, -1)    # Headers
            curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE) # Cursor
            curses.init_pair(6, curses.COLOR_MAGENTA, -1) # Visual range
            curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Modals

        while True:
            stdscr.clear()
            self._render(stdscr)
            stdscr.refresh()

            try:
                key = stdscr.getch()
            except KeyboardInterrupt:
                break

            self.status_msg = ""

            if key in (ord('q'), ord('Q'), 27):  # 'q' or Esc
                if self.visual_mode:
                    self.visual_mode = False
                    self.visual_start_day = None
                else:
                    break
            elif key in (curses.KEY_LEFT, ord('h')):
                self._move_day(-1)
            elif key in (curses.KEY_RIGHT, ord('l')):
                self._move_day(1)
            elif key in (curses.KEY_UP, ord('k')):
                self._move_day(-7)
            elif key in (curses.KEY_DOWN, ord('j')):
                self._move_day(7)
            elif key in (ord('n'), ord(']')):  # Next month
                self._change_month(1)
            elif key in (ord('p'), ord('[')):  # Prev month
                self._change_month(-1)
            elif key in (ord('N'), ord('}'), ord('L')):  # Next year
                self._change_year(1)
            elif key in (ord('P'), ord('{'), ord('H')):  # Prev year
                self._change_year(-1)
            elif key in (ord('t'), ord('T')):  # Today
                self.cur_year = self.today_bs.year
                self.cur_month = self.today_bs.month
                self.selected_day = self.today_bs.day
                self.visual_mode = False
            elif key in (9, ord('\t')):  # Tab: Toggle Language
                self.lang = "en" if self.lang == "ne" else "ne"
            elif key == ord('v'):  # Toggle Visual day mode
                if self.visual_mode == 'day':
                    self.visual_mode = False
                    self.visual_start_day = None
                else:
                    self.visual_mode = 'day'
                    self.visual_start_day = self.selected_day
            elif key == ord('V'):  # Select week mode
                self.visual_mode = 'week'
                sel_bs = BSDate(self.cur_year, self.cur_month, self.selected_day)
                wday = sel_bs.weekday  # 0=Sunday
                max_d = get_days_in_bs_month(self.cur_year, self.cur_month)
                self.visual_start_day = max(1, self.selected_day - wday)
                self.selected_day = min(max_d, self.visual_start_day + 6)
            elif key in (ord('/'), ord('s')):  # Search
                self._open_search_modal(stdscr)
            elif key in (ord('c'), ord('C')):  # Date Converter
                self._open_converter_modal(stdscr)
            elif key == ord('?'):  # Help Dialog
                self._open_help_modal(stdscr)
            elif key == ord('W'):  # Toggle Long Weekends View
                self.show_long_weekends = not self.show_long_weekends
                self.status_msg = f"Long Weekends: {'Shown' if self.show_long_weekends else 'Hidden'}"
            elif key == ord('u'):  # Sync
                self._run_remote_update(stdscr)
            elif key == ord('y'):  # Copy date / range
                self._copy_selection(iso=False)
            elif key in (ord('Y'), ord('i')):  # Copy ISO
                self._copy_selection(iso=True)

    def _move_day(self, delta: int):
        max_days = get_days_in_bs_month(self.cur_year, self.cur_month)
        new_day = self.selected_day + delta

        if 1 <= new_day <= max_days:
            self.selected_day = new_day
        elif new_day < 1:
            self._change_month(-1)
            prev_max = get_days_in_bs_month(self.cur_year, self.cur_month)
            self.selected_day = max(1, prev_max + new_day)
        else:
            overflow = new_day - max_days
            self._change_month(1)
            self.selected_day = min(overflow, get_days_in_bs_month(self.cur_year, self.cur_month))

    def _change_month(self, delta: int):
        self.cur_month += delta
        if self.cur_month > 12:
            self.cur_month = 1
            self.cur_year += 1
        elif self.cur_month < 1:
            self.cur_month = 12
            self.cur_year -= 1

        self.cur_year = max(1975, min(2100, self.cur_year))
        max_days = get_days_in_bs_month(self.cur_year, self.cur_month)
        self.selected_day = min(self.selected_day, max_days)
        if self.visual_mode:
            self.visual_start_day = self.selected_day

    def _change_year(self, delta: int):
        self.cur_year = max(1975, min(2100, self.cur_year + delta))
        max_days = get_days_in_bs_month(self.cur_year, self.cur_month)
        self.selected_day = min(self.selected_day, max_days)
        if self.visual_mode:
            self.visual_start_day = self.selected_day

    def _copy_selection(self, iso: bool = False):
        if self.visual_mode and self.visual_start_day:
            s_day = min(self.visual_start_day, self.selected_day)
            e_day = max(self.visual_start_day, self.selected_day)
            s_bs = BSDate(self.cur_year, self.cur_month, s_day)
            e_bs = BSDate(self.cur_year, self.cur_month, e_day)
            if iso:
                text = f"{s_bs.year:04d}-{s_bs.month:02d}-{s_bs.day:02d} to {e_bs.year:04d}-{e_bs.month:02d}-{e_bs.day:02d}"
            else:
                m_name = get_month_name(self.cur_month, self.lang)
                y_str = to_devanagari_num(self.cur_year) if self.lang == "ne" else str(self.cur_year)
                text = f"{to_devanagari_num(s_day)} – {to_devanagari_num(e_day)} {m_name} {y_str}"
        else:
            bs = BSDate(self.cur_year, self.cur_month, self.selected_day)
            if iso:
                text = f"{bs.year:04d}-{bs.month:02d}-{bs.day:02d}"
            else:
                from .formatter import format_bs_date
                text = format_bs_date(bs, "%W, %D %M %Y (%T)", lang=self.lang)

        try:
            subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=True)
            self.status_msg = f"📋 Copied '{text}' to clipboard!"
        except Exception:
            self.status_msg = f"Copied: {text}"

    def _run_remote_update(self, stdscr):
        stdscr.addstr(0, 2, "⏳ Syncing latest festivals from remote...", curses.color_pair(3) | curses.A_BOLD)
        stdscr.refresh()
        ok, count, msg = check_and_update(force=True)
        self.status_msg = f"✨ {msg}" if ok else f"⚠️ {msg}"

    def _open_converter_modal(self, stdscr):
        h, w = stdscr.getmaxyx()
        curses.echo()
        curses.curs_set(1)

        win = curses.newwin(9, min(60, w - 4), max(2, (h - 9) // 2), max(2, (w - 60) // 2))
        win.box()
        win.addstr(1, 2, "🔄 Convert Date (YYYY-MM-DD):", curses.A_BOLD)
        win.addstr(2, 2, "Enter AD or BS date to convert & jump:", curses.A_DIM)
        win.refresh()

        try:
            inp = win.getstr(4, 2, 20).decode("utf-8").strip()
        except Exception:
            inp = ""

        curses.noecho()
        curses.curs_set(0)

        if not inp:
            return

        try:
            parts = [int(p) for p in inp.replace("/", "-").split("-")]
            if len(parts) != 3:
                raise ValueError
            y, m, d = parts[0], parts[1], parts[2]
            if y >= 2045:  # BS -> AD
                bs_obj = BSDate(y, m, d)
                ad_obj = bs_obj.to_ad()
                self.cur_year, self.cur_month, self.selected_day = bs_obj.year, bs_obj.month, bs_obj.day
                self.status_msg = f"BS {bs_obj.year}-{bs_obj.month:02d}-{bs_obj.day:02d} -> AD {ad_obj.strftime('%Y-%m-%d (%A)')}"
            else:  # AD -> BS
                ad_obj = date(y, m, d)
                bs_obj = ad_to_bs(ad_obj)
                self.cur_year, self.cur_month, self.selected_day = bs_obj.year, bs_obj.month, bs_obj.day
                self.status_msg = f"AD {ad_obj.strftime('%Y-%m-%d')} -> BS {bs_obj.year}-{bs_obj.month:02d}-{bs_obj.day:02d}"
        except Exception as e:
            self.status_msg = f"Error converting date: {e}"

    def _open_help_modal(self, stdscr):
        h, w = stdscr.getmaxyx()
        win_w = min(72, w - 4)
        win_h = min(22, h - 2)
        win = curses.newwin(win_h, win_w, max(1, (h - win_h) // 2), max(2, (w - win_w) // 2))
        win.box()

        win.addstr(1, 2, "📖 Nepali Calendar Navigation & Keybindings", curses.color_pair(4) | curses.A_BOLD)
        win.addstr(2, 2, "─" * (win_w - 4), curses.A_DIM)

        help_items = [
            ("🧭 Navigation", "hjkl / Arrows : Move cursor | t : Jump to today"),
            ("📅 Month/Year", "n / p / [/] : Next/Prev month | N / P / H / L : Next/Prev year"),
            ("📐 Selection", "v : Toggle visual day range | V : Select entire week"),
            ("🔍 Search", "/ or s : Search 3,280+ festivals by keyword/synonym"),
            ("🔄 Converter", "c : Open in-app AD <-> BS date converter & jump"),
            ("🏖️ Weekends", "W : Toggle long weekend streaks view"),
            ("📋 Clipboard", "y : Copy formatted date/range | yi / Y : Copy ISO date"),
            ("🌐 Language", "Tab : Toggle Nepali (देवनागरी) <-> English (Romanized)"),
            ("✨ Remote Sync", "u : Synchronize latest festivals from remote repository"),
            ("🚪 Exit", "q / Esc : Close help or quit modal")
        ]

        for idx, (cat, desc) in enumerate(help_items):
            if 3 + idx < win_h - 2:
                win.addstr(3 + idx, 2, f"{cat:14} ", curses.color_pair(3) | curses.A_BOLD)
                win.addstr(3 + idx, 17, desc[:win_w - 19])

        win.addstr(win_h - 2, 2, "Press any key to close this help dialog...", curses.A_DIM)
        win.refresh()
        win.getch()

    def _open_search_modal(self, stdscr):
        h, w = stdscr.getmaxyx()
        curses.echo()
        curses.curs_set(1)

        search_win = curses.newwin(12, min(70, w - 4), max(2, (h - 12) // 2), max(2, (w - 70) // 2))
        search_win.box()
        search_win.keypad(True)

        prompt = "🔍 Search Festival / Event (e.g. dashain, tihar, teej): "
        search_win.addstr(1, 2, prompt, curses.A_BOLD)
        search_win.refresh()

        try:
            query = search_win.getstr(2, 2, 40).decode("utf-8").strip()
        except Exception:
            query = ""

        curses.noecho()
        curses.curs_set(0)

        if not query:
            return

        ref_bs = BSDate(self.cur_year, self.cur_month, self.selected_day)
        results = search_events(query, ref_bs)

        if not results:
            self.status_msg = f"No festivals found matching '{query}'"
            return

        search_win.clear()
        search_win.box()
        search_win.addstr(1, 2, f"Results for '{query}' (Press 1-{min(6, len(results))} to jump, 'q' to cancel):", curses.A_BOLD)

        for idx, res in enumerate(results[:6]):
            m_name = get_month_name(res.bs_date.month, self.lang)
            d_str = to_devanagari_num(res.bs_date.day) if self.lang == "ne" else str(res.bs_date.day)
            y_str = to_devanagari_num(res.bs_date.year) if self.lang == "ne" else str(res.bs_date.year)
            line = f" [{idx+1}] {d_str} {m_name} {y_str}: {res.festival} ({res.ad_date.strftime('%b %d')})"
            search_win.addstr(3 + idx, 2, line[:min(65, w - 8)])

        search_win.refresh()
        ch = search_win.getch()

        if ord('1') <= ch <= ord('6'):
            sel_idx = ch - ord('1')
            if sel_idx < len(results):
                target = results[sel_idx]
                self.cur_year = target.bs_date.year
                self.cur_month = target.bs_date.month
                self.selected_day = target.bs_date.day
                self.status_msg = f"Jumped to: {target.festival}"

    def _render(self, stdscr):
        h, w = stdscr.getmaxyx()
        month_name = get_month_name(self.cur_month, self.lang)
        year_str = to_devanagari_num(self.cur_year) if self.lang == "ne" else str(self.cur_year)

        # 1. Nepal Clock & Office Status Banner
        clock_status = get_nepal_clock_status(self.event_mgr)
        clock_text = f"🇳🇵 Nepal Time: {clock_status.nepal_time_str} {clock_status.status_label_ne if self.lang == 'ne' else clock_status.status_label_en}  (Local: {clock_status.time_diff_str})"
        stdscr.addstr(1, max(2, (w - len(clock_text)) // 2), clock_text, curses.color_pair(4) | curses.A_BOLD)

        # 2. Month & Year Title + Progress Bar
        first_bs = BSDate(self.cur_year, self.cur_month, 1)
        first_ad = first_bs.to_ad()
        max_days = get_days_in_bs_month(self.cur_year, self.cur_month)
        last_bs = BSDate(self.cur_year, self.cur_month, max_days)
        last_ad = last_bs.to_ad()

        # Month progress
        pct = int((self.selected_day / max_days) * 100)
        prog_bar = f"[{'█' * (pct // 10)}{'░' * (10 - pct // 10)}] {pct}%"

        title = f"{month_name} {year_str} (वि.सं.)  |  AD: {first_ad.strftime('%b %d')} – {last_ad.strftime('%b %d, %Y')}  |  {prog_bar}"
        stdscr.addstr(3, max(2, (w - len(title)) // 2), title, curses.A_BOLD)

        # 3. Weekday Headers
        headers = WEEKDAYS_SHORT_NE if self.lang == "ne" else WEEKDAYS_SHORT_EN
        col_width = 8
        start_x = max(2, (w - (col_width * 7)) // 2)

        for idx, day_name in enumerate(headers):
            attr = curses.color_pair(2) if idx == 6 else curses.color_pair(4)
            stdscr.addstr(5, start_x + (idx * col_width), f"{day_name:^7}", attr | curses.A_BOLD)

        stdscr.addstr(6, start_x, "─" * (col_width * 7), curses.A_DIM)

        # 4. 2-Line Day Cards Matrix
        first_weekday = first_bs.weekday  # 0=Sunday
        cur_row = 7
        cur_col = first_weekday

        # Range bounds if visual mode
        v_min = v_max = None
        if self.visual_mode and self.visual_start_day:
            v_min = min(self.visual_start_day, self.selected_day)
            v_max = max(self.visual_start_day, self.selected_day)

        for day in range(1, max_days + 1):
            day_bs = BSDate(self.cur_year, self.cur_month, day)
            day_ad = day_bs.to_ad()
            day_str = to_devanagari_num(f"{day}") if self.lang == "ne" else f"{day}"
            ad_sub = f"({day_ad.day})"

            is_today = (self.cur_year == self.today_bs.year and 
                        self.cur_month == self.today_bs.month and 
                        day == self.today_bs.day)
            is_cursor = (day == self.selected_day)
            is_in_visual = (v_min is not None and v_min <= day <= v_max)
            is_sat = (cur_col == 6)
            is_hol = self.event_mgr.is_public_holiday(day_bs)
            hol_star = "*" if is_hol and not is_sat else " "

            x = start_x + (cur_col * col_width)
            y = cur_row

            # Determine Card Styling
            attr = curses.A_NORMAL
            if is_cursor:
                attr = curses.color_pair(5) | curses.A_BOLD
            elif is_in_visual:
                attr = curses.color_pair(6) | curses.A_BOLD
            elif is_today:
                attr = curses.color_pair(1) | curses.A_BOLD
            elif is_hol or is_sat:
                attr = curses.color_pair(2) | curses.A_BOLD

            # Top Line: BS Date + Holiday Indicator
            top_text = f"{day_str:>3}{hol_star}"
            stdscr.addstr(y, x + 1, top_text, attr)

            # Bottom Line: Gregorian Subscript
            sub_attr = attr if (is_cursor or is_in_visual) else curses.A_DIM
            stdscr.addstr(y + 1, x + 1, f"{ad_sub:^5}", sub_attr)

            cur_col += 1
            if cur_col > 6:
                cur_col = 0
                cur_row += 2

        # 5. Details Card / Panchanga Panel / Long Weekends
        detail_y = cur_row + 2
        stdscr.addstr(detail_y, start_x, "─" * (col_width * 7), curses.A_DIM)

        sel_bs = BSDate(self.cur_year, self.cur_month, self.selected_day)
        sel_ad = sel_bs.to_ad()
        tithi_str = self.event_mgr.get_tithi_for_date(sel_bs)
        panch = calculate_panchanga(sel_bs, tithi_str)
        weekday_name = get_weekday_name(sel_bs.weekday, self.lang)
        day_str = to_devanagari_num(self.selected_day) if self.lang == "ne" else str(self.selected_day)

        if self.show_long_weekends:
            streaks = detect_long_weekends(self.cur_year, self.cur_month, self.event_mgr)
            stdscr.addstr(detail_y + 1, start_x, f"🏖️ Long Weekends in {month_name} {year_str}:", curses.color_pair(4) | curses.A_BOLD)
            if not streaks:
                stdscr.addstr(detail_y + 2, start_x, "No consecutive 2+ days off this month.", curses.A_DIM)
            else:
                for s_idx, st in enumerate(streaks[:3]):
                    hol_s = f" ({', '.join(st.holiday_names)})" if st.holiday_names else ""
                    stdscr.addstr(detail_y + 2 + s_idx, start_x, f"• {st.days_count} Days: {st.start_str} to {st.end_str}{hol_s}", curses.color_pair(2))
        elif self.visual_mode and v_min and v_max:
            stdscr.addstr(detail_y + 1, start_x, f"📐 Visual Range: {to_devanagari_num(v_min)} – {to_devanagari_num(v_max)} {month_name} ({v_max - v_min + 1} days)", curses.color_pair(6) | curses.A_BOLD)
            line_idx = 0
            for d in range(v_min, v_max + 1):
                if detail_y + 2 + line_idx >= h - 3:
                    break
                d_bs = BSDate(self.cur_year, self.cur_month, d)
                for ev in self.event_mgr.get_events_for_date(d_bs):
                    if ev.title_ne:
                        flag = "🚩 " if ev.is_holiday else "• "
                        d_text = f"{flag}{to_devanagari_num(d)} {month_name}: {ev.get_title(self.lang)}"
                        color = curses.color_pair(2) if ev.is_holiday else curses.color_pair(3)
                        stdscr.addstr(detail_y + 2 + line_idx, start_x, d_text[:min(len(d_text), w - start_x - 2)], color)
                        line_idx += 1
                        if detail_y + 2 + line_idx >= h - 3:
                            break
        else:
            # Single Day Mode
            info_line = f"📅 {weekday_name}, {day_str} {month_name} {year_str}  (AD: {sel_ad.strftime('%Y-%m-%d')})  |  ✨ तिथि: {tithi_str}"
            stdscr.addstr(detail_y + 1, start_x, info_line, curses.A_BOLD)

            # Solar Panchanga details
            p_line = f"☀️ Sunrise: {panch.sunrise} | Sunset: {panch.sunset} ({panch.day_length}) | 🪐 Rashi: {panch.sun_rashi} | ⚠️ Rahu: {panch.rahu_kaal}"
            stdscr.addstr(detail_y + 2, start_x, p_line, curses.color_pair(3))

            # Multi-line Events Display
            events = self.event_mgr.get_events_for_date(sel_bs)
            ev_offset = 0
            for ev in events:
                if ev.title_ne and (detail_y + 3 + ev_offset < h - 3):
                    flag = "🚩 [सार्वजनिक बिदा] " if ev.is_holiday else "✨ [पर्व/उत्सव] "
                    tithi_suffix = f" (तिथि: {ev.tithi})" if ev.tithi else ""
                    ev_text = f"{flag}{ev.get_title(self.lang)}{tithi_suffix}"
                    color = curses.color_pair(2) if ev.is_holiday else curses.color_pair(1)
                    stdscr.addstr(detail_y + 3 + ev_offset, start_x, ev_text[:min(len(ev_text), w - start_x - 2)], color | curses.A_BOLD)
                    ev_offset += 1

        # Status line message
        if self.status_msg:
            stdscr.addstr(h - 3, start_x, self.status_msg, curses.color_pair(1) | curses.A_BOLD)

        # Footer Help
        footer = "hjkl: Move | v/V: Range | /: Search | c: Convert | W: Weekends | ?: Help | q: Quit"
        stdscr.addstr(h - 1, max(2, (w - len(footer)) // 2), footer, curses.A_DIM)
