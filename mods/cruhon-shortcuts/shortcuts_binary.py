"""
cruhon-shortcuts — binary group
=================================
Shortcuts for @string.*, @struct.*, @zlib.*, @calendar.*, and @email.* —
the stdlib namespaces backing this plugin (added to Cruhon core in v2.2).

Global aliases (source rewrites)
─────────────────────────────────

string:
@ascii_letters[]        → @string.ascii_letters[]
@ascii_lower[]          → @string.ascii_lowercase[]
@ascii_upper[]          → @string.ascii_uppercase[]
@digits[]               → @string.digits[]
@punctuation[]          → @string.punctuation[]
@whitespace[]           → @string.whitespace[]
@printable[]            → @string.printable[]
@capwords[s]            → @string.capwords[s]
@template[tpl]          → @string.template[tpl]
@substitute[tpl; m]     → @string.substitute[tpl; m]

struct:
@pack[fmt; ...]         → @struct.pack[fmt; ...]
@unpack[fmt; data]      → @struct.unpack[fmt; data]
@calcsize[fmt]          → @struct.calcsize[fmt]

zlib:
@compress[data]         → @zlib.compress[data]
@decompress[data]       → @zlib.decompress[data]
@crc32[data]            → @zlib.crc32[data]
@adler32[data]          → @zlib.adler32[data]

calendar:
@is_leap[year]          → @calendar.is_leap[year]
@days_in_month[y; m]    → @calendar.days_in_month[y; m]
@month_name_of[m]       → @calendar.month_name[m]
@day_name_of[w]         → @calendar.day_name[w]
@month_text[y; m]       → @calendar.month_text[y; m]

email:
@email_make[s; f; t; b] → @email.make[s; f; t; b]
@email_parse[raw]       → @email.parse[raw]
@parse_address[s]       → @email.parse_address[s]
@valid_email[s]         → @email.valid_address[s]

Namespace method aliases
─────────────────────────
@string.letters[]       → @string.ascii_letters[]
@string.lower[]         → @string.ascii_lowercase[]
@string.upper[]         → @string.ascii_uppercase[]
@string.tmpl[tpl]       → @string.template[tpl]
@string.sub[tpl; m]     → @string.substitute[tpl; m]
@struct.size[fmt]       → @struct.calcsize[fmt]
@struct.from_bytes[f; d]→ @struct.unpack[f; d]
@struct.to_bytes[f; v]  → @struct.pack[f; v]
@zlib.deflate[d]        → @zlib.compress[d]
@zlib.inflate[d]        → @zlib.decompress[d]
@calendar.leap[y]       → @calendar.is_leap[y]
@calendar.mdays[y; m]   → @calendar.days_in_month[y; m]
@email.msg[]            → @email.message[]
@email.from_string[r]   → @email.parse[r]

New methods (via api.lib_call)
───────────────────────────────
@string.random[n]           → random alphanumeric string of length n
@string.random[n; charset]  → random string from a custom charset
@string.is_in[s; charset]   → True if every char of s is in charset
@string.only[s; charset]    → keep only chars from charset
@struct.hexdump[data]       → space-separated hex string of bytes
@struct.from_hex[hex]       → bytes from a hex string
@zlib.compress_ratio[data]  → ratio of compressed-to-original size (float)
@calendar.is_weekday[y;m;d] → True if the date is Mon–Fri
@calendar.is_weekend[y;m;d] → True if the date is Sat/Sun
@calendar.first_weekday[y;m]→ weekday of the 1st of the month
@email.quick[to; subj; body]→ minimal EmailMessage with sensible defaults
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    # string
    "@ascii_letters[":  "@string.ascii_letters[",
    "@ascii_lower[":    "@string.ascii_lowercase[",
    "@ascii_upper[":    "@string.ascii_uppercase[",
    "@digits[":         "@string.digits[",
    "@punctuation[":    "@string.punctuation[",
    "@whitespace[":     "@string.whitespace[",
    "@printable[":      "@string.printable[",
    "@capwords[":       "@string.capwords[",
    "@template[":       "@string.template[",
    "@substitute[":     "@string.substitute[",
    # struct
    "@pack[":           "@struct.pack[",
    "@unpack[":         "@struct.unpack[",
    "@calcsize[":       "@struct.calcsize[",
    # zlib
    "@compress[":       "@zlib.compress[",
    "@decompress[":     "@zlib.decompress[",
    "@crc32[":          "@zlib.crc32[",
    "@adler32[":        "@zlib.adler32[",
    # calendar
    "@is_leap[":        "@calendar.is_leap[",
    "@days_in_month[":  "@calendar.days_in_month[",
    "@month_name_of[":  "@calendar.month_name[",
    "@day_name_of[":    "@calendar.day_name[",
    "@month_text[":     "@calendar.month_text[",
    # email
    "@email_make[":     "@email.make[",
    "@email_parse[":    "@email.parse[",
    "@parse_address[":  "@email.parse_address[",
    "@valid_email[":    "@email.valid_address[",
}

METHOD_ALIASES: dict[str, str] = {
    "@string.letters[":   "@string.ascii_letters[",
    "@string.lower[":     "@string.ascii_lowercase[",
    "@string.upper[":     "@string.ascii_uppercase[",
    "@string.tmpl[":      "@string.template[",
    "@string.sub[":       "@string.substitute[",
    "@struct.size[":      "@struct.calcsize[",
    "@struct.from_bytes[":"@struct.unpack[",
    "@struct.to_bytes[":  "@struct.pack[",
    "@zlib.deflate[":     "@zlib.compress[",
    "@zlib.inflate[":     "@zlib.decompress[",
    "@calendar.leap[":    "@calendar.is_leap[",
    "@calendar.mdays[":   "@calendar.days_in_month[",
    "@email.msg[":        "@email.message[",
    "@email.from_string[":"@email.parse[",
}

_RN  = "__import__('random')"
_STR = "__import__('string')"
_CAL = "__import__('calendar')"
_EM  = "__import__('email.message', fromlist=['EmailMessage'])"


def _new_lib_calls(api) -> None:

    # ── string ────────────────────────────────────────────────
    api.lib_call("string", "random", lambda a: (
        f"''.join({_RN}.choices({a[1]}, k={a[0]}))"
        if len(a) > 1 else
        f"''.join({_RN}.choices({_STR}.ascii_letters + {_STR}.digits, k={a[0]}))"
        if a else
        f"''.join({_RN}.choices({_STR}.ascii_letters + {_STR}.digits, k=12))"
    ))

    api.lib_call("string", "is_in", lambda a: (
        f"all(_c in {a[1]} for _c in str({a[0]}))"
        if len(a) > 1 else
        f"False"
    ))

    api.lib_call("string", "only", lambda a: (
        f"''.join(_c for _c in str({a[0]}) if _c in {a[1]})"
        if len(a) > 1 else
        f"str({a[0]})"
    ))

    # ── struct ────────────────────────────────────────────────
    api.lib_call("struct", "hexdump", lambda a: (
        f"' '.join(format(_b, '02x') for _b in {a[0]})"
        if a else
        f"''"
    ))

    api.lib_call("struct", "from_hex", lambda a: (
        f"bytes.fromhex(str({a[0]}).replace(' ', ''))"
        if a else
        f"b''"
    ))

    # ── zlib ──────────────────────────────────────────────────
    api.lib_call("zlib", "compress_ratio", lambda a: (
        f"(lambda _d: (lambda _raw, _comp: "
        f"len(_comp) / len(_raw) if _raw else 0.0)("
        f"(_d.encode('utf-8') if isinstance(_d, str) else _d), "
        f"__import__('zlib').compress(_d.encode('utf-8') if isinstance(_d, str) else _d)))"
        f"({a[0]})"
        if a else
        f"0.0"
    ))

    # ── calendar ──────────────────────────────────────────────
    api.lib_call("calendar", "is_weekday", lambda a: (
        f"({_CAL}.weekday({a[0]}, {a[1]}, {a[2]}) < 5)"
        if len(a) > 2 else
        f"False"
    ))

    api.lib_call("calendar", "is_weekend", lambda a: (
        f"({_CAL}.weekday({a[0]}, {a[1]}, {a[2]}) >= 5)"
        if len(a) > 2 else
        f"False"
    ))

    api.lib_call("calendar", "first_weekday", lambda a: (
        f"{_CAL}.monthrange({a[0]}, {a[1]})[0]"
        if len(a) > 1 else
        f"0"
    ))

    # ── email ─────────────────────────────────────────────────
    api.lib_call("email", "quick", lambda a: (
        f"(lambda _m: ("
        f"_m.__setitem__('To', {a[0]}), "
        f"_m.__setitem__('Subject', {a[1]}), "
        f"_m.set_content({a[2]}), _m)[-1])({_EM}.EmailMessage())"
        if len(a) > 2 else
        f"{_EM}.EmailMessage()"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
