"""
Text & sequence diffing for Cruhon — @diff.*

Wraps Python's `difflib`: similarity ratios, unified/context diffs,
fuzzy matching, and line-by-line comparison. No `@import` needed.

━━━ SIMILARITY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @diff.ratio[a; b]            → similarity ratio 0.0–1.0
  @diff.quick_ratio[a; b]      → faster upper-bound similarity estimate
  @diff.is_similar[a; b]       → True if ratio >= 0.6 (default cutoff)
  @diff.is_similar[a; b; cut]  → True if ratio >= cut

━━━ DIFFS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @diff.unified[a; b]          → unified-diff lines (strings split on '\\n')
  @diff.context[a; b]          → context-diff lines
  @diff.ndiff[a; b]            → ndiff lines (with +/-/? markers)
  @diff.lines[a; b]            → only the changed (+/-) lines

━━━ FUZZY MATCH ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @diff.close_matches[word; options]      → up to 3 closest matches
  @diff.close_matches[word; options; n]   → up to n closest matches
  @diff.best_match[word; options]         → single best match, or None
"""
from ..registry import register_lib, register_lib_call

_DL = "__import__('difflib')"


def _lines(expr: str) -> str:
    """Coerce a str (split on newlines) or a list into a list of lines."""
    return f"({expr}.splitlines(keepends=True) if isinstance({expr}, str) else list({expr}))"


def register():
    register_lib("diff", "difflib")

    # ── SIMILARITY ────────────────────────────────────────────
    register_lib_call("diff", "ratio",
        lambda a: f"{_DL}.SequenceMatcher(None, {a[0]}, {a[1]}).ratio()" if len(a) > 1 else "0.0")

    register_lib_call("diff", "quick_ratio",
        lambda a: f"{_DL}.SequenceMatcher(None, {a[0]}, {a[1]}).quick_ratio()" if len(a) > 1 else "0.0")

    register_lib_call("diff", "is_similar",
        lambda a: (
            f"({_DL}.SequenceMatcher(None, {a[0]}, {a[1]}).ratio() >= {a[2]})"
            if len(a) > 2 else
            f"({_DL}.SequenceMatcher(None, {a[0]}, {a[1]}).ratio() >= 0.6)"
            if len(a) > 1 else "False"
        ))

    # ── DIFFS ─────────────────────────────────────────────────
    register_lib_call("diff", "unified",
        lambda a: f"list({_DL}.unified_diff({_lines(a[0])}, {_lines(a[1])}))" if len(a) > 1 else "[]")

    register_lib_call("diff", "context",
        lambda a: f"list({_DL}.context_diff({_lines(a[0])}, {_lines(a[1])}))" if len(a) > 1 else "[]")

    register_lib_call("diff", "ndiff",
        lambda a: f"list({_DL}.ndiff({_lines(a[0])}, {_lines(a[1])}))" if len(a) > 1 else "[]")

    register_lib_call("diff", "lines",
        lambda a: (
            f"[_l for _l in {_DL}.ndiff({_lines(a[0])}, {_lines(a[1])}) "
            f"if _l and _l[0] in '+-']"
            if len(a) > 1 else "[]"
        ))

    # ── FUZZY MATCH ───────────────────────────────────────────
    register_lib_call("diff", "close_matches",
        lambda a: (
            f"{_DL}.get_close_matches({a[0]}, {a[1]}, n={a[2]})"
            if len(a) > 2 else
            f"{_DL}.get_close_matches({a[0]}, {a[1]})"
            if len(a) > 1 else "[]"
        ))

    register_lib_call("diff", "best_match",
        lambda a: (
            f"(lambda _m: _m[0] if _m else None)({_DL}.get_close_matches({a[0]}, {a[1]}, n=1))"
            if len(a) > 1 else "None"
        ))
