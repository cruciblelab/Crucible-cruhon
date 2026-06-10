"""
Text / string stdlib wrappers for Cruhon — @text.*

Covers re / str / textwrap / html so a non-coder can do every common text
operation without knowing regex syntax or method names.

━━━ CASE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @text.upper[s]             → "HELLO"
  @text.lower[s]             → "hello"
  @text.title[s]             → "Hello World"
  @text.capitalize[s]        → "Hello world"
  @text.swapcase[s]          → "hELLO"

━━━ WHITESPACE / TRIM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @text.strip[s]             → strip both ends
  @text.lstrip[s]            → strip left
  @text.rstrip[s]            → strip right
  @text.strip[s; chars]      → strip specific chars

━━━ SEARCH / TEST ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @text.contains[s; sub]     → bool
  @text.startswith[s; pre]   → bool
  @text.endswith[s; suf]     → bool
  @text.count[s; sub]        → occurrences
  @text.index[s; sub]        → first position (-1 if not found)
  @text.is_digit[s]          → bool
  @text.is_alpha[s]          → bool
  @text.is_alnum[s]          → bool
  @text.is_space[s]          → bool
  @text.is_upper[s]          → bool
  @text.is_lower[s]          → bool

━━━ SPLIT / JOIN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @text.split[s]             → split on whitespace
  @text.split[s; sep]        → split on sep
  @text.split[s; sep; n]     → split max n times
  @text.join[sep; items]     → sep.join(items)
  @text.lines[s]             → splitlines()
  @text.words[s]             → split on whitespace, filter empty

━━━ REPLACE / FORMAT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @text.replace[s; old; new]             → str.replace
  @text.replace[s; old; new; n]         → replace max n times
  @text.format[template; *args/kwargs]  → str.format_map / .format
  @text.template[s; dict]               → str.format_map(dict)
  @text.repeat[s; n]                    → s * n
  @text.reverse[s]                      → s[::-1]

━━━ SLICE / SIZE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @text.len[s]               → len
  @text.slice[s; start]      → s[start:]
  @text.slice[s; start; end] → s[start:end]
  @text.truncate[s; n]       → truncate to n chars, append "…"
  @text.truncate[s; n; suf]  → custom suffix

━━━ PAD / ALIGN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @text.pad_left[s; width]           → right-justify (pad left with spaces)
  @text.pad_left[s; width; char]     → pad with char
  @text.pad_right[s; width]          → left-justify
  @text.pad_right[s; width; char]
  @text.center[s; width]
  @text.center[s; width; char]
  @text.zfill[s; width]              → zero-pad numbers

━━━ WRAP / INDENT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @text.wrap[s; width]       → list of lines (default 70)
  @text.fill[s; width]       → single wrapped string
  @text.indent[s; prefix]    → add prefix to every line
  @text.dedent[s]            → remove common leading whitespace

━━━ REGEX ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @text.match[pattern; s]          → bool (anchored at start)
  @text.search[pattern; s]         → bool (anywhere)
  @text.find[pattern; s]           → first match string or None
  @text.findall[pattern; s]        → list of all matches
  @text.sub[pattern; new; s]       → re.sub
  @text.sub[pattern; new; s; n]    → replace max n times
  @text.split_re[pattern; s]       → re.split
  @text.groups[pattern; s]         → capture groups of first match

━━━ HTML ESCAPE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @text.escape_html[s]       → & → &amp; etc.
  @text.unescape_html[s]     → reverse

━━━ SLUG / CLEAN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @text.slug[s]              → "Hello World!" → "hello-world"
  @text.clean[s]             → collapse whitespace to single spaces, strip
  @text.remove_digits[s]     → remove all digit characters
  @text.remove_punct[s]      → remove punctuation
  @text.only_digits[s]       → keep only digit characters
"""
from ..registry import register_lib, register_lib_call

_RE = "__import__('re')"
_TW = "__import__('textwrap')"
_HL = "__import__('html')"


