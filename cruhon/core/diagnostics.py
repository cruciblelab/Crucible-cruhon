"""
cruhon/core/diagnostics.py
==========================
Single source of truth for rich, readable diagnostics.

Cruhon aims to be MORE readable than Python when something goes wrong.
Where Python prints a flat traceback, Cruhon shows:

  - the error type and the Cruhon line it maps to
  - the source line with surrounding context
  - a caret (^^^) under the exact offending token
  - a plain-language hint
  - a "did you mean …?" suggestion when a name is misspelled

Everything is centralized here so the lexer, parser, transpiler, runner
and CLI all render the same way. Nothing in this module ever raises — a
diagnostic failure must never mask the original error.

Optional file logging
----------------------
A user can route Cruhon's own diagnostics to a file WITHOUT touching code,
just environment variables:

    CRUHON_LOG=cruhon.log         → write diagnostics to cruhon.log
    CRUHON_LOG=1                  → write to ./cruhon.log (default name)
    CRUHON_LOG_LEVEL=DEBUG        → ERROR | WARNING | INFO | DEBUG (default INFO)

At DEBUG the log also captures the source, the generated Python and the
line map for every run. This is separate from the @log.* library, which
is for a *script's own* application logging.
"""

from __future__ import annotations

import os
import sys
import time
import difflib
import re
from typing import Optional


# ─────────────────────────────────────────────────────────────
# COLOR — auto-disabled for files, pipes, or NO_COLOR
# ─────────────────────────────────────────────────────────────

_COLORS = {
    "red":    "\033[31m",
    "green":  "\033[32m",
    "yellow": "\033[33m",
    "blue":   "\033[34m",
    "cyan":   "\033[36m",
    "grey":   "\033[90m",
    "bold":   "\033[1m",
    "reset":  "\033[0m",
}


