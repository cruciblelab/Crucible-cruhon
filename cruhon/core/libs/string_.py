"""
String constants & helpers for Cruhon — @string.*

Wraps Python's `string` module: character-class constants, the
`Template` class, and `capwords`. No `@import` needed.

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

━━━ HELPERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @string.capwords[s]         → capitalize each word ("hello world" → "Hello World")
  @string.capwords[s; sep]    → capwords with a custom separator
"""
from ..registry import register_lib, register_lib_call

_S = "__import__('string')"


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

    # ── HELPERS ───────────────────────────────────────────────
    register_lib_call("string", "capwords",
        lambda a: (
            f"{_S}.capwords({a[0]}, {a[1]})"
            if len(a) > 1 else
            f"{_S}.capwords({a[0]})"
        ))
