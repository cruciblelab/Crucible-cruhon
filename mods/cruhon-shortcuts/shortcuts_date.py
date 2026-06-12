"""
cruhon-shortcuts — date group
==============================
Shortcuts for @date.* operations.

Global aliases (source rewrites)
─────────────────────────────────
@now[]                  → @date.now[]
@today[]                → @date.today[]
@utcnow[]               → @date.utcnow[]
@timestamp[]            → @date.timestamp[]
@ts[]                   → @date.timestamp[]
@fmt_date[fmt]          → @date.format[fmt]
@fmt_date[dt; fmt]      → @date.format[dt; fmt]
@parse_date[s; fmt]     → @date.parse[s; fmt]
@from_iso[s]            → @date.from_iso[s]
@date_add[dt; ...]      → @date.add[dt; ...]
@date_sub[dt; ...]      → @date.sub[dt; ...]
@date_diff[d1; d2]      → @date.diff[d1; d2]
@diff_days[d1; d2]      → @date.diff_days[d1; d2]
@diff_seconds[d1; d2]   → @date.diff_seconds[d1; d2]
@weekday[dt]            → @date.weekday[dt]
@weekday_name[dt]       → @date.weekday_name[dt]
@month_name[dt]         → @date.month_name[dt]
@is_weekend[dt]         → @date.is_weekend[dt]
@make_date[y; m; d]     → @date.make[y; m; d]
@date_iso[dt]           → @date.iso[dt]
@from_ts[ts]            → @date.from_timestamp[ts]
@date_utc[]             → @date.utc[]
@in_timezone[dt; tz]    → @date.to_timezone[dt; tz]

Namespace method aliases
─────────────────────────
@date.ts[]              → @date.timestamp[]
@date.fmt[fmt]          → @date.format[fmt]
@date.parse_iso[s]      → @date.from_iso[s]
@date.add_days[dt; n]   → @date.add[dt; days=n]
@date.delta[d1; d2]     → @date.diff_days[d1; d2]
@date.strftime[dt; fmt] → @date.format[dt; fmt]
@date.strptime[s; fmt]  → @date.parse[s; fmt]

New methods (via api.lib_call)
───────────────────────────────
@date.year[]            → current year (int)
@date.month_num[]       → current month number (int)
@date.day_num[]         → current day of month (int)
@date.hour[]            → current hour (int, 0–23)
@date.minute[]          → current minute (int)
@date.second[]          → current second (int)
@date.unix[]            → current Unix epoch (int)
@date.unixf[]           → current Unix epoch (float, with microseconds)
@date.date_str[]        → today as "YYYY-MM-DD" string
@date.time_str[]        → current time as "HH:MM:SS" string
@date.datetime_str[]    → "YYYY-MM-DD HH:MM:SS" string
@date.tomorrow[]        → tomorrow as datetime
@date.yesterday[]       → yesterday as datetime
@date.days_ago[n]       → datetime N days ago
@date.days_from_now[n]  → datetime N days from now
@date.months_ago[n]     → datetime N months ago (approx 30 days each)
@date.start_of_day[dt]  → midnight of dt
@date.end_of_day[dt]    → 23:59:59 of dt
@date.start_of_week[dt] → Monday of the week containing dt
@date.end_of_week[dt]   → Sunday of the week containing dt
@date.age[birthdate]    → age in years (int)
@date.since[dt]         → seconds since dt (float)
@date.until[dt]         → seconds until dt (float, negative if past)
@date.quarter[dt]       → quarter number 1–4
@date.is_leap[year]     → True if year is a leap year
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@now[":           "@date.now[",
    "@today[":         "@date.today[",
    "@utcnow[":        "@date.utcnow[",
    "@timestamp[":     "@date.timestamp[",
    "@ts[":            "@date.timestamp[",
    "@fmt_date[":      "@date.format[",
    "@parse_date[":    "@date.parse[",
    "@from_iso[":      "@date.from_iso[",
    "@date_add[":      "@date.add[",
    "@date_sub[":      "@date.sub[",
    "@date_diff[":     "@date.diff[",
    "@diff_days[":     "@date.diff_days[",
    "@diff_seconds[":  "@date.diff_seconds[",
    "@weekday[":       "@date.weekday[",
    "@weekday_name[":  "@date.weekday_name[",
    "@month_name[":    "@date.month_name[",
    "@is_weekend[":    "@date.is_weekend[",
    "@make_date[":     "@date.make[",
    "@date_iso[":      "@date.iso[",
    "@from_ts[":       "@date.from_timestamp[",
    "@date_utc[":      "@date.utc[",
    "@in_timezone[":   "@date.to_timezone[",
}

METHOD_ALIASES: dict[str, str] = {
    "@date.ts[":         "@date.timestamp[",
    "@date.fmt[":        "@date.format[",
    "@date.parse_iso[":  "@date.from_iso[",
    "@date.delta[":      "@date.diff_days[",
    "@date.strftime[":   "@date.format[",
    "@date.strptime[":   "@date.parse[",
    "@date.add_days[":   "@date.add[",
}

_DT = "__import__('datetime').datetime"
_D  = "__import__('datetime').date"
_TD = "__import__('datetime').timedelta"
_CAL = "__import__('calendar')"


def _new_lib_calls(api) -> None:

    # date.year, date.month, date.day, date.hour, date.minute, date.second already
    # exist in core (they take a datetime argument). We register distinct no-arg
    # variants that always return the CURRENT time component.
    api.lib_call("date", "cur_year",
        lambda a: f"{_DT}.now().year")

    api.lib_call("date", "cur_month",
        lambda a: f"{_DT}.now().month")

    api.lib_call("date", "cur_day",
        lambda a: f"{_DT}.now().day")

    api.lib_call("date", "cur_hour",
        lambda a: f"{_DT}.now().hour")

    api.lib_call("date", "cur_minute",
        lambda a: f"{_DT}.now().minute")

    api.lib_call("date", "cur_second",
        lambda a: f"{_DT}.now().second")

    api.lib_call("date", "unix",
        lambda a: f"int({_DT}.now().timestamp())")

    api.lib_call("date", "unixf",
        lambda a: f"{_DT}.now().timestamp()")

    api.lib_call("date", "date_str",
        lambda a: f"{_DT}.now().strftime('%Y-%m-%d')")

    api.lib_call("date", "time_str",
        lambda a: f"{_DT}.now().strftime('%H:%M:%S')")

    api.lib_call("date", "datetime_str",
        lambda a: f"{_DT}.now().strftime('%Y-%m-%d %H:%M:%S')")

    api.lib_call("date", "tomorrow",
        lambda a: f"({_DT}.now() + {_TD}(days=1))")

    api.lib_call("date", "yesterday",
        lambda a: f"({_DT}.now() - {_TD}(days=1))")

    api.lib_call("date", "days_ago",
        lambda a: f"({_DT}.now() - {_TD}(days={a[0]}))" if a else f"({_DT}.now() - {_TD}(days=1))")

    api.lib_call("date", "days_from_now",
        lambda a: f"({_DT}.now() + {_TD}(days={a[0]}))" if a else f"({_DT}.now() + {_TD}(days=1))")

    api.lib_call("date", "months_ago",
        lambda a: f"({_DT}.now() - {_TD}(days={a[0]} * 30))" if a else f"({_DT}.now() - {_TD}(days=30))")

    api.lib_call("date", "start_of_day",
        lambda a: (
            f"{a[0]}.replace(hour=0, minute=0, second=0, microsecond=0)"
            if a else
            f"{_DT}.now().replace(hour=0, minute=0, second=0, microsecond=0)"
        ))

    api.lib_call("date", "end_of_day",
        lambda a: (
            f"{a[0]}.replace(hour=23, minute=59, second=59, microsecond=999999)"
            if a else
            f"{_DT}.now().replace(hour=23, minute=59, second=59, microsecond=999999)"
        ))

    api.lib_call("date", "start_of_week",
        lambda a: (
            f"(lambda _d: _d - {_TD}(days=_d.weekday()))"
            f"({a[0]})"
            if a else
            f"(lambda _d: _d - {_TD}(days=_d.weekday()))"
            f"({_DT}.now())"
        ))

    api.lib_call("date", "end_of_week",
        lambda a: (
            f"(lambda _d: _d + {_TD}(days=6 - _d.weekday()))"
            f"({a[0]})"
            if a else
            f"(lambda _d: _d + {_TD}(days=6 - _d.weekday()))"
            f"({_DT}.now())"
        ))

    api.lib_call("date", "age",
        lambda a: (
            f"(lambda _b, _t: _t.year - _b.year - ((_t.month, _t.day) < (_b.month, _b.day)))"
            f"({a[0]}, {_DT}.now())"
            if a else
            f"0"
        ))

    api.lib_call("date", "since",
        lambda a: (
            f"({_DT}.now() - {a[0]}).total_seconds()"
            if a else
            f"0.0"
        ))

    api.lib_call("date", "until",
        lambda a: (
            f"({a[0]} - {_DT}.now()).total_seconds()"
            if a else
            f"0.0"
        ))

    api.lib_call("date", "quarter",
        lambda a: (
            f"(({a[0]}.month - 1) // 3 + 1)"
            if a else
            f"(({_DT}.now().month - 1) // 3 + 1)"
        ))

    api.lib_call("date", "is_leap",
        lambda a: (
            f"{_CAL}.isleap({a[0]})"
            if a else
            f"{_CAL}.isleap({_DT}.now().year)"
        ))

    api.lib_call("date", "add_days",
        lambda a: (
            f"({a[0]} + {_TD}(days={a[1]}))"
            if len(a) > 1 else
            f"({a[0]} + {_TD}(days=1))"
        ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
