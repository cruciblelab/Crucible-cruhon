"""
Calendar operations for Cruhon — @calendar.*

Wraps Python's `calendar` module: leap-year tests, month ranges, weekday
math, human-readable month/day names, and navigation helpers.
No `@import` needed.

━━━ LEAP YEARS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @calendar.is_leap[year]            → bool
  @calendar.leap_days[y1; y2]        → number of leap years in range [y1, y2)

━━━ MONTH INFO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @calendar.month_range[year; month] → (weekday_of_1st, number_of_days)
  @calendar.days_in_month[year; mon] → number of days in that month
  @calendar.weekday[y; m; d]         → weekday (Mon=0 … Sun=6)
  @calendar.month_name[month]        → "January" … "December"
  @calendar.month_abbr[month]        → "Jan" … "Dec"
  @calendar.day_name[weekday]        → "Monday" … "Sunday"
  @calendar.day_abbr[weekday]        → "Mon" … "Sun"

━━━ CALENDAR DATA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @calendar.month_dates[year; month] → matrix of week-rows (lists of day ints)
  @calendar.year_dates[year]         → nested calendar structure for the year
  @calendar.month_text[year; month]  → printable month as a string
  @calendar.year_text[year]          → full-year calendar as a string
  @calendar.weekheader[width]        → header row of abbreviated weekday names

━━━ WEEKDAY CHECKS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @calendar.is_weekday[y; m; d]      → True if Mon–Fri
  @calendar.is_weekend[y; m; d]      → True if Sat/Sun
  @calendar.first_weekday_of[y; m]   → weekday index (0-6) of the 1st of the month
  @calendar.get_first_weekday[]      → current locale first-weekday setting

━━━ DAY / WEEK NUMBERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @calendar.day_of_year[y; m; d]     → 1-indexed day number in the year
  @calendar.week_of_year[y; m; d]    → ISO week number

━━━ NAVIGATION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @calendar.quarter[month]           → quarter number (1–4)
  @calendar.next_month[y; m]         → (year, month) of the following month
  @calendar.prev_month[y; m]         → (year, month) of the preceding month

━━━ CONVERSION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @calendar.timegm[time_tuple]       → UTC timestamp from a struct_time tuple
"""
from ..registry import register_lib, register_lib_call

_C  = "__import__('calendar')"
_DT = "__import__('datetime')"


def register():
    register_lib("calendar", "calendar")

    # ── LEAP YEARS ────────────────────────────────────────────
    register_lib_call("calendar", "is_leap",
        lambda a: f"{_C}.isleap({a[0]})")

    register_lib_call("calendar", "leap_days",
        lambda a: f"{_C}.leapdays({a[0]}, {a[1]})" if len(a) > 1 else f"0")

    # ── MONTH INFO ────────────────────────────────────────────
    register_lib_call("calendar", "month_range",
        lambda a: f"{_C}.monthrange({a[0]}, {a[1]})" if len(a) > 1 else f"{_C}.monthrange({a[0]}, 1)")

    register_lib_call("calendar", "days_in_month",
        lambda a: f"{_C}.monthrange({a[0]}, {a[1]})[1]" if len(a) > 1 else f"{_C}.monthrange({a[0]}, 1)[1]")

    register_lib_call("calendar", "weekday",
        lambda a: f"{_C}.weekday({a[0]}, {a[1]}, {a[2]})" if len(a) > 2 else f"{_C}.weekday({a[0]}, 1, 1)")

    register_lib_call("calendar", "month_name",
        lambda a: f"{_C}.month_name[{a[0]}]")

    register_lib_call("calendar", "month_abbr",
        lambda a: f"{_C}.month_abbr[{a[0]}]")

    register_lib_call("calendar", "day_name",
        lambda a: f"{_C}.day_name[{a[0]}]")

    register_lib_call("calendar", "day_abbr",
        lambda a: f"{_C}.day_abbr[{a[0]}]")

    # ── CALENDAR DATA ─────────────────────────────────────────
    register_lib_call("calendar", "month_dates",
        lambda a: f"{_C}.monthcalendar({a[0]}, {a[1]})" if len(a) > 1 else f"{_C}.monthcalendar({a[0]}, 1)")

    register_lib_call("calendar", "year_dates",
        lambda a: f"{_C}.Calendar().yeardatescalendar({a[0]})")

    register_lib_call("calendar", "month_text",
        lambda a: f"{_C}.month({a[0]}, {a[1]})" if len(a) > 1 else f"{_C}.month({a[0]}, 1)")

    register_lib_call("calendar", "year_text",
        lambda a: f"{_C}.calendar({a[0]})" if a else "''")

    register_lib_call("calendar", "weekheader",
        lambda a: f"{_C}.weekheader({a[0]})" if a else f"{_C}.weekheader(3)")

    # ── WEEKDAY CHECKS ────────────────────────────────────────
    register_lib_call("calendar", "is_weekday",
        lambda a: (
            f"({_C}.weekday({a[0]}, {a[1]}, {a[2]}) < 5)"
            if len(a) > 2 else "False"
        ))

    register_lib_call("calendar", "is_weekend",
        lambda a: (
            f"({_C}.weekday({a[0]}, {a[1]}, {a[2]}) >= 5)"
            if len(a) > 2 else "False"
        ))

    register_lib_call("calendar", "first_weekday_of",
        lambda a: (
            f"{_C}.monthrange({a[0]}, {a[1]})[0]"
            if len(a) > 1 else "0"
        ))

    register_lib_call("calendar", "get_first_weekday",
        lambda a: f"{_C}.firstweekday()")

    # ── DAY / WEEK NUMBERS ────────────────────────────────────
    register_lib_call("calendar", "day_of_year",
        lambda a: (
            f"{_DT}.date({a[0]}, {a[1]}, {a[2]}).timetuple().tm_yday"
            if len(a) > 2 else "0"
        ))

    register_lib_call("calendar", "week_of_year",
        lambda a: (
            f"{_DT}.date({a[0]}, {a[1]}, {a[2]}).isocalendar()[1]"
            if len(a) > 2 else "0"
        ))

    # ── NAVIGATION ────────────────────────────────────────────
    register_lib_call("calendar", "quarter",
        lambda a: f"(int({a[0]}) - 1) // 3 + 1" if a else "0")

    register_lib_call("calendar", "next_month",
        lambda a: (
            f"(lambda _y, _m: (_y + 1, 1) if _m == 12 else (_y, _m + 1))({a[0]}, {a[1]})"
            if len(a) > 1 else "(0, 1)"
        ))

    register_lib_call("calendar", "prev_month",
        lambda a: (
            f"(lambda _y, _m: (_y - 1, 12) if _m == 1 else (_y, _m - 1))({a[0]}, {a[1]})"
            if len(a) > 1 else "(0, 12)"
        ))

    # ── CONVERSION ────────────────────────────────────────────
    register_lib_call("calendar", "timegm",
        lambda a: f"{_C}.timegm({a[0]})")
