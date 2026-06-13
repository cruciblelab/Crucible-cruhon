"""
cruhon/core/libs/textwrap_.py
=============================
Text wrapping & filling for Cruhon — @textwrap.*

Wrap, fill, shorten, indent and dedent blocks of text without @raw.

━━━ WRAP / FILL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @textwrap.wrap[text]            → list of lines (width 70)
  @textwrap.wrap[text; width]     → list of lines at given width
  @textwrap.fill[text]            → single string with newlines (width 70)
  @textwrap.fill[text; width]     → filled at given width
  @textwrap.shorten[text; width]  → collapse + truncate with " [...]"

━━━ INDENT / DEDENT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @textwrap.indent[text; prefix]  → add prefix to every non-empty line
  @textwrap.dedent[text]          → remove common leading whitespace

━━━ HELPERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @textwrap.center[text; width]   → center each line in width
  @textwrap.truncate[text; n]     → cut to n chars, add "…" if longer
"""
from ..registry import register_lib, register_lib_call

_TW = "__import__('textwrap')"


def register():
    register_lib("textwrap", None)

    # ── Wrap / Fill ───────────────────────────────────────────
    register_lib_call("textwrap", "wrap",
        lambda a: (
            f"{_TW}.wrap({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_TW}.wrap({a[0]})"
        ))

    register_lib_call("textwrap", "fill",
        lambda a: (
            f"{_TW}.fill({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_TW}.fill({a[0]})"
        ))

    register_lib_call("textwrap", "shorten",
        lambda a: (
            f"{_TW}.shorten({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_TW}.shorten({a[0]}, 70)"
        ))

    # ── Indent / Dedent ───────────────────────────────────────
    register_lib_call("textwrap", "indent",
        lambda a: f"{_TW}.indent({a[0]}, {a[1]})")

    register_lib_call("textwrap", "dedent",
        lambda a: f"{_TW}.dedent({a[0]})")

    # ── Helpers ───────────────────────────────────────────────
    register_lib_call("textwrap", "center",
        lambda a: (
            f"(lambda _t, _w: '\\n'.join(_l.center(_w) for _l in _t.splitlines()))({a[0]}, {a[1]})"
        ))

    register_lib_call("textwrap", "truncate",
        lambda a: (
            f"(lambda _t, _n: _t if len(_t) <= _n else _t[:_n] + '\\u2026')({a[0]}, {a[1]})"
        ))
