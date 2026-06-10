"""
Date & time stdlib wrappers for Cruhon — @date.*

Covers datetime / date / time / calendar / zoneinfo so a non-coder can do
every common date operation without writing strftime/timedelta by hand.

━━━ CURRENT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @date.now[]                     → datetime.now()
  @date.today[]                   → date.today()
  @date.utcnow[]                  → datetime aware UTC now
  @date.timestamp[]               → current Unix timestamp (float)

━━━ FORMAT / PARSE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @date.format[dt; pattern]       → strftime ("%Y-%m-%d %H:%M")
  @date.format[pattern]           → now formatted with pattern
  @date.parse[text; pattern]      → strptime → datetime
  @date.iso[dt]                   → ISO 8601 string
  @date.iso[]                     → now as ISO 8601
  @date.from_iso[text]            → datetime.fromisoformat
  @date.from_timestamp[ts]        → datetime.fromtimestamp

━━━ ARITHMETIC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @date.add[dt; days=; hours=; minutes=; seconds=; weeks=]   → dt + timedelta
  @date.sub[dt; days=; hours=; ...]                          → dt - timedelta
  @date.diff[a; b]                → timedelta (a - b)
  @date.diff_days[a; b]           → whole days between a and b
  @date.diff_seconds[a; b]        → total seconds between a and b
  @date.total_seconds[td]         → timedelta.total_seconds()
  @date.timedelta[days=; hours=; minutes=; seconds=; weeks=] → timedelta

━━━ MODIFY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @date.replace[dt; year=; month=; day=; hour=; minute=; second=]
  @date.combine[date; time]       → datetime.combine(date, time)

━━━ COMPONENTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @date.year[dt]   @date.month[dt]   @date.day[dt]
  @date.hour[dt]   @date.minute[dt]  @date.second[dt]
  @date.microsecond[dt]           → microsecond component
  @date.weekday[dt]               → 0=Monday … 6=Sunday
  @date.weekday_name[dt]          → "Monday" …
  @date.month_name[dt]            → "January" …
  @date.is_weekend[dt]            → bool
  @date.isocalendar[dt]           → (year, week, weekday) namedtuple
  @date.isoweek[dt]               → ISO week number
  @date.isoyear[dt]               → ISO year

━━━ TIMEZONE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @date.utc[]                     → timezone.utc constant
  @date.timezone["Europe/Istanbul"] → ZoneInfo object
  @date.to_timezone[dt; "US/Eastern"] → convert datetime to tz

━━━ BUILD ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @date.make[year; month; day]                 → date
  @date.make[year; month; day; hour; minute]   → datetime
  @date.make_time[hour; minute; second]        → time object
  @date.days_in_month[year; month]             → number of days

━━━ SLEEP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @date.sleep[seconds]            — pause execution
"""
from ..registry import register_lib, register_lib_call

_DT = "__import__('datetime')"
_TIME = "__import__('time')"
_CAL = "__import__('calendar')"


def _coerce(expr: str) -> str:
    """Wrap a value so it works whether it's already a datetime or an ISO string."""
    return (
        f"({expr} if hasattr({expr}, 'strftime') "
        f"else {_DT}.datetime.fromisoformat(str({expr})))"
    )


