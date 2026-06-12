"""
cruhon-shortcuts-pro — text group
=====================================
Extends @text.* with case conversion, word analysis, text normalization,
and formatting utilities.

Global aliases (source rewrites)
─────────────────────────────────
@camel_case[s]           → @text.camel_case[s]
@snake_case[s]           → @text.snake_case[s]
@kebab_case[s]           → @text.kebab_case[s]
@pascal_case[s]          → @text.pascal_case[s]
@word_freq[s]            → @text.word_freq[s]
@normalize_ws[s]         → @text.normalize_ws[s]
@excerpt[s; n]           → @text.excerpt[s; n]
@initials[s]             → @text.initials[s]
@squeeze[s; ch]          → @text.squeeze[s; ch]
@ordinal[n]              → @text.ordinal[n]
@pluralize[word; n]      → @text.pluralize[word; n]
@de_accent[s]            → @text.de_accent[s]
@wrap_lines[s; w]        → @text.wrap_lines[s; w]
@sentence_count[s]       → @text.sentence_count[s]
@char_freq[s]            → @text.char_freq[s]
@longest_word[s]         → @text.longest_word[s]
@shortest_word[s]        → @text.shortest_word[s]

Namespace method aliases
─────────────────────────
@text.camel[s]        → @text.camel_case[s]
@text.snake[s]        → @text.snake_case[s]
@text.kebab[s]        → @text.kebab_case[s]
@text.pascal[s]       → @text.pascal_case[s]
@text.wfreq[s]        → @text.word_freq[s]
@text.nws[s]          → @text.normalize_ws[s]
@text.xrpt[s; n]      → @text.excerpt[s; n]
@text.init[s]         → @text.initials[s]
@text.sqz[s; ch]      → @text.squeeze[s; ch]
@text.ord[n]          → @text.ordinal[n]

New methods (via api.lib_call)
───────────────────────────────
@text.camel_case[s]        → to camelCase from any separator style
@text.snake_case[s]        → to snake_case
@text.kebab_case[s]        → to kebab-case
@text.pascal_case[s]       → to PascalCase
@text.word_freq[s]         → {word: count} frequency dict
@text.normalize_ws[s]      → collapse all whitespace runs to single space
@text.excerpt[s; n]        → first n words, ending with "…" if truncated
@text.initials[s]          → first letter of each word, e.g. "John Doe" → "JD"
@text.squeeze[s; ch]       → collapse consecutive identical chars: squeeze("aaa","a") → "a"
@text.ordinal[n]           → "1st", "2nd", "3rd", "4th" …
@text.pluralize[word; n]   → word if n==1 else word+"s" (simple English rule)
@text.de_accent[s]         → remove accents (unicodedata NFKD decomposition)
@text.wrap_lines[s; width] → word-wrap to given width (textwrap.fill)
@text.sentence_count[s]    → count sentences (split on . ! ?)
@text.char_freq[s]         → {char: count} for all characters
@text.longest_word[s]      → longest word in string
@text.shortest_word[s]     → shortest word in string (non-empty)
@text.pad_center[s; n; ch] → center-pad string to width n with fill character ch
@text.mirror[s]            → reverse the string
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@camel_case[":      "@text.camel_case[",
    "@snake_case[":      "@text.snake_case[",
    "@kebab_case[":      "@text.kebab_case[",
    "@pascal_case[":     "@text.pascal_case[",
    "@word_freq[":       "@text.word_freq[",
    "@normalize_ws[":    "@text.normalize_ws[",
    "@excerpt[":         "@text.excerpt[",
    "@initials[":        "@text.initials[",
    "@squeeze[":         "@text.squeeze[",
    "@ordinal[":         "@text.ordinal[",
    "@pluralize[":       "@text.pluralize[",
    "@de_accent[":       "@text.de_accent[",
    "@wrap_lines[":      "@text.wrap_lines[",
    "@sentence_count[":  "@text.sentence_count[",
    "@char_freq[":       "@text.char_freq[",
    "@longest_word[":    "@text.longest_word[",
    "@shortest_word[":   "@text.shortest_word[",
}

METHOD_ALIASES: dict[str, str] = {
    "@text.camel[":   "@text.camel_case[",
    "@text.snake[":   "@text.snake_case[",
    "@text.kebab[":   "@text.kebab_case[",
    "@text.pascal[":  "@text.pascal_case[",
    "@text.wfreq[":   "@text.word_freq[",
    "@text.nws[":     "@text.normalize_ws[",
    "@text.xrpt[":    "@text.excerpt[",
    "@text.init[":    "@text.initials[",
    "@text.sqz[":     "@text.squeeze[",
    "@text.ord[":     "@text.ordinal[",
}

_RE = "__import__('re')"


def _new_lib_calls(api) -> None:

    api.lib_call("text", "camel_case", lambda a: (
        f"(lambda _s: _s[0].lower() + _s[1:] if _s else '')("
        f"''.join(_w.capitalize() for _w in "
        f"{_RE}.split(r'[\\s_\\-]+', str({a[0]})) if _w))"
        if a else "''"
    ))

    api.lib_call("text", "snake_case", lambda a: (
        f"{_RE}.sub(r'[\\s\\-]+', '_', "
        f"{_RE}.sub(r'([A-Z]+)([A-Z][a-z])', r'\\1_\\2', "
        f"{_RE}.sub(r'([a-z0-9])([A-Z])', r'\\1_\\2', str({a[0]})))).lower()"
        if a else "''"
    ))

    api.lib_call("text", "kebab_case", lambda a: (
        f"{_RE}.sub(r'[\\s_]+', '-', "
        f"{_RE}.sub(r'([A-Z]+)([A-Z][a-z])', r'\\1-\\2', "
        f"{_RE}.sub(r'([a-z0-9])([A-Z])', r'\\1-\\2', str({a[0]})))).lower()"
        if a else "''"
    ))

    api.lib_call("text", "pascal_case", lambda a: (
        f"''.join(_w.capitalize() for _w in "
        f"{_RE}.split(r'[\\s_\\-]+', str({a[0]})) if _w)"
        if a else "''"
    ))

    api.lib_call("text", "word_freq", lambda a: (
        f"(lambda _ws: dict(sorted("
        f"{{_w: _ws.count(_w) for _w in set(_ws)}}.items(), "
        f"key=lambda _kv: -_kv[1])))"
        f"({_RE}.findall(r'\\b\\w+\\b', str({a[0]}).lower()))"
        if a else "{}"
    ))

    api.lib_call("text", "normalize_ws", lambda a: (
        f"' '.join(str({a[0]}).split())"
        if a else "''"
    ))

    api.lib_call("text", "excerpt", lambda a: (
        f"(lambda _words, _n: ' '.join(_words[:_n]) + ('\\u2026' if len(_words) > _n else ''))"
        f"(str({a[0]}).split(), int({a[1]}))"
        if len(a) > 1 else
        f"str({a[0]})" if a else "''"
    ))

    api.lib_call("text", "initials", lambda a: (
        f"''.join(_w[0].upper() for _w in str({a[0]}).split() if _w)"
        if a else "''"
    ))

    api.lib_call("text", "squeeze", lambda a: (
        f"{_RE}.sub(r'(' + {_RE}.escape(str({a[1]})) + r')\\1+', r'\\1', str({a[0]}))"
        if len(a) > 1 else
        f"{_RE}.sub(r'(.)\\1+', r'\\1', str({a[0]}))" if a else "''"
    ))

    api.lib_call("text", "ordinal", lambda a: (
        f"(lambda _n: str(_n) + ('th' if 11 <= abs(_n) % 100 <= 13 else "
        f"{{1: 'st', 2: 'nd', 3: 'rd'}}.get(abs(_n) % 10, 'th')))(int({a[0]}))"
        if a else "'0th'"
    ))

    api.lib_call("text", "pluralize", lambda a: (
        f"(str({a[0]}) if int({a[1]}) == 1 else str({a[0]}) + 's')"
        if len(a) > 1 else
        f"str({a[0]}) + 's'" if a else "''"
    ))

    api.lib_call("text", "de_accent", lambda a: (
        f"''.join(_c for _c in "
        f"__import__('unicodedata').normalize('NFKD', str({a[0]})) "
        f"if __import__('unicodedata').category(_c) != 'Mn')"
        if a else "''"
    ))

    api.lib_call("text", "wrap_lines", lambda a: (
        f"__import__('textwrap').fill(str({a[0]}), width=int({a[1]}))"
        if len(a) > 1 else
        f"str({a[0]})" if a else "''"
    ))

    api.lib_call("text", "sentence_count", lambda a: (
        f"len([_s for _s in {_RE}.split(r'[.!?]+', str({a[0]})) if _s.strip()])"
        if a else "0"
    ))

    api.lib_call("text", "char_freq", lambda a: (
        f"(lambda _s: {{_c: _s.count(_c) for _c in set(_s)}})(str({a[0]}))"
        if a else "{}"
    ))

    api.lib_call("text", "longest_word", lambda a: (
        f"max({_RE}.findall(r'\\b\\w+\\b', str({a[0]})), key=len, default='')"
        if a else "''"
    ))

    api.lib_call("text", "shortest_word", lambda a: (
        f"min((_w for _w in {_RE}.findall(r'\\b\\w+\\b', str({a[0]})) if _w), "
        f"key=len, default='')"
        if a else "''"
    ))

    api.lib_call("text", "pad_center", lambda a: (
        f"str({a[0]}).center(int({a[1]}), str({a[2]}))"
        if len(a) > 2 else
        f"str({a[0]}).center(int({a[1]}))" if len(a) > 1 else
        f"str({a[0]})" if a else "''"
    ))

    api.lib_call("text", "mirror", lambda a: (
        f"str({a[0]})[::-1]" if a else "''"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
