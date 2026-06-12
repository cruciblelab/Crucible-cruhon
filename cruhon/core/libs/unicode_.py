"""
Unicode character database for Cruhon — @unicode.*

Wraps Python's `unicodedata`: look up character names and categories,
normalize text, read numeric values, and strip accents. No `@import` needed.

━━━ LOOKUP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @unicode.name[char]        → official name, e.g. "A" → "LATIN CAPITAL LETTER A"
  @unicode.lookup[name]      → character from its name (inverse of name)
  @unicode.category[char]    → general category, e.g. "Lu", "Nd", "Po"
  @unicode.bidirectional[c]  → bidirectional class
  @unicode.combining[char]   → combining class (int)
  @unicode.mirrored[char]    → 1 if mirrored in bidi text else 0

━━━ NUMERIC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @unicode.numeric[char]     → numeric value, e.g. "½" → 0.5
  @unicode.digit[char]       → digit value, e.g. "7" → 7
  @unicode.decimal[char]     → decimal value of a decimal char

━━━ NORMALIZE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @unicode.normalize[form; s]→ normalize ("NFC", "NFD", "NFKC", "NFKD")
  @unicode.nfc[s]            → NFC normalization
  @unicode.nfd[s]            → NFD normalization
  @unicode.nfkc[s]           → NFKC normalization
  @unicode.nfkd[s]           → NFKD normalization
  @unicode.strip_accents[s]  → remove diacritics (NFKD + drop combining marks)

━━━ INFO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @unicode.unidata_version[] → Unicode database version string
"""
from ..registry import register_lib, register_lib_call

_UD = "__import__('unicodedata')"


def register():
    register_lib("unicode", "unicodedata")

    # ── LOOKUP ────────────────────────────────────────────────
    register_lib_call("unicode", "name",
        lambda a: f"{_UD}.name({a[0]})" if a else "''")

    register_lib_call("unicode", "lookup",
        lambda a: f"{_UD}.lookup({a[0]})" if a else "''")

    register_lib_call("unicode", "category",
        lambda a: f"{_UD}.category({a[0]})" if a else "''")

    register_lib_call("unicode", "bidirectional",
        lambda a: f"{_UD}.bidirectional({a[0]})" if a else "''")

    register_lib_call("unicode", "combining",
        lambda a: f"{_UD}.combining({a[0]})" if a else "0")

    register_lib_call("unicode", "mirrored",
        lambda a: f"{_UD}.mirrored({a[0]})" if a else "0")

    # ── NUMERIC ───────────────────────────────────────────────
    register_lib_call("unicode", "numeric",
        lambda a: f"{_UD}.numeric({a[0]})" if a else "0.0")

    register_lib_call("unicode", "digit",
        lambda a: f"{_UD}.digit({a[0]})" if a else "0")

    register_lib_call("unicode", "decimal",
        lambda a: f"{_UD}.decimal({a[0]})" if a else "0")

    # ── NORMALIZE ─────────────────────────────────────────────
    register_lib_call("unicode", "normalize",
        lambda a: f"{_UD}.normalize({a[0]}, {a[1]})" if len(a) > 1 else f"str({a[0]})" if a else "''")

    register_lib_call("unicode", "nfc",
        lambda a: f"{_UD}.normalize('NFC', {a[0]})" if a else "''")

    register_lib_call("unicode", "nfd",
        lambda a: f"{_UD}.normalize('NFD', {a[0]})" if a else "''")

    register_lib_call("unicode", "nfkc",
        lambda a: f"{_UD}.normalize('NFKC', {a[0]})" if a else "''")

    register_lib_call("unicode", "nfkd",
        lambda a: f"{_UD}.normalize('NFKD', {a[0]})" if a else "''")

    register_lib_call("unicode", "strip_accents",
        lambda a: (
            f"''.join(_c for _c in {_UD}.normalize('NFKD', {a[0]}) "
            f"if {_UD}.category(_c) != 'Mn')"
            if a else "''"
        ))

    # ── INFO ──────────────────────────────────────────────────
    register_lib_call("unicode", "unidata_version",
        lambda a: f"{_UD}.unidata_version")
