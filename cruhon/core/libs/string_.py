"""
String constants & helpers for Cruhon — @string.*

Wraps Python's `string` module: character-class constants, the
`Template` class, capwords, character filtering, translation tables,
and random string generators. No `@import` needed.

━━━ CONSTANTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @string.ascii_letters[]     → "abc…xyzABC…XYZ"
  @string.ascii_lowercase[]   → "abcdefghijklmnopqrstuvwxyz"
  @string.ascii_uppercase[]   → "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
  @string.digits[]            → "0123456789"
  @string.hexdigits[]         → "0123456789abcdefABCDEF"
  @string.octdigits[]         → "01234567"
  @string.punctuation[]       → "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
  @string.whitespace[]        → " \\t\\n\\r\\x0b\\x0c"
  @string.printable[]         → digits + letters + punctuation + whitespace

━━━ TEMPLATE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @string.template[tpl]            → string.Template object
  @string.substitute[tpl; mapping] → Template(tpl).substitute(mapping)
  @string.safe_substitute[tpl; m]  → Template(tpl).safe_substitute(m)
  @string.formatter[]              → string.Formatter() object

━━━ HELPERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @string.capwords[s]          → capitalize each word ("hello world" → "Hello World")
  @string.capwords[s; sep]     → capwords with a custom separator

━━━ CHAR UTILITIES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @string.ascii_to_int[c]      → ord(c) — code point of character
  @string.int_to_ascii[n]      → chr(n) — character from code point
  @string.filter[s; chars]     → keep only chars in the given set
  @string.exclude[s; chars]    → remove chars found in the given set
  @string.count_in[s; chars]   → count chars that belong to the set
  @string.maketrans[from; to]  → str.maketrans(from, to) translation table
  @string.translate[s; fr; to] → s.translate(str.maketrans(from, to))

━━━ RANDOM STRING GENERATORS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @string.random_lower[n]      → n random lowercase letters
  @string.random_upper[n]      → n random uppercase letters
  @string.random_digits_str[n] → n random digit characters
"""
from ..registry import register_lib, register_lib_call

_S  = "__import__('string')"
_RN = "__import__('random')"


def register():
    register_lib("string", "string")

    # ── CONSTANTS ─────────────────────────────────────────────
    for _name in (
        "ascii_letters", "ascii_lowercase", "ascii_uppercase",
        "digits", "hexdigits", "octdigits",
        "punctuation", "whitespace", "printable",
    ):
        register_lib_call("string", _name,
            (lambda n: lambda a: f"{_S}.{n}")(_name))

    # ── TEMPLATE ──────────────────────────────────────────────
    register_lib_call("string", "template",
        lambda a: f"{_S}.Template({a[0]})")

    register_lib_call("string", "substitute",
        lambda a: (
            f"{_S}.Template({a[0]}).substitute({a[1]})"
            if len(a) > 1 else
            f"{_S}.Template({a[0]}).substitute()"
        ))

    register_lib_call("string", "safe_substitute",
        lambda a: (
            f"{_S}.Template({a[0]}).safe_substitute({a[1]})"
            if len(a) > 1 else
            f"{_S}.Template({a[0]}).safe_substitute()"
        ))

    register_lib_call("string", "formatter",
        lambda a: f"{_S}.Formatter()")

    # ── HELPERS ───────────────────────────────────────────────
    register_lib_call("string", "capwords",
        lambda a: (
            f"{_S}.capwords({a[0]}, {a[1]})"
            if len(a) > 1 else
            f"{_S}.capwords({a[0]})"
        ))

    # ── CHAR UTILITIES ────────────────────────────────────────
    register_lib_call("string", "ascii_to_int",
        lambda a: f"ord(str({a[0]})[0])" if a else "0")

    register_lib_call("string", "int_to_ascii",
        lambda a: f"chr(int({a[0]}))" if a else "'\\x00'")

    register_lib_call("string", "filter",
        lambda a: (
            f"''.join(_c for _c in str({a[0]}) if _c in {a[1]})"
            if len(a) > 1 else f"str({a[0]})"
        ))

    register_lib_call("string", "exclude",
        lambda a: (
            f"''.join(_c for _c in str({a[0]}) if _c not in {a[1]})"
            if len(a) > 1 else f"str({a[0]})"
        ))

    register_lib_call("string", "count_in",
        lambda a: (
            f"sum(1 for _c in str({a[0]}) if _c in {a[1]})"
            if len(a) > 1 else "0"
        ))

    register_lib_call("string", "maketrans",
        lambda a: (
            f"str.maketrans({a[0]}, {a[1]})"
            if len(a) > 1 else f"str.maketrans({a[0]}, '')"
        ))

    register_lib_call("string", "translate",
        lambda a: (
            f"str({a[0]}).translate(str.maketrans({a[1]}, {a[2]}))"
            if len(a) > 2 else f"str({a[0]})"
        ))

    # ── RANDOM STRING GENERATORS ──────────────────────────────
    register_lib_call("string", "random_lower",
        lambda a: (
            f"''.join({_RN}.choices({_S}.ascii_lowercase, k=int({a[0]})))"
            if a else
            f"''.join({_RN}.choices({_S}.ascii_lowercase, k=8))"
        ))

    register_lib_call("string", "random_upper",
        lambda a: (
            f"''.join({_RN}.choices({_S}.ascii_uppercase, k=int({a[0]})))"
            if a else
            f"''.join({_RN}.choices({_S}.ascii_uppercase, k=8))"
        ))

    register_lib_call("string", "random_digits_str",
        lambda a: (
            f"''.join({_RN}.choices({_S}.digits, k=int({a[0]})))"
            if a else
            f"''.join({_RN}.choices({_S}.digits, k=6))"
        ))
