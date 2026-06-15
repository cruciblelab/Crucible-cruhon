"""
cruhon/core/libs/tokenize_.py
=============================
Python source tokenizer for Cruhon — @tokenize.*

Tokenize Python source code strings and extract tokens by category.
Each token is a named tuple with fields: type, string, start, end, line.

━━━ TOKEN LISTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @tokenize.tokens[source]        → all tokens as a list
  @tokenize.names[source]         → NAME tokens (identifiers)
  @tokenize.strings[source]       → STRING literal tokens
  @tokenize.numbers[source]       → NUMBER literal tokens
  @tokenize.comments[source]      → COMMENT tokens
  @tokenize.ops[source]           → OP (operator/delimiter) tokens
  @tokenize.keywords[source]      → keyword tokens from NAME tokens

━━━ INDIVIDUAL TOKEN FIELDS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @tokenize.type[tok]             → token type number
  @tokenize.string[tok]           → token string value
  @tokenize.start[tok]            → (row, col) start position
  @tokenize.end[tok]              → (row, col) end position
  @tokenize.line[tok]             → source line containing the token

━━━ TYPE CONSTANTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @tokenize.NAME[]                → tokenize.NAME constant
  @tokenize.OP[]                  → tokenize.OP constant
  @tokenize.NUMBER[]              → tokenize.NUMBER constant
  @tokenize.STRING[]              → tokenize.STRING constant
  @tokenize.COMMENT[]             → tokenize.COMMENT constant
  @tokenize.NEWLINE[]             → tokenize.NEWLINE constant
  @tokenize.INDENT[]              → tokenize.INDENT constant
  @tokenize.DEDENT[]              → tokenize.DEDENT constant
  @tokenize.tok_name[n]           → string name for token type number

━━━ UTILITIES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @tokenize.untokenize[tokens]    → reconstruct source from token list
  @tokenize.count[source]         → total number of tokens
  @tokenize.unique_names[source]  → sorted list of unique identifiers
"""
from ..registry import register_lib, register_lib_call

_TK = "__import__('tokenize')"
_IO = "__import__('io')"

# Helper: tokenize a source string, return list of TokenInfo
_TOK_LIST = (
    f"(lambda _src: list({_TK}.generate_tokens({_IO}.StringIO(_src).readline)))"
)

# Filter by token type
_FILTER = (
    f"(lambda _src, _type: "
    f"[_t for _t in {_TOK_LIST}(_src) if _t.type == _type])"
)


def register():
    register_lib("tokenize", None)

    # ── Token lists ───────────────────────────────────────────
    register_lib_call("tokenize", "tokens",
        lambda a: f"{_TOK_LIST}({a[0]})")
    register_lib_call("tokenize", "names",
        lambda a: f"{_FILTER}({a[0]}, {_TK}.NAME)")
    register_lib_call("tokenize", "strings",
        lambda a: f"{_FILTER}({a[0]}, {_TK}.STRING)")
    register_lib_call("tokenize", "numbers",
        lambda a: f"{_FILTER}({a[0]}, {_TK}.NUMBER)")
    register_lib_call("tokenize", "comments",
        lambda a: f"{_FILTER}({a[0]}, {_TK}.COMMENT)")
    register_lib_call("tokenize", "ops",
        lambda a: f"{_FILTER}({a[0]}, {_TK}.OP)")
    register_lib_call("tokenize", "keywords",
        lambda a: (
            f"(lambda _src: [_t for _t in {_TOK_LIST}(_src) "
            f"if _t.type == {_TK}.NAME and __import__('keyword').iskeyword(_t.string)])({a[0]})"
        ))

    # ── Individual token fields ───────────────────────────────
    register_lib_call("tokenize", "type",
        lambda a: f"{a[0]}.type")
    register_lib_call("tokenize", "string",
        lambda a: f"{a[0]}.string")
    register_lib_call("tokenize", "start",
        lambda a: f"{a[0]}.start")
    register_lib_call("tokenize", "end",
        lambda a: f"{a[0]}.end")
    register_lib_call("tokenize", "line",
        lambda a: f"{a[0]}.line")

    # ── Type constants ────────────────────────────────────────
    register_lib_call("tokenize", "NAME",
        lambda a: f"{_TK}.NAME")
    register_lib_call("tokenize", "OP",
        lambda a: f"{_TK}.OP")
    register_lib_call("tokenize", "NUMBER",
        lambda a: f"{_TK}.NUMBER")
    register_lib_call("tokenize", "STRING",
        lambda a: f"{_TK}.STRING")
    register_lib_call("tokenize", "COMMENT",
        lambda a: f"{_TK}.COMMENT")
    register_lib_call("tokenize", "NEWLINE",
        lambda a: f"{_TK}.NEWLINE")
    register_lib_call("tokenize", "INDENT",
        lambda a: f"{_TK}.INDENT")
    register_lib_call("tokenize", "DEDENT",
        lambda a: f"{_TK}.DEDENT")
    register_lib_call("tokenize", "tok_name",
        lambda a: f"{_TK}.tok_name[{a[0]}]")

    # ── Utilities ─────────────────────────────────────────────
    register_lib_call("tokenize", "untokenize",
        lambda a: f"{_TK}.untokenize({a[0]})")
    register_lib_call("tokenize", "count",
        lambda a: f"len({_TOK_LIST}({a[0]}))")
    register_lib_call("tokenize", "unique_names",
        lambda a: (
            f"sorted(set(_t.string for _t in {_TOK_LIST}({a[0]}) "
            f"if _t.type == {_TK}.NAME))"
        ))
