"""
Document validation — parse + transpile the document and convert errors to LSP Diagnostics.
"""
from __future__ import annotations
import re
from lsprotocol import types


def _line_col_to_range(source: str, line: int) -> types.Range:
    lines = source.splitlines()
    row = max(0, line - 1)
    end_col = len(lines[row]) if row < len(lines) else 0
    return types.Range(
        start=types.Position(line=row, character=0),
        end=types.Position(line=row, character=end_col),
    )


def validate(source: str) -> list[types.Diagnostic]:
    diagnostics: list[types.Diagnostic] = []

    try:
        from cruhon.core import parse, transpile
        from cruhon.core.parser import ParseError
    except ImportError:
        return diagnostics

    # Parse
    try:
        ast = parse(source)
    except Exception as exc:
        line = getattr(exc, "line", 1) or 1
        diagnostics.append(types.Diagnostic(
            range=_line_col_to_range(source, line),
            message=_clean_message(str(exc)),
            severity=types.DiagnosticSeverity.Error,
            source="cruhon-lsp",
        ))
        return diagnostics

    # Transpile
    try:
        transpile(ast)
    except Exception as exc:
        line = getattr(exc, "line", 1) or 1
        diagnostics.append(types.Diagnostic(
            range=_line_col_to_range(source, line),
            message=_clean_message(str(exc)),
            severity=types.DiagnosticSeverity.Error,
            source="cruhon-lsp",
        ))

    # Lint-style warnings (non-blocking)
    diagnostics.extend(_lint_warnings(source))
    return diagnostics


def _clean_message(msg: str) -> str:
    prefixes = ("[ParseError]", "[TranspileError]", "[RunError]")
    for p in prefixes:
        if p in msg:
            msg = msg[msg.index(p) + len(p):].strip(" —\t")
    return msg


_LINE_PATTERN = re.compile(r"Line\s+(\d+)", re.IGNORECASE)

_LINT_MAX_LINE = 120
_LINT_MAX_NEST = 8

_BLOCK_OPENERS = {
    "if", "elif", "else", "for", "while", "func", "class", "try", "catch",
    "finally", "with", "match", "async", "module", "repeat", "foreach",
    "retry", "timeout", "macro", "template", "raw",
}


def _lint_warnings(source: str) -> list[types.Diagnostic]:
    diags: list[types.Diagnostic] = []
    lines = source.splitlines()
    depth = 0

    for i, raw_line in enumerate(lines):
        # Long lines
        if len(raw_line) > _LINT_MAX_LINE:
            diags.append(types.Diagnostic(
                range=types.Range(
                    start=types.Position(line=i, character=_LINT_MAX_LINE),
                    end=types.Position(line=i, character=len(raw_line)),
                ),
                message=f"Line too long ({len(raw_line)} > {_LINT_MAX_LINE} characters).",
                severity=types.DiagnosticSeverity.Warning,
                source="cruhon-lint",
            ))

        # Nesting depth
        stripped = raw_line.lstrip()
        cmd_match = re.match(r"@(\w+)", stripped)
        if cmd_match:
            cmd = cmd_match.group(1)
            if cmd in _BLOCK_OPENERS:
                depth += 1
                if depth > _LINT_MAX_NEST:
                    diags.append(types.Diagnostic(
                        range=types.Range(
                            start=types.Position(line=i, character=0),
                            end=types.Position(line=i, character=len(raw_line)),
                        ),
                        message=f"Nesting depth {depth} exceeds recommended maximum of {_LINT_MAX_NEST}.",
                        severity=types.DiagnosticSeverity.Hint,
                        source="cruhon-lint",
                    ))
            elif cmd == "end":
                depth = max(0, depth - 1)

    return diags
