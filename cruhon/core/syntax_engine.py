"""
cruhon/core/syntax_engine.py
============================
Single truth source for argument and expression parsing.
Both Lexer._read_raw and Parser.parse_args delegate here.

Introduced in v0.6 to fix inconsistent bracket/depth handling between
the two previous separate implementations.
"""

from __future__ import annotations


class SyntaxEngine:

    def split_args(self, source: str) -> list[str]:
        """
        Split a Cruhon argument string on top-level ; separators.

        Rules:
          - ; splits only at depth 0
          - [ ( { increase depth
          - ] ) } decrease depth
          - content inside strings is never a separator
          - escaped characters inside strings are handled

        Examples:
          "a; b; c"           → ["a", "b", "c"]
          "name; [1,2,3]"     → ["name", "[1,2,3]"]
          "name; lst[0]"      → ["name", "lst[0]"]
          'name; "x; y"'      → ["name", '"x; y"']
          "name; add(3, 4)"   → ["name", "add(3, 4)"]
          'name; d["key"]'    → ["name", 'd["key"]']
          "name; [1; 2; 3]"   → ["name", "[1; 2; 3]"]
        """
        args = []
        current: list[str] = []
        depth = 0
        in_string: str | None = None
        i = 0

        while i < len(source):
            ch = source[i]

            if in_string:
                current.append(ch)
                if ch == '\\' and i + 1 < len(source):
                    i += 1
                    current.append(source[i])
                elif ch == in_string:
                    in_string = None
            elif ch in ('"', "'"):
                in_string = ch
                current.append(ch)
            elif ch in '([{':
                depth += 1
                current.append(ch)
            elif ch in ')]}':
                depth -= 1
                current.append(ch)
            elif ch == ';' and depth == 0:
                arg = ''.join(current).strip()
                if arg:
                    args.append(arg)
                current = []
            else:
                current.append(ch)

            i += 1

        last = ''.join(current).strip()
        if last:
            args.append(last)

        return args

    def read_block(self, line: str, start: int) -> tuple[str, int]:
        """
        Read raw content from position `start` until ] or ; at depth 0.
        Returns (content, new_position).

        Produces identical results to the original _read_raw() in lexer.py,
        with the addition of string-aware parsing (original _read_raw had no
        string handling — this is a correctness improvement, not a behavior
        change for normal input).

        The `]` at depth 0 is NOT consumed — the caller decides what to do
        with it (same contract as original _read_raw).
        """
        i = start
        depth = 0
        in_string: str | None = None
        result: list[str] = []

        while i < len(line):
            ch = line[i]

            if in_string:
                result.append(ch)
                if ch == '\\' and i + 1 < len(line):
                    i += 1
                    result.append(line[i])
                elif ch == in_string:
                    in_string = None
            elif ch in ('"', "'"):
                in_string = ch
                result.append(ch)
            elif ch == '[':
                depth += 1
                result.append(ch)
            elif ch == ']':
                if depth == 0:
                    break
                depth -= 1
                result.append(ch)
            elif ch == ';' and depth == 0:
                break
            else:
                result.append(ch)

            i += 1

        return ''.join(result).strip(), i

    def validate_arg(self, arg: str, line: int = 0) -> None:
        """
        Check for common argument mistakes.
        Raises ParseError with a helpful message if malformed.

        Currently detects: unbalanced parentheses (caused by using ; inside
        a function call instead of ,).
        """
        depth = 0
        in_str: str | None = None
        for ch in arg:
            if in_str:
                if ch == in_str:
                    in_str = None
            elif ch in ('"', "'"):
                in_str = ch
            elif ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1

        if depth != 0:
            from .parser import ParseError
            raise ParseError(
                f"Unbalanced parentheses in argument: {arg!r}\n"
                f"  Hint: use , inside function calls, not ;",
                line
            )


# ─────────────────────────────────────────────────────────────
# MODULE-LEVEL SINGLETON
# ─────────────────────────────────────────────────────────────

_syntax_engine = SyntaxEngine()


def get_syntax_engine() -> SyntaxEngine:
    """Return the shared SyntaxEngine instance."""
    return _syntax_engine
