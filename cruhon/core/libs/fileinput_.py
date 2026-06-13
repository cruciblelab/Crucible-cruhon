"""
cruhon/core/libs/fileinput_.py
==============================
Fileinput wrappers for Cruhon — @fileinput.*

File reading utilities beyond basic @file.read — multi-file iteration,
line numbering, grep, head/tail, word/char counting.

━━━ READ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @fileinput.lines[path]              → list of stripped lines
  @fileinput.lines_raw[path]          → list of lines (newlines preserved)
  @fileinput.lines_multi[paths]       → lines from a list of files, combined
  @fileinput.numbered[path]           → [(1, line), (2, line), ...]

━━━ SLICE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @fileinput.head[path; n]            → first n lines
  @fileinput.tail[path; n]            → last n lines
  @fileinput.slice[path; start; end]  → lines[start:end]

━━━ SEARCH ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @fileinput.grep[path; pattern]      → lines matching regex
  @fileinput.grep_n[path; pattern]    → [(lineno, line), ...] matching regex
  @fileinput.contains[path; text]     → bool: text appears in file

━━━ COUNT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @fileinput.count_lines[path]        → number of lines
  @fileinput.count_words[path]        → number of words
  @fileinput.count_chars[path]        → number of characters

━━━ TRANSFORM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @fileinput.replace[path; old; new]       → new content string (file unchanged)
  @fileinput.replace_save[path; old; new]  — replace in-place and save
  @fileinput.strip_empty[path]        → lines with content only (no blank lines)
  @fileinput.unique_lines[path]       → deduplicated lines (order preserved)
"""
from ..registry import register_lib, register_lib_call


def register():
    register_lib("fileinput", None)

    # ── Read ──────────────────────────────────────────────────
    register_lib_call("fileinput", "lines",
        lambda a: f"[_l.rstrip('\\n') for _l in open({a[0]}, encoding='utf-8')]")

    register_lib_call("fileinput", "lines_raw",
        lambda a: f"open({a[0]}, encoding='utf-8').readlines()")

    register_lib_call("fileinput", "lines_multi",
        lambda a: (
            f"[_l.rstrip('\\n') for _p in {a[0]} for _l in open(_p, encoding='utf-8')]"
        ))

    register_lib_call("fileinput", "numbered",
        lambda a: f"list(enumerate((_l.rstrip('\\n') for _l in open({a[0]}, encoding='utf-8')), 1))")

    # ── Slice ─────────────────────────────────────────────────
    register_lib_call("fileinput", "head",
        lambda a: (
            f"(lambda _p, _n: [_l.rstrip('\\n') for _l in open(_p, encoding='utf-8')][:int(_n)])({a[0]}, {a[1]})"
        ))

    register_lib_call("fileinput", "tail",
        lambda a: (
            f"(lambda _p, _n: [_l.rstrip('\\n') for _l in open(_p, encoding='utf-8')][-int(_n):])({a[0]}, {a[1]})"
        ))

    register_lib_call("fileinput", "slice",
        lambda a: (
            f"(lambda _p, _s, _e: [_l.rstrip('\\n') for _l in open(_p, encoding='utf-8')][int(_s):int(_e)])({a[0]}, {a[1]}, {a[2]})"
        ))

    # ── Search ────────────────────────────────────────────────
    register_lib_call("fileinput", "grep",
        lambda a: (
            f"(lambda _p, _pat: [_l.rstrip('\\n') for _l in open(_p, encoding='utf-8') if __import__('re').search(_pat, _l)])({a[0]}, {a[1]})"
        ))

    register_lib_call("fileinput", "grep_n",
        lambda a: (
            f"(lambda _p, _pat: [(_i, _l.rstrip('\\n')) for _i, _l in enumerate(open(_p, encoding='utf-8'), 1) if __import__('re').search(_pat, _l)])({a[0]}, {a[1]})"
        ))

    register_lib_call("fileinput", "contains",
        lambda a: f"({a[1]} in open({a[0]}, encoding='utf-8').read())")

    # ── Count ─────────────────────────────────────────────────
    register_lib_call("fileinput", "count_lines",
        lambda a: f"sum(1 for _ in open({a[0]}, encoding='utf-8'))")

    register_lib_call("fileinput", "count_words",
        lambda a: f"len(open({a[0]}, encoding='utf-8').read().split())")

    register_lib_call("fileinput", "count_chars",
        lambda a: f"len(open({a[0]}, encoding='utf-8').read())")

    # ── Transform ─────────────────────────────────────────────
    register_lib_call("fileinput", "replace",
        lambda a: f"open({a[0]}, encoding='utf-8').read().replace({a[1]}, {a[2]})")

    register_lib_call("fileinput", "replace_save",
        lambda a: (
            f"(lambda _p, _o, _n: (lambda _c: open(_p, 'w', encoding='utf-8').write(_c))("
            f"open(_p, encoding='utf-8').read().replace(_o, _n)))({a[0]}, {a[1]}, {a[2]})"
        ))

    register_lib_call("fileinput", "strip_empty",
        lambda a: f"[_l.rstrip('\\n') for _l in open({a[0]}, encoding='utf-8') if _l.strip()]")

    register_lib_call("fileinput", "unique_lines",
        lambda a: (
            f"(lambda _lines: list(dict.fromkeys(_lines)))([_l.rstrip('\\n') for _l in open({a[0]}, encoding='utf-8')])"
        ))
