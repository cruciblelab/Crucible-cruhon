"""
Extract document symbols (variables, functions, macros, templates, pipelines)
from a Cruhon source document.
"""
from __future__ import annotations
import re
from lsprotocol import types

_SYMBOL_PATTERNS: list[tuple[str, types.SymbolKind, re.Pattern]] = [
    ("var",      types.SymbolKind.Variable, re.compile(r"@var\s*\[\s*(\w+)\s*;")),
    ("const",    types.SymbolKind.Constant, re.compile(r"@const\s*\[\s*(\w+)\s*;")),
    ("func",     types.SymbolKind.Function, re.compile(r"@func\s*\[\s*(\w+)")),
    ("macro",    types.SymbolKind.Function, re.compile(r"@macro\s*\[\s*(\w+)")),
    ("class",    types.SymbolKind.Class,    re.compile(r"@class\s*\[\s*(\w+)")),
    ("template", types.SymbolKind.String,   re.compile(r"@template\s*\[\s*(\w+)")),
    ("pipeline", types.SymbolKind.Function, re.compile(r"@pipeline\s*\[\s*(\w+)")),
    ("module",   types.SymbolKind.Module,   re.compile(r"@module\s*\[\s*(\w+)")),
]


def extract_symbols(source: str) -> list[types.DocumentSymbol]:
    symbols: list[types.DocumentSymbol] = []
    lines = source.splitlines()

    for i, line in enumerate(lines):
        for _cmd, kind, pattern in _SYMBOL_PATTERNS:
            m = pattern.search(line)
            if m:
                name = m.group(1)
                pos = types.Position(line=i, character=m.start(1))
                end_pos = types.Position(line=i, character=m.end(1))
                rng = types.Range(start=pos, end=end_pos)
                symbols.append(types.DocumentSymbol(
                    name=name,
                    kind=kind,
                    range=rng,
                    selection_range=rng,
                ))

    return symbols