def color_enabled(stream=None) -> bool:
    """True if ANSI color should be emitted to the given stream."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("CRUHON_NO_COLOR"):
        return False
    stream = stream or sys.stderr
    try:
        return bool(stream.isatty())
    except Exception:
        return False


def c(text: str, name: str, enabled: bool = True) -> str:
    """Wrap text in an ANSI color when enabled."""
    if not enabled:
        return text
    return f"{_COLORS.get(name, '')}{text}{_COLORS['reset']}"


# ─────────────────────────────────────────────────────────────
# NAME SUGGESTIONS — "did you mean …?"
# ─────────────────────────────────────────────────────────────

# Python keywords / builtins that are valid bare identifiers, so we don't
# suggest them as if they were typos of each other.
_COMMON_BUILTINS = frozenset(
    "print len range int str float bool list dict set tuple sum min max abs "
    "sorted reversed enumerate zip map filter open input type isinstance "
    "True False None".split()
)


def collect_identifiers(source: str) -> set[str]:
    """Pull plausible variable / function names out of Cruhon source."""
    if not source:
        return set()
    names: set[str] = set()
    for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", source):
        tok = m.group(0)
        # Skip 1-char names, ALL-CAPS constants, and builtins — none of these
        # are useful "did you mean" targets for an undefined-name typo.
        if len(tok) > 1 and not tok.isupper() and tok not in _COMMON_BUILTINS:
            names.add(tok)
    return names


def suggest(name: str, candidates, n: int = 1, cutoff: float = 0.6) -> Optional[str]:
    """Return the closest candidate to `name`, or None if nothing is close."""
    if not name or not candidates:
        return None
    pool = [x for x in set(candidates) if x and x != name]
    if not pool:
        return None
    matches = difflib.get_close_matches(name, pool, n=n, cutoff=cutoff)
    return matches[0] if matches else None


# ─────────────────────────────────────────────────────────────
# SOURCE EXCERPT — context lines + caret
# ─────────────────────────────────────────────────────────────

def source_excerpt(
    source: str,
    line_no: int,
    col: Optional[int] = None,
    span: Optional[int] = None,
    context: int = 2,
    colored: bool = False,
) -> str:
    """
    Render a source excerpt around `line_no` (1-based) with a gutter and an
    optional caret under column `col` spanning `span` chars.

    Returns "" if the line cannot be located, so callers can append safely.
    """
    if not source or not line_no or line_no < 1:
        return ""
    lines = source.splitlines()
    if line_no > len(lines):
        return ""

    start = max(1, line_no - context)
    end = min(len(lines), line_no + context)
    gutter_w = len(str(end))

    out = []
    for n in range(start, end + 1):
        text = lines[n - 1]
        is_target = (n == line_no)
        arrow = "→" if is_target else " "
        gutter = str(n).rjust(gutter_w)
        if colored:
            arrow = c(arrow, "red") if is_target else arrow
            gutter = c(gutter, "grey")
            sep = c("│", "grey")
        else:
            sep = "│"
        out.append(f"   {arrow} {gutter} {sep} {text}")

        if is_target and col is not None and col >= 0:
            caret_len = max(1, span or 1)
            pad = " " * (3 + 1 + 1 + gutter_w + 1 + 1 + 1 + col)
            caret = "^" * caret_len
            if colored:
                caret = c(caret, "red")
            out.append(f"{pad}{caret}")

    return "\n".join(out)


# ─────────────────────────────────────────────────────────────
# RICH REPORT — the master renderer
# ─────────────────────────────────────────────────────────────

def render_report(
    *,
    error_type: str,
    message: str,
    filename: str = "<clpy>",
    line: Optional[int] = None,
    col: Optional[int] = None,
    span: Optional[int] = None,
    source: Optional[str] = None,
    hint: Optional[str] = None,
    suggestion: Optional[str] = None,
    colored: Optional[bool] = None,
) -> str:
    """
    Build the full multi-line diagnostic. Used for both terminal display
    and the diagnostic log file (with `colored=False`).
    """
    if colored is None:
        colored = color_enabled()

    loc = filename
    if line:
        loc += f":{line}"

    header = f"✗ {error_type}"
    if colored:
        header = c(header, "red")
        loc = c(loc, "cyan")

    parts = [f"{header}  {loc}"]

    if message:
        parts.append("")
        parts.append(f"  {message}")

    if source and line:
        excerpt = source_excerpt(source, line, col=col, span=span, colored=colored)
        if excerpt:
            parts.append("")
            parts.append(excerpt)

    if suggestion:
        s = f"  Did you mean '{suggestion}'?"
        parts.append("")
        parts.append(c(s, "yellow") if colored else s)

    if hint:
        h = f"  Hint: {hint}"
        parts.append("")
        parts.append(c(h, "grey") if colored else h)

    return "\n".join(parts)


def render_exception(exc: Exception, source: Optional[str] = None,
                     filename: str = "<clpy>", colored: Optional[bool] = None) -> str:
    """
    Render any Cruhon exception (or its cause) richly. Falls back to a plain
    one-liner if the exception carries no structured info.
    """
    line = getattr(exc, "line", None) or getattr(exc, "cruhon_line", None)
    col = getattr(exc, "col", None)
    span = getattr(exc, "span", None)
    hint = getattr(exc, "hint", None)
    suggestion = getattr(exc, "suggestion", None)
    etype = getattr(exc, "error_type", None) or type(exc).__name__
    msg = getattr(exc, "clean_message", None) or str(exc)

    return render_report(
        error_type=etype, message=msg, filename=filename, line=line,
        col=col, span=span, source=source, hint=hint, suggestion=suggestion,
        colored=colored,
    )


# ─────────────────────────────────────────────────────────────
# DIAGNOSTIC LOG — opt-in file logging of Cruhon's own internals
# ─────────────────────────────────────────────────────────────

_LEVELS = {"ERROR": 40, "WARNING": 30, "INFO": 20, "DEBUG": 10}


class DiagnosticLog:
    """
    Append-only diagnostic log. Inert unless CRUHON_LOG is set. Never raises.
    """

    def __init__(self):
        self._path: Optional[str] = None
        self._level = 20
        self._resolved = False

    # -- configuration ----------------------------------------

    def _resolve(self):
        if self._resolved:
            return
        self._resolved = True
        raw = os.environ.get("CRUHON_LOG")
        if not raw:
            return
        if raw in ("1", "true", "True", "on", "yes"):
            self._path = "cruhon.log"
        else:
            self._path = raw
        lvl = os.environ.get("CRUHON_LOG_LEVEL", "INFO").upper()
        self._level = _LEVELS.get(lvl, 20)

    def configure(self, path: Optional[str], level: str = "INFO"):
        """Programmatic / CLI override of the env configuration."""
        self._resolved = True
        self._path = path or None
        self._level = _LEVELS.get((level or "INFO").upper(), 20)

    @property
    def enabled(self) -> bool:
        self._resolve()
        return self._path is not None

    # -- writing ----------------------------------------------

    def _write(self, level_name: str, text: str):
        if not self.enabled:
            return
        if _LEVELS.get(level_name, 20) < self._level:
            return
        try:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] [{level_name}] {text}\n")
        except Exception:
            pass  # logging must never break a run

    def event(self, message: str, level: str = "INFO"):
        self._write(level.upper(), message)

    def debug(self, message: str):
        self._write("DEBUG", message)

    def warning(self, message: str):
        self._write("WARNING", message)

    def block(self, title: str, body: str, level: str = "DEBUG"):
        """Write a multi-line block (e.g. generated Python) at DEBUG."""
        if not self.enabled:
            return
        if _LEVELS.get(level.upper(), 10) < self._level:
            return
        indented = "\n".join(f"    {ln}" for ln in body.splitlines())
        self._write(level.upper(), f"{title}:\n{indented}")

    # -- run lifecycle ----------------------------------------

    def run_start(self, filename: str, source: str):
        if not self.enabled:
            return
        self._write("INFO", f"─── run start: {filename} ───")
        self.block("source", source, level="DEBUG")

    def run_ok(self, filename: str, python_code: str, elapsed_ms: float):
        if not self.enabled:
            return
        self.block("generated python", python_code, level="DEBUG")
        self._write("INFO", f"run ok: {filename} ({elapsed_ms:.1f} ms)")

    def run_error(self, filename: str, report: str, py_traceback: str = ""):
        if not self.enabled:
            return
        self._write("ERROR", f"run failed: {filename}")
        # plain (uncolored) report into the file
        self.block("diagnostic", report, level="ERROR")
        if py_traceback:
            self.block("python traceback", py_traceback, level="DEBUG")


# Process-wide singleton.
_diag_log = DiagnosticLog()


def get_diagnostic_log() -> DiagnosticLog:
    return _diag_log
