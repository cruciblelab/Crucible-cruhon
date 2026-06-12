"""
Cruhon Language Server — provides completion, diagnostics, hover, and symbols
for .clpy files.

Run as:
    python -m cruhon_lsp
    python -m cruhon_lsp --tcp --port 2087
"""
from __future__ import annotations

import logging
import re
from lsprotocol import types
from pygls.lsp.server import LanguageServer

from .completions import (
    build_command_completions,
    build_namespace_completions,
    build_method_completions,
    get_command_docs,
    get_namespace_docs,
)
from .diagnostics import validate
from .symbols import extract_symbols

logger = logging.getLogger(__name__)

server = LanguageServer(
    "cruhon-language-server",
    "2.6.0",
    text_document_sync_kind=types.TextDocumentSyncKind.Full,
)

# Pre-built completions (lazy on first use)
_cmd_completions: list[types.CompletionItem] | None = None
_ns_completions: list[types.CompletionItem] | None = None


def _get_cmd_completions() -> list[types.CompletionItem]:
    global _cmd_completions
    if _cmd_completions is None:
        _cmd_completions = build_command_completions()
    return _cmd_completions


def _get_ns_completions() -> list[types.CompletionItem]:
    global _ns_completions
    if _ns_completions is None:
        _ns_completions = build_namespace_completions()
    return _ns_completions


# ── Diagnostics ──────────────────────────────────────────────────────────────

def _publish_diagnostics(ls: LanguageServer, uri: str, source: str) -> None:
    diags = validate(source)
    ls.text_document_publish_diagnostics(
        types.PublishDiagnosticsParams(uri=uri, diagnostics=diags)
    )


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: types.DidOpenTextDocumentParams) -> None:
    doc = params.text_document
    _publish_diagnostics(ls, doc.uri, doc.text)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: types.DidChangeTextDocumentParams) -> None:
    # Full sync — last change has the full text
    if params.content_changes:
        source = params.content_changes[-1].text
        _publish_diagnostics(ls, params.text_document.uri, source)


@server.feature(types.TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: LanguageServer, params: types.DidSaveTextDocumentParams) -> None:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    _publish_diagnostics(ls, params.text_document.uri, doc.source)


# ── Completion ───────────────────────────────────────────────────────────────

@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(trigger_characters=["@", "."]),
)
def completion(
    ls: LanguageServer, params: types.CompletionParams
) -> types.CompletionList | None:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    source = doc.source
    lines = source.splitlines()

    cursor_line = params.position.line
    cursor_col = params.position.character
    current_line = lines[cursor_line] if cursor_line < len(lines) else ""
    prefix = current_line[:cursor_col]

    # @namespace.  → method completions
    ns_match = re.search(r"@(\w+)\.$", prefix)
    if ns_match:
        namespace = ns_match.group(1)
        methods = build_method_completions(namespace)
        if methods:
            return types.CompletionList(is_incomplete=False, items=methods)

    # @  → commands + namespace names
    if re.search(r"@\w*$", prefix):
        items = _get_cmd_completions() + _get_ns_completions()
        return types.CompletionList(is_incomplete=False, items=items)

    return None


# ── Hover ────────────────────────────────────────────────────────────────────

@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(
    ls: LanguageServer, params: types.HoverParams
) -> types.Hover | None:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    source = doc.source
    lines = source.splitlines()

    cursor_line = params.position.line
    cursor_col = params.position.character
    line_text = lines[cursor_line] if cursor_line < len(lines) else ""

    # Find the @command or @namespace.method under the cursor
    # Scan backwards to find @
    at_pos = line_text.rfind("@", 0, cursor_col + 1)
    if at_pos < 0:
        return None

    after = line_text[at_pos + 1:]

    # @namespace.method
    ns_method_match = re.match(r"(\w+)\.(\w+)", after)
    if ns_method_match:
        ns, method = ns_method_match.group(1), ns_method_match.group(2)
        # Check cursor is within the token
        token_end = at_pos + 1 + ns_method_match.end()
        if cursor_col <= token_end:
            docs = get_namespace_docs(ns, method)
            if docs:
                return types.Hover(
                    contents=types.MarkupContent(
                        kind=types.MarkupKind.Markdown, value=docs
                    )
                )

    # @command
    cmd_match = re.match(r"(\w+)", after)
    if cmd_match:
        cmd = cmd_match.group(1)
        token_end = at_pos + 1 + cmd_match.end()
        if cursor_col <= token_end:
            # Try namespace first
            docs = get_namespace_docs(cmd)
            if not docs:
                docs = get_command_docs(cmd)
            if docs:
                return types.Hover(
                    contents=types.MarkupContent(
                        kind=types.MarkupKind.Markdown, value=docs
                    )
                )

    return None


# ── Document symbols ─────────────────────────────────────────────────────────

@server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(
    ls: LanguageServer, params: types.DocumentSymbolParams
) -> list[types.DocumentSymbol] | None:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return extract_symbols(doc.source)


# ── Definition (go-to) ───────────────────────────────────────────────────────

@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def definition(
    ls: LanguageServer, params: types.DefinitionParams
) -> types.Location | None:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    source = doc.source
    lines = source.splitlines()

    cursor_line = params.position.line
    cursor_col = params.position.character
    line_text = lines[cursor_line] if cursor_line < len(lines) else ""

    # Look for @call[name] → find @macro[name], @pipeline, @template definition
    call_match = re.search(r"@(?:call|apply|render)\s*\[\s*(\w+)", line_text)
    if not call_match or not (call_match.start(1) <= cursor_col <= call_match.end(1)):
        # Also check if cursor is on a word that might be a macro/pipeline/template name
        # Look for the word at the cursor position
        word_at_cursor = _word_at(line_text, cursor_col)
        if not word_at_cursor:
            return None
        target_name = word_at_cursor
    else:
        target_name = call_match.group(1)

    # Search the document for the definition
    def_patterns = [
        re.compile(rf"@macro\s*\[\s*{re.escape(target_name)}\b"),
        re.compile(rf"@pipeline\s*\[\s*{re.escape(target_name)}\b"),
        re.compile(rf"@template\s*\[\s*{re.escape(target_name)}\b"),
        re.compile(rf"@func\s*\[\s*{re.escape(target_name)}\b"),
    ]

    for i, src_line in enumerate(lines):
        for pattern in def_patterns:
            if pattern.search(src_line):
                pos = types.Position(line=i, character=0)
                return types.Location(
                    uri=params.text_document.uri,
                    range=types.Range(start=pos, end=pos),
                )

    return None


def _word_at(line: str, col: int) -> str | None:
    m = re.finditer(r"\b\w+\b", line)
    for match in m:
        if match.start() <= col <= match.end():
            return match.group()
    return None
