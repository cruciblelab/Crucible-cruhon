"""
cruhon/core/libs/locale_.py
===========================
Locale-aware formatting for Cruhon — @locale.*

Format numbers and currency, and parse locale-formatted strings.

━━━ LOCALE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @locale.get[]                   → current locale (category, encoding)
  @locale.set[name]               → set LC_ALL ("" = user default, "C" = neutral)
  @locale.encoding[]              → preferred text encoding

━━━ NUMBERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @locale.number[n]               → group-formatted integer ("1,234,567")
  @locale.decimal[n]              → group-formatted float
  @locale.currency[n]             → currency string for the current locale
  @locale.atof[s]                 → parse a locale float string
  @locale.atoi[s]                 → parse a locale integer string
"""
from ..registry import register_lib, register_lib_call

_LC = "__import__('locale')"


def register():
    register_lib("locale", None)

    # ── Locale ────────────────────────────────────────────────
    register_lib_call("locale", "get",
        lambda a: f"{_LC}.getlocale()")
    register_lib_call("locale", "set",
        lambda a: f"{_LC}.setlocale({_LC}.LC_ALL, {a[0]})")
    register_lib_call("locale", "encoding",
        lambda a: f"{_LC}.getpreferredencoding()")

    # ── Numbers ───────────────────────────────────────────────
    register_lib_call("locale", "number",
        lambda a: f"{_LC}.format_string('%d', {a[0]}, grouping=True)")
    register_lib_call("locale", "decimal",
        lambda a: f"{_LC}.format_string('%f', {a[0]}, grouping=True)")
    register_lib_call("locale", "currency",
        lambda a: f"{_LC}.currency({a[0]})")
    register_lib_call("locale", "atof",
        lambda a: f"{_LC}.atof({a[0]})")
    register_lib_call("locale", "atoi",
        lambda a: f"{_LC}.atoi({a[0]})")
