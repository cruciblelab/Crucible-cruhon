"""
cruhon/core/lexer.py
====================
Source code (.clpy) → Token list

Token types:
  AT_CMD    → @print, @var, @if ...
  LBRACKET  → [
  RBRACKET  → ]
  SEMICOLON → ;
  STRING    → "text" or bare text
  NUMBER    → 42, 3.14
  INDENT    → indentation level
  NEWLINE   → end of line
  EOF       → end of file
  RAW       → raw Python expression (conditions, arithmetic)

Mods can add new token types via register_token_type().
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Optional


# ─────────────────────────────────────────────────────────────
# TOKEN
# ─────────────────────────────────────────────────────────────

# Core token types
TOKEN_TYPES = {
    "AT_CMD",
    "LBRACKET",
    "RBRACKET",
    "SEMICOLON",
    "STRING",
    "NUMBER",
    "BOOL",
    "INDENT",
    "DEDENT",
    "NEWLINE",
    "EOF",
    "RAW",
    "COMMENT",
    "NAMESPACE",   # @requests.get → namespace=requests, cmd=get
    "DOT",
}


def register_token_type(name: str):
    """Mod system: register a new token type."""
    TOKEN_TYPES.add(name)


@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int = 0

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"


# ─────────────────────────────────────────────────────────────
# LEXER
# ─────────────────────────────────────────────────────────────

class LexerError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(f"[LexerError] Line {line}:{col} — {msg}")
        self.line = line
        self.col = col


class Lexer:
    """
    Converts .clpy source code into a token list.

    Mod system:
      - register_token_type() for new token types
      - pre_hooks: source manipulation before tokenization
      - post_hooks: token list manipulation after tokenization
    """

    def __init__(self):
        self._pre_hooks: list = []   # (fn) -> transforms source str
        self._post_hooks: list = []  # (tokens) -> transforms tokens

    # ── Mod hooks ─────────────────────────────────────────────

    def add_pre_hook(self, fn):
        """Manipulate source code before tokenization."""
        self._pre_hooks.append(fn)

    def add_post_hook(self, fn):
        """Manipulate token list after tokenization."""
        self._post_hooks.append(fn)

    # ── Ana tokenize ──────────────────────────────────────────

    def tokenize(self, source: str) -> List[Token]:
        # Apply pre-hooks
        for hook in self._pre_hooks:
            source = hook(source)

        tokens = []
        lines = source.splitlines()
        indent_stack = [0]

        for line_num, line in enumerate(lines, start=1):
            # Empty line
            if not line.strip():
                tokens.append(Token("NEWLINE", "\n", line_num))
                continue

            # Comment line
            stripped = line.lstrip()
            if stripped.startswith("#"):
                tokens.append(Token("COMMENT", stripped[1:].strip(), line_num))
                tokens.append(Token("NEWLINE", "\n", line_num))
                continue

            # Girinti hesapla
            indent = len(line) - len(line.lstrip())
            current_indent = indent_stack[-1]

            if indent > current_indent:
                indent_stack.append(indent)
                tokens.append(Token("INDENT", str(indent), line_num))
            elif indent < current_indent:
                while indent_stack[-1] > indent:
                    indent_stack.pop()
                    tokens.append(Token("DEDENT", str(indent), line_num))
                if indent_stack[-1] != indent:
                    raise LexerError(
                        f"Indentation error (expected {indent_stack[-1]}, got {indent})",
                        line_num, 0
                    )

            # Tokenize line content
            line_tokens = self._tokenize_line(stripped, line_num)
            tokens.extend(line_tokens)
            tokens.append(Token("NEWLINE", "\n", line_num))

        # Close open indent blocks
        while len(indent_stack) > 1:
            indent_stack.pop()
            tokens.append(Token("DEDENT", "0", len(lines)))

        tokens.append(Token("EOF", "", len(lines)))

        # Apply post-hooks
        for hook in self._post_hooks:
            tokens = hook(tokens)

        return tokens

    def _tokenize_line(self, line: str, line_num: int) -> List[Token]:
        """Tokenize a single line."""
        tokens = []
        i = 0
        length = len(line)

        while i < length:
            # Skip whitespace
            if line[i] == " ":
                i += 1
                continue

            # @ komutu
            if line[i] == "@":
                i += 1
                cmd, i = self._read_identifier(line, i, line_num)

                # namespace mi? (@requests.get)
                if i < length and line[i] == ".":
                    i += 1
                    method, i = self._read_identifier(line, i, line_num)
                    tokens.append(Token("NAMESPACE", cmd, line_num))
                    tokens.append(Token("DOT", ".", line_num))
                    tokens.append(Token("AT_CMD", method, line_num))
                else:
                    tokens.append(Token("AT_CMD", cmd, line_num))
                continue

            # [
            if line[i] == "[":
                tokens.append(Token("LBRACKET", "[", line_num))
                i += 1
                continue

            # ]
            if line[i] == "]":
                tokens.append(Token("RBRACKET", "]", line_num))
                i += 1
                continue

            # ;
            if line[i] == ";":
                tokens.append(Token("SEMICOLON", ";", line_num))
                i += 1
                continue

            # String — double quote
            if line[i] == '"':
                s, i = self._read_string(line, i, line_num, '"')
                tokens.append(Token("STRING", s, line_num))
                continue

            # String — single quote
            if line[i] == "'":
                s, i = self._read_string(line, i, line_num, "'")
                tokens.append(Token("STRING", s, line_num))
                continue

            # Number
            if line[i].isdigit() or (line[i] == "-" and i + 1 < length and line[i+1].isdigit()):
                num, i = self._read_number(line, i, line_num)
                tokens.append(Token("NUMBER", num, line_num))
                continue

            # Boolean
            if line[i:i+4] == "True" or line[i:i+5] == "False":
                val = "True" if line[i:i+4] == "True" else "False"
                tokens.append(Token("BOOL", val, line_num))
                i += len(val)
                continue

            # RAW expression (conditions, arithmetic, variable references)
            raw, i = self._read_raw(line, i, line_num)
            if raw:
                tokens.append(Token("RAW", raw, line_num))

        return tokens

    # ── Helper readers ────────────────────────────────────────

    def _read_identifier(self, line: str, i: int, line_num: int):
        start = i
        while i < len(line) and (line[i].isalnum() or line[i] in "_"):
            i += 1
        if i == start:
            raise LexerError(f"Expected identifier after '@', got {line[i]!r}", line_num, i)
        return line[start:i], i

    def _read_string(self, line: str, i: int, line_num: int, quote: str):
        i += 1  # skip opening quote
        start = i
        while i < len(line) and line[i] != quote:
            if line[i] == "\\" and i + 1 < len(line):
                i += 2
                continue
            i += 1
        if i >= len(line):
            raise LexerError("Unterminated string", line_num, start)
        result = line[start:i]
        i += 1  # skip closing quote
        return result, i

    def _read_number(self, line: str, i: int, line_num: int):
        start = i
        if line[i] == "-":
            i += 1
        while i < len(line) and (line[i].isdigit() or line[i] == "."):
            i += 1
        return line[start:i], i

    def _read_raw(self, line: str, i: int, line_num: int):
        """Delegate to SyntaxEngine for consistent depth-aware block reading."""
        from .syntax_engine import get_syntax_engine
        content, new_i = get_syntax_engine().read_block(line, i)
        return content, new_i


# ─────────────────────────────────────────────────────────────
# SINGLETON — modlar bu instance'a hook ekler
# ─────────────────────────────────────────────────────────────

_lexer_instance = Lexer()


def get_lexer() -> Lexer:
    return _lexer_instance


def tokenize(source: str) -> List[Token]:
    return _lexer_instance.tokenize(source)
