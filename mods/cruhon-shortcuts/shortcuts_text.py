"""
cruhon-shortcuts — text group
==============================
Shortcuts for @text.* string operations.

Global aliases (source rewrites)
─────────────────────────────────
@upper[s]               → @text.upper[s]
@lower[s]               → @text.lower[s]
@title_case[s]          → @text.title[s]
@capitalize[s]          → @text.capitalize[s]
@swapcase[s]            → @text.swapcase[s]
@casefold[s]            → @text.casefold[s]
@trim[s]                → @text.strip[s]
@strip[s]               → @text.strip[s]
@lstrip[s]              → @text.lstrip[s]
@rstrip[s]              → @text.rstrip[s]
@contains_str[s; sub]   → @text.contains[s; sub]
@startswith[s; pre]     → @text.startswith[s; pre]
@endswith[s; suf]       → @text.endswith[s; suf]
@count_str[s; sub]      → @text.count[s; sub]
@index_str[s; sub]      → @text.index[s; sub]
@str_split[s]           → @text.split[s]
@str_join[sep; items]   → @text.join[sep; items]
@str_lines[s]           → @text.lines[s]
@str_words[s]           → @text.words[s]
@str_replace[s; o; n]   → @text.replace[s; o; n]
@str_format[tpl; ...]   → @text.format[tpl; ...]
@str_repeat[s; n]       → @text.repeat[s; n]
@str_reverse[s]         → @text.reverse[s]
@str_slug[s]            → @text.slug[s]
@regex[s; pat]          → @text.regex[s; pat]
@str_pad[s; w]          → @text.pad[s; w]
@str_encode[s; enc]     → @text.encode[s; enc]
@str_decode[b; enc]     → @text.decode[b; enc]

Namespace method aliases
─────────────────────────
@text.trim[s]           → @text.strip[s]
@text.fmt[tpl; ...]     → @text.format[tpl; ...]
@text.has[s; sub]       → @text.contains[s; sub]
@text.sub[s; pat; rep]  → @text.regex_replace[s; pat; rep]

New methods (via api.lib_call)
───────────────────────────────
@text.truncate[s; n]            → s[:n] with optional ellipsis
@text.truncate[s; n; ellipsis]  → s[:n] + "..."
@text.indent[s; n]              → prepend N spaces to each line
@text.indent[s; n; prefix]      → prepend prefix to each line
@text.dedent[s]                 → remove common leading whitespace
@text.center[s; width]          → center-align string
@text.ljust[s; width]           → left-justify (pad right)
@text.rjust[s; width]           → right-justify (pad left)
@text.zfill[s; width]           → zero-fill to width
@text.pad_left[s; w; ch]        → left-pad with character (default space)
@text.pad_right[s; w; ch]       → right-pad with character (default space)
@text.remove_prefix[s; pre]     → strip leading prefix
@text.remove_suffix[s; suf]     → strip trailing suffix
@text.count_words[s]            → number of whitespace-separated words
@text.count_lines[s]            → number of lines
@text.char_count[s]             → character count
@text.byte_size[s]              → byte length (UTF-8)
@text.is_blank[s]               → True if empty or only whitespace
@text.wrap[s; width]            → textwrap.fill
@text.shorten[s; width]         → textwrap.shorten
@text.csv_row[items]            → join list as CSV row (comma-separated, quoted)
@text.tsv_row[items]            → join list as TSV row (tab-separated)
@text.hex[s]                    → hex representation of string bytes
@text.from_hex[h]               → decode hex back to string
@text.regex_replace[s; pat; r]  → re.sub(pat, r, s)
@text.regex_find[s; pat]        → re.findall(pat, s)
@text.regex_split[s; pat]       → re.split(pat, s)
@text.regex_match[s; pat]       → bool — pattern matches
@text.strip_html[s]             → remove HTML tags from string
@text.nl2br[s]                  → replace newlines with <br>
@text.escape_html[s]            → HTML-escape special characters
@text.unescape_html[s]          → reverse HTML escape
@text.camel_to_snake[s]         → CamelCase → snake_case
@text.snake_to_camel[s]         → snake_case → CamelCase
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@upper[":         "@text.upper[",
    "@lower[":         "@text.lower[",
    "@title_case[":    "@text.title[",
    "@capitalize[":    "@text.capitalize[",
    "@swapcase[":      "@text.swapcase[",
    "@casefold[":      "@text.casefold[",
    "@trim[":          "@text.strip[",
    "@strip[":         "@text.strip[",
    "@lstrip[":        "@text.lstrip[",
    "@rstrip[":        "@text.rstrip[",
    "@contains_str[":  "@text.contains[",
    "@startswith[":    "@text.startswith[",
    "@endswith[":      "@text.endswith[",
    "@count_str[":     "@text.count[",
    "@index_str[":     "@text.index[",
    "@str_split[":     "@text.split[",
    "@str_join[":      "@text.join[",
    "@str_lines[":     "@text.lines[",
    "@str_words[":     "@text.words[",
    "@str_replace[":   "@text.replace[",
    "@str_format[":    "@text.format[",
    "@str_repeat[":    "@text.repeat[",
    "@str_reverse[":   "@text.reverse[",
    "@str_slug[":      "@text.slug[",
    "@regex[":         "@text.regex[",
    "@str_pad[":       "@text.pad[",
    "@str_encode[":    "@text.encode[",
    "@str_decode[":    "@text.decode[",
}

METHOD_ALIASES: dict[str, str] = {
    "@text.trim[":          "@text.strip[",
    "@text.fmt[":           "@text.format[",
    "@text.has[":           "@text.contains[",
}

_RE   = "__import__('re')"
_TW   = "__import__('textwrap')"
_HTML = "__import__('html')"


def _new_lib_calls(api) -> None:
    # Note: truncate, indent, dedent, wrap, sub, center, ljust, rjust, zfill,
    # pad_left, pad_right, escape_html, unescape_html already exist in
    # cruhon/core/libs/text_.py — do not re-register them here.

    api.lib_call("text", "remove_prefix", lambda a: (
        f"(str({a[0]})[len({a[1]}):] if str({a[0]}).startswith({a[1]}) else str({a[0]}))"
        if len(a) > 1 else
        f"str({a[0]})"
    ))

    api.lib_call("text", "remove_suffix", lambda a: (
        f"(str({a[0]})[:-len({a[1]})] if str({a[0]}).endswith({a[1]}) else str({a[0]}))"
        if len(a) > 1 else
        f"str({a[0]})"
    ))

    api.lib_call("text", "count_words", lambda a: (
        f"len(str({a[0]}).split())"
    ))

    api.lib_call("text", "count_lines", lambda a: (
        f"len(str({a[0]}).splitlines())"
    ))

    api.lib_call("text", "char_count", lambda a: (
        f"len(str({a[0]}))"
    ))

    api.lib_call("text", "byte_size", lambda a: (
        f"len(str({a[0]}).encode('utf-8'))"
    ))

    api.lib_call("text", "is_blank", lambda a: (
        f"(not str({a[0]}).strip())"
    ))

    # text.wrap already exists in core (returns list of lines — do not re-register)

    api.lib_call("text", "shorten", lambda a: (
        f"{_TW}.shorten(str({a[0]}), width={a[1]})"
        if len(a) > 1 else
        f"{_TW}.shorten(str({a[0]}), width=80)"
    ))

    api.lib_call("text", "csv_row", lambda a: (
        f"','.join({_RE}.sub(r'\"', '\"\"', str(item)) "
        f"if ',' in str(item) or '\"' in str(item) else str(item) "
        f"for item in {a[0]})"
        if a else
        f"''"
    ))

    api.lib_call("text", "tsv_row", lambda a: (
        f"'\\t'.join(str(x) for x in {a[0]})"
        if a else
        f"''"
    ))

    api.lib_call("text", "hex", lambda a: (
        f"str({a[0]}).encode('utf-8').hex()"
    ))

    api.lib_call("text", "from_hex", lambda a: (
        f"bytes.fromhex(str({a[0]})).decode('utf-8')"
    ))

    api.lib_call("text", "regex_replace", lambda a: (
        f"{_RE}.sub({a[1]}, {a[2]}, str({a[0]}))"
        if len(a) > 2 else
        f"str({a[0]})"
    ))

    api.lib_call("text", "regex_find", lambda a: (
        f"{_RE}.findall({a[1]}, str({a[0]}))"
        if len(a) > 1 else
        f"[]"
    ))

    api.lib_call("text", "regex_split", lambda a: (
        f"{_RE}.split({a[1]}, str({a[0]}))"
        if len(a) > 1 else
        f"str({a[0]}).split()"
    ))

    api.lib_call("text", "regex_match", lambda a: (
        f"bool({_RE}.search({a[1]}, str({a[0]})))"
        if len(a) > 1 else
        f"False"
    ))

    api.lib_call("text", "strip_html", lambda a: (
        f"{_RE}.sub(r'<[^>]+>', '', str({a[0]}))"
    ))

    api.lib_call("text", "nl2br", lambda a: (
        f"str({a[0]}).replace('\\n', '<br>')"
    ))

    # escape_html and unescape_html already exist in core text lib

    api.lib_call("text", "camel_to_snake", lambda a: (
        f"{_RE}.sub(r'([A-Z])', r'_\\1', str({a[0]})).lstrip('_').lower()"
    ))

    api.lib_call("text", "snake_to_camel", lambda a: (
        f"''.join(word.capitalize() for word in str({a[0]}).split('_'))"
    ))

    # text.sub already exists in core text lib — do not re-register


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
