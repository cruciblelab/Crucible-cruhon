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
@str_template[tpl]      → @string.template[tpl]
@substitute[tpl; m]     → @string.substitute[tpl; m]
@ascii_to_int[c]        → @string.ascii_to_int[c]
@int_to_ascii[n]        → @string.int_to_ascii[n]
@str_filter[s; chars]   → @string.filter[s; chars]
@str_exclude[s; chars]  → @string.exclude[s; chars]
@rnd_lower[n]           → @string.random_lower[n]
@rnd_upper[n]           → @string.random_upper[n]
@rnd_digits[n]          → @string.random_digits_str[n]

struct:
@pack[fmt; ...]         → @struct.pack[fmt; ...]
@struct_unpack[fmt; d]  → @struct.unpack[fmt; d]
@unpack_list[fmt; data] → @struct.unpack_list[fmt; data]
@calcsize[fmt]          → @struct.calcsize[fmt]
@struct_hex[fmt; ...]   → @struct.to_hex[fmt; ...]
@struct_pad[n]          → @struct.pad[n]

zlib:
@compress[data]         → @zlib.compress[data]
@decompress[data]       → @zlib.decompress[data]
@compress_b64[data]     → @zlib.compress_b64[data]
@decompress_b64[b64]    → @zlib.decompress_b64[b64]
@compress_str[s]        → @zlib.compress_str[s]
@decompress_str[s]      → @zlib.decompress_str[s]
@crc32[data]            → @zlib.crc32[data]
@adler32[data]          → @zlib.adler32[data]
@adler32_hex[data]      → @zlib.adler32_hex[data]

calendar:
@is_leap[year]          → @calendar.is_leap[year]
@days_in_month[y; m]    → @calendar.days_in_month[y; m]
@month_name_of[m]       → @calendar.month_name[m]
@day_name_of[w]         → @calendar.day_name[w]
@month_text[y; m]       → @calendar.month_text[y; m]
@is_weekday[y; m; d]    → @calendar.is_weekday[y; m; d]
@is_weekend[y; m; d]    → @calendar.is_weekend[y; m; d]
@day_of_year[y; m; d]   → @calendar.day_of_year[y; m; d]
@week_of_year[y; m; d]  → @calendar.week_of_year[y; m; d]
@quarter_of[month]      → @calendar.quarter[month]
@next_month[y; m]       → @calendar.next_month[y; m]
@prev_month[y; m]       → @calendar.prev_month[y; m]

email:
@email_make[s; f; t; b] → @email.make[s; f; t; b]
@email_parse[raw]       → @email.parse[raw]
@parse_address[s]       → @email.parse_address[s]
@valid_email[s]         → @email.valid_address[s]
@email_body[msg]        → @email.body[msg]
@email_html[msg]        → @email.html_body[msg]
@email_bytes[msg]       → @email.to_bytes[msg]
@email_attachments[msg] → @email.all_attachments[msg]
@addr_list[s]           → @email.address_list[s]

Namespace method aliases
─────────────────────────
@string.letters[]       → @string.ascii_letters[]
@string.lower[]         → @string.ascii_lowercase[]
@string.upper[]         → @string.ascii_uppercase[]
@string.tmpl[tpl]       → @string.template[tpl]
@string.sub[tpl; m]     → @string.substitute[tpl; m]
@string.rnd_lower[n]    → @string.random_lower[n]
@string.rnd_upper[n]    → @string.random_upper[n]
@string.rnd_digits[n]   → @string.random_digits_str[n]
@string.chars[s; cs]    → @string.filter[s; cs]
@string.no_chars[s; cs] → @string.exclude[s; cs]
@struct.size[fmt]       → @struct.calcsize[fmt]
@struct.from_bytes[f;d] → @struct.unpack[f; d]
@struct.to_bytes[f; v]  → @struct.pack[f; v]
@struct.list[f; d]      → @struct.unpack_list[f; d]
@struct.hex[f; v]       → @struct.to_hex[f; v]
@zlib.deflate[d]        → @zlib.compress[d]
@zlib.inflate[d]        → @zlib.decompress[d]
@zlib.b64[d]            → @zlib.compress_b64[d]
@zlib.str_c[s]          → @zlib.compress_str[s]
@zlib.str_d[s]          → @zlib.decompress_str[s]
@calendar.leap[y]       → @calendar.is_leap[y]
@calendar.mdays[y; m]   → @calendar.days_in_month[y; m]
@calendar.wkday[y;m;d]  → @calendar.is_weekday[y;m;d]
@calendar.wkend[y;m;d]  → @calendar.is_weekend[y;m;d]
@calendar.q[m]          → @calendar.quarter[m]
@calendar.doy[y;m;d]    → @calendar.day_of_year[y;m;d]
@calendar.woy[y;m;d]    → @calendar.week_of_year[y;m;d]
@email.msg[]            → @email.message[]
@email.from_string[r]   → @email.parse[r]
@email.html[m]          → @email.html_body[m]
@email.bytes[m]         → @email.to_bytes[m]
@email.attachments[m]   → @email.all_attachments[m]