def register():
    register_lib("date", None)  # Builtin namespace, no @import needed

    # ── CURRENT ───────────────────────────────────────────────
    register_lib_call("date", "now",
        lambda a: f"{_DT}.datetime.now()")

    register_lib_call("date", "today",
        lambda a: f"{_DT}.date.today()")

    register_lib_call("date", "utcnow",
        lambda a: f"{_DT}.datetime.now({_DT}.timezone.utc)")

    register_lib_call("date", "timestamp",
        lambda a: f"{_TIME}.time()")

    # ── FORMAT / PARSE ────────────────────────────────────────
    # @date.format[dt; pattern]  or  @date.format[pattern] (uses now)
    register_lib_call("date", "format",
        lambda a: (
            f"{_coerce(a[0])}.strftime({a[1]})"
            if len(a) > 1 else
            f"{_DT}.datetime.now().strftime({a[0]})"
        ))

    register_lib_call("date", "parse",
        lambda a: f"{_DT}.datetime.strptime({a[0]}, {a[1]})")

    register_lib_call("date", "iso",
        lambda a: (
            f"{_coerce(a[0])}.isoformat()"
            if a else
            f"{_DT}.datetime.now().isoformat()"
        ))

    register_lib_call("date", "from_iso",
        lambda a: f"{_DT}.datetime.fromisoformat({a[0]})")

    register_lib_call("date", "from_timestamp",
        lambda a: f"{_DT}.datetime.fromtimestamp({a[0]})")

    # ── ARITHMETIC ────────────────────────────────────────────
    # add/sub use kwargs: @date.add[dt; days=3; hours=2]
    def _delta(a, sign):
        base = _coerce(a[0])
        kwargs = ", ".join(a[1:]) if len(a) > 1 else "days=0"
        return f"{base} {sign} {_DT}.timedelta({kwargs})"

    register_lib_call("date", "add", lambda a: _delta(a, "+"))
    register_lib_call("date", "sub", lambda a: _delta(a, "-"))

    register_lib_call("date", "diff",
        lambda a: f"({_coerce(a[0])} - {_coerce(a[1])})")

    register_lib_call("date", "diff_days",
        lambda a: f"({_coerce(a[0])} - {_coerce(a[1])}).days")

    register_lib_call("date", "diff_seconds",
        lambda a: f"({_coerce(a[0])} - {_coerce(a[1])}).total_seconds()")

    # ── COMPONENTS ────────────────────────────────────────────
    for part in ("year", "month", "day", "hour", "minute", "second"):
        register_lib_call("date", part,
            (lambda p: lambda a: f"{_coerce(a[0])}.{p}")(part))

    register_lib_call("date", "weekday",
        lambda a: f"{_coerce(a[0])}.weekday()")

    register_lib_call("date", "weekday_name",
        lambda a: f"{_coerce(a[0])}.strftime('%A')")

    register_lib_call("date", "month_name",
        lambda a: f"{_coerce(a[0])}.strftime('%B')")

    register_lib_call("date", "is_weekend",
        lambda a: f"({_coerce(a[0])}.weekday() >= 5)")

    # ── BUILD ─────────────────────────────────────────────────
    register_lib_call("date", "make",
        lambda a: (
            f"{_DT}.datetime({', '.join(a)})"
            if len(a) > 3 else
            f"{_DT}.date({', '.join(a)})"
        ))

    register_lib_call("date", "days_in_month",
        lambda a: f"{_CAL}.monthrange({a[0]}, {a[1]})[1]")

    # ── TIMEDELTA CONSTRUCTOR ─────────────────────────────────
    register_lib_call("date", "timedelta",
        lambda a: f"{_DT}.timedelta({', '.join(a) if a else 'days=0'})")

    register_lib_call("date", "total_seconds",
        lambda a: f"({a[0]}).total_seconds()")

    # ── MODIFY ────────────────────────────────────────────────
    register_lib_call("date", "replace",
        lambda a: f"{_coerce(a[0])}.replace({', '.join(a[1:])})")

    register_lib_call("date", "combine",
        lambda a: f"{_DT}.datetime.combine({a[0]}, {a[1]})")

    # ── EXTRA COMPONENTS ─────────────────────────────────────
    register_lib_call("date", "microsecond",
        lambda a: f"{_coerce(a[0])}.microsecond")

    register_lib_call("date", "isocalendar",
        lambda a: f"{_coerce(a[0])}.isocalendar()")

    register_lib_call("date", "isoweek",
        lambda a: f"{_coerce(a[0])}.isocalendar().week")

    register_lib_call("date", "isoyear",
        lambda a: f"{_coerce(a[0])}.isocalendar().year")

    # ── TIMEZONE ─────────────────────────────────────────────
    register_lib_call("date", "utc",
        lambda a: f"{_DT}.timezone.utc")

    register_lib_call("date", "timezone",
        lambda a: f"__import__('zoneinfo').ZoneInfo({a[0]})")

    register_lib_call("date", "to_timezone",
        lambda a: (
            f"{_coerce(a[0])}.astimezone(__import__('zoneinfo').ZoneInfo({a[1]}))"
            if len(a) > 1 else
            f"{_coerce(a[0])}.astimezone()"
        ))

    # ── EXTRA BUILD ───────────────────────────────────────────
    register_lib_call("date", "make_time",
        lambda a: f"{_DT}.time({', '.join(a)})")

    # ── SLEEP ─────────────────────────────────────────────────
    register_lib_call("date", "sleep",
        lambda a: f"{_TIME}.sleep({a[0]})" if a else f"{_TIME}.sleep(0)")