def register():
    register_lib("text", None)   # no single Python module to import

    # ── CASE ─────────────────────────────────────────────────
    register_lib_call("text", "upper",      lambda a: f"str({a[0]}).upper()")
    register_lib_call("text", "lower",      lambda a: f"str({a[0]}).lower()")
    register_lib_call("text", "title",      lambda a: f"str({a[0]}).title()")
    register_lib_call("text", "capitalize", lambda a: f"str({a[0]}).capitalize()")
    register_lib_call("text", "swapcase",   lambda a: f"str({a[0]}).swapcase()")

    # ── WHITESPACE / TRIM ────────────────────────────────────
    register_lib_call("text", "strip",
        lambda a: f"str({a[0]}).strip({a[1] if len(a)>1 else ''})")
    register_lib_call("text", "lstrip",
        lambda a: f"str({a[0]}).lstrip({a[1] if len(a)>1 else ''})")
    register_lib_call("text", "rstrip",
        lambda a: f"str({a[0]}).rstrip({a[1] if len(a)>1 else ''})")

    # ── SEARCH / TEST ────────────────────────────────────────
    register_lib_call("text", "contains",
        lambda a: f"({a[1]} in str({a[0]}))")
    register_lib_call("text", "startswith",
        lambda a: f"str({a[0]}).startswith({a[1]})")
    register_lib_call("text", "endswith",
        lambda a: f"str({a[0]}).endswith({a[1]})")
    register_lib_call("text", "count",
        lambda a: f"str({a[0]}).count({a[1]})")
    register_lib_call("text", "index",
        lambda a: f"(str({a[0]}).find({a[1]}))")
    register_lib_call("text", "is_digit",   lambda a: f"str({a[0]}).isdigit()")
    register_lib_call("text", "is_alpha",   lambda a: f"str({a[0]}).isalpha()")
    register_lib_call("text", "is_alnum",   lambda a: f"str({a[0]}).isalnum()")
    register_lib_call("text", "is_space",   lambda a: f"str({a[0]}).isspace()")
    register_lib_call("text", "is_upper",   lambda a: f"str({a[0]}).isupper()")
    register_lib_call("text", "is_lower",   lambda a: f"str({a[0]}).islower()")

    # ── SPLIT / JOIN ─────────────────────────────────────────
    register_lib_call("text", "split",
        lambda a: (
            f"str({a[0]}).split({a[1]}, {a[2]})" if len(a) > 2 else
            f"str({a[0]}).split({a[1]})"          if len(a) > 1 else
            f"str({a[0]}).split()"
        ))
    register_lib_call("text", "join",
        lambda a: f"str({a[0]}).join(str(_i) for _i in {a[1]})")
    register_lib_call("text", "lines",
        lambda a: f"str({a[0]}).splitlines()")
    register_lib_call("text", "words",
        lambda a: f"[_w for _w in str({a[0]}).split() if _w]")

    # ── REPLACE / FORMAT ─────────────────────────────────────
    register_lib_call("text", "replace",
        lambda a: (
            f"str({a[0]}).replace({a[1]}, {a[2]}, {a[3]})" if len(a) > 3 else
            f"str({a[0]}).replace({a[1]}, {a[2]})"
        ))
    register_lib_call("text", "format",
        lambda a: f"str({a[0]}).format(*{a[1:]})" if len(a) > 1 else f"str({a[0]})")
    register_lib_call("text", "template",
        lambda a: f"str({a[0]}).format_map({a[1]})")
    register_lib_call("text", "repeat",
        lambda a: f"(str({a[0]}) * int({a[1]}))")
    register_lib_call("text", "reverse",
        lambda a: f"str({a[0]})[::-1]")

    # ── SLICE / SIZE ─────────────────────────────────────────
    register_lib_call("text", "len",
        lambda a: f"len(str({a[0]}))")
    register_lib_call("text", "slice",
        lambda a: (
            f"str({a[0]})[{a[1]}:{a[2]}]" if len(a) > 2 else
            f"str({a[0]})[{a[1]}:]"
        ))
    register_lib_call("text", "truncate",
        lambda a: (
            f"(str({a[0]})[:{a[1]}] + {a[2]} if len(str({a[0]})) > int({a[1]}) else str({a[0]}))"
            if len(a) > 2 else
            f"(str({a[0]})[:{a[1]}] + '…' if len(str({a[0]})) > int({a[1]}) else str({a[0]}))"
        ))

    # ── PAD / ALIGN ──────────────────────────────────────────
    register_lib_call("text", "pad_left",
        lambda a: f"str({a[0]}).rjust(int({a[1]}), {a[2] if len(a)>2 else repr(' ')})")
    register_lib_call("text", "pad_right",
        lambda a: f"str({a[0]}).ljust(int({a[1]}), {a[2] if len(a)>2 else repr(' ')})")
    register_lib_call("text", "center",
        lambda a: f"str({a[0]}).center(int({a[1]}), {a[2] if len(a)>2 else repr(' ')})")
    register_lib_call("text", "zfill",
        lambda a: f"str({a[0]}).zfill(int({a[1]}))")

    # ── WRAP / INDENT ────────────────────────────────────────
    register_lib_call("text", "wrap",
        lambda a: f"{_TW}.wrap(str({a[0]}), {a[1] if len(a)>1 else 70})")
    register_lib_call("text", "fill",
        lambda a: f"{_TW}.fill(str({a[0]}), {a[1] if len(a)>1 else 70})")
    register_lib_call("text", "indent",
        lambda a: f"{_TW}.indent(str({a[0]}), {a[1] if len(a)>1 else repr('  ')})")
    register_lib_call("text", "dedent",
        lambda a: f"{_TW}.dedent(str({a[0]}))")

    # ── REGEX ────────────────────────────────────────────────
    register_lib_call("text", "match",
        lambda a: f"bool({_RE}.match({a[0]}, str({a[1]})))")
    register_lib_call("text", "search",
        lambda a: f"bool({_RE}.search({a[0]}, str({a[1]})))")
    register_lib_call("text", "find",
        lambda a: f"(_m.group(0) if (_m := {_RE}.search({a[0]}, str({a[1]}))) else None)")
    register_lib_call("text", "findall",
        lambda a: f"{_RE}.findall({a[0]}, str({a[1]}))")
    register_lib_call("text", "sub",
        lambda a: (
            f"{_RE}.sub({a[0]}, {a[1]}, str({a[2]}), count={a[3]})" if len(a) > 3 else
            f"{_RE}.sub({a[0]}, {a[1]}, str({a[2]}))"
        ))
    register_lib_call("text", "split_re",
        lambda a: f"{_RE}.split({a[0]}, str({a[1]}))")
    register_lib_call("text", "groups",
        lambda a: f"(list({_RE}.search({a[0]}, str({a[1]})).groups()) if {_RE}.search({a[0]}, str({a[1]})) else [])")

    # ── HTML ESCAPE ──────────────────────────────────────────
    register_lib_call("text", "escape_html",
        lambda a: f"{_HL}.escape(str({a[0]}))")
    register_lib_call("text", "unescape_html",
        lambda a: f"{_HL}.unescape(str({a[0]}))")

    # ── SLUG / CLEAN ─────────────────────────────────────────
    register_lib_call("text", "slug",
        lambda a: (
            f"{_RE}.sub(r'[^a-z0-9]+', '-', "
            f"{_RE}.sub(r'[^\\w\\s-]', '', str({a[0]}).lower()).strip()).strip('-')"
        ))
    register_lib_call("text", "clean",
        lambda a: f"' '.join(str({a[0]}).split())")
    register_lib_call("text", "remove_digits",
        lambda a: f"{_RE}.sub(r'\\d', '', str({a[0]}))")
    register_lib_call("text", "remove_punct",
        lambda a: (
            f"{_RE}.sub(r'[^\\w\\s]', '', str({a[0]}))"
        ))
    register_lib_call("text", "only_digits",
        lambda a: f"{_RE}.sub(r'\\D', '', str({a[0]}))")