New methods (via api.lib_call)
───────────────────────────────
@string.random[n]           → random alphanumeric string of length n
@string.random[n; charset]  → random string from a custom charset
@string.is_in[s; charset]   → True if every char of s is in charset
@string.only[s; charset]    → keep only chars from charset
@struct.hexdump[data]       → space-separated hex string of bytes
@struct.from_hex[hex]       → bytes from a hex string
@zlib.compress_ratio[data]  → ratio of compressed-to-original size (float)
@email.quick[to; subj; body]→ minimal EmailMessage with sensible defaults
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    # string — constants
    "@ascii_letters[":   "@string.ascii_letters[",
    "@ascii_lower[":     "@string.ascii_lowercase[",
    "@ascii_upper[":     "@string.ascii_uppercase[",
    "@digits[":          "@string.digits[",
    "@punctuation[":     "@string.punctuation[",
    "@whitespace[":      "@string.whitespace[",
    "@printable[":       "@string.printable[",
    "@capwords[":        "@string.capwords[",
    "@str_template[":    "@string.template[",
    "@substitute[":      "@string.substitute[",
    # string — new core methods
    "@ascii_to_int[":    "@string.ascii_to_int[",
    "@int_to_ascii[":    "@string.int_to_ascii[",
    "@str_filter[":      "@string.filter[",
    "@str_exclude[":     "@string.exclude[",
    "@rnd_lower[":       "@string.random_lower[",
    "@rnd_upper[":       "@string.random_upper[",
    "@rnd_digits[":      "@string.random_digits_str[",
    # struct
    "@pack[":            "@struct.pack[",
    "@struct_unpack[":   "@struct.unpack[",
    "@unpack_list[":     "@struct.unpack_list[",
    "@calcsize[":        "@struct.calcsize[",
    "@struct_hex[":      "@struct.to_hex[",
    "@struct_pad[":      "@struct.pad[",
    # zlib
    "@compress[":        "@zlib.compress[",
    "@decompress[":      "@zlib.decompress[",
    "@compress_b64[":    "@zlib.compress_b64[",
    "@decompress_b64[":  "@zlib.decompress_b64[",
    "@compress_str[":    "@zlib.compress_str[",
    "@decompress_str[":  "@zlib.decompress_str[",
    "@crc32[":           "@zlib.crc32[",
    "@adler32[":         "@zlib.adler32[",
    "@adler32_hex[":     "@zlib.adler32_hex[",
    # calendar
    "@is_leap[":         "@calendar.is_leap[",
    "@days_in_month[":   "@calendar.days_in_month[",
    "@month_name_of[":   "@calendar.month_name[",
    "@day_name_of[":     "@calendar.day_name[",
    "@month_text[":      "@calendar.month_text[",
    "@is_weekday[":      "@calendar.is_weekday[",
    "@is_weekend[":      "@calendar.is_weekend[",
    "@day_of_year[":     "@calendar.day_of_year[",
    "@week_of_year[":    "@calendar.week_of_year[",
    "@quarter_of[":      "@calendar.quarter[",
    "@next_month[":      "@calendar.next_month[",
    "@prev_month[":      "@calendar.prev_month[",
    # email
    "@email_make[":      "@email.make[",
    "@email_parse[":     "@email.parse[",
    "@parse_address[":   "@email.parse_address[",
    "@valid_email[":     "@email.valid_address[",
    "@email_body[":      "@email.body[",
    "@email_html[":      "@email.html_body[",
    "@email_bytes[":     "@email.to_bytes[",
    "@email_attachments[":"@email.all_attachments[",
    "@addr_list[":       "@email.address_list[",
}

METHOD_ALIASES: dict[str, str] = {
    "@string.letters[":    "@string.ascii_letters[",
    "@string.lower[":      "@string.ascii_lowercase[",
    "@string.upper[":      "@string.ascii_uppercase[",
    "@string.tmpl[":       "@string.template[",
    "@string.sub[":        "@string.substitute[",
    "@string.rnd_lower[":  "@string.random_lower[",
    "@string.rnd_upper[":  "@string.random_upper[",
    "@string.rnd_digits[": "@string.random_digits_str[",
    "@string.chars[":      "@string.filter[",
    "@string.no_chars[":   "@string.exclude[",
    "@struct.size[":       "@struct.calcsize[",
    "@struct.from_bytes[": "@struct.unpack[",
    "@struct.to_bytes[":   "@struct.pack[",
    "@struct.list[":       "@struct.unpack_list[",
    "@struct.hex[":        "@struct.to_hex[",
    "@zlib.deflate[":      "@zlib.compress[",
    "@zlib.inflate[":      "@zlib.decompress[",
    "@zlib.b64[":          "@zlib.compress_b64[",
    "@zlib.str_c[":        "@zlib.compress_str[",
    "@zlib.str_d[":        "@zlib.decompress_str[",
    "@calendar.leap[":     "@calendar.is_leap[",
    "@calendar.mdays[":    "@calendar.days_in_month[",
    "@calendar.wkday[":    "@calendar.is_weekday[",
    "@calendar.wkend[":    "@calendar.is_weekend[",
    "@calendar.q[":        "@calendar.quarter[",
    "@calendar.doy[":      "@calendar.day_of_year[",
    "@calendar.woy[":      "@calendar.week_of_year[",
    "@email.msg[":         "@email.message[",
    "@email.from_string[": "@email.parse[",
    "@email.html[":        "@email.html_body[",
    "@email.bytes[":       "@email.to_bytes[",
    "@email.attachments[": "@email.all_attachments[",
}

_RN  = "__import__('random')"
_STR = "__import__('string')"
_EM  = "__import__('email.message', fromlist=['EmailMessage'])"


def _new_lib_calls(api) -> None:

    # ── string ────────────────────────────────────────────────
    api.lib_call("string", "random", lambda a: (
        f"''.join({_RN}.choices({a[1]}, k=int({a[0]})))"
        if len(a) > 1 else
        f"''.join({_RN}.choices({_STR}.ascii_letters + {_STR}.digits, k=int({a[0]})))"
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
