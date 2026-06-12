"""PDF (@pdf.*) wrappers for Cruhon. Requires: pip install pdfplumber"""
from ..registry import register_lib, register_lib_call

_BUILTIN = "__builtin__"
_PP = "__import__('pdfplumber')"


def register():
    register_lib("pdf", _BUILTIN)

    register_lib_call("pdf", "open",
        lambda args: f"{_PP}.open({args[0]})" if args else f"{_PP}.open('')")

    register_lib_call("pdf", "pages",
        lambda args: f"{_PP}.open({args[0]}).pages" if args else "[]")

    register_lib_call("pdf", "page_count",
        lambda args: f"len({_PP}.open({args[0]}).pages)" if args else "0")

    register_lib_call("pdf", "text",
        lambda args: (
            f"' '.join(p.extract_text() or '' for p in {_PP}.open({args[0]}).pages)"
            if args else "''"
        ))

    register_lib_call("pdf", "text_of",
        lambda args: (
            f"{_PP}.open({args[0]}).pages[{args[1]}].extract_text() or ''"
            if len(args) >= 2 else "''"
        ))

    register_lib_call("pdf", "words",
        lambda args: (
            f"[w['text'] for p in {_PP}.open({args[0]}).pages for w in (p.extract_words() or [])]"
            if args else "[]"
        ))

    register_lib_call("pdf", "tables",
        lambda args: (
            f"[t for p in {_PP}.open({args[0]}).pages for t in (p.extract_tables() or [])]"
            if args else "[]"
        ))

    register_lib_call("pdf", "table_of",
        lambda args: (
            f"{_PP}.open({args[0]}).pages[{args[1]}].extract_table()"
            if len(args) >= 2 else "None"
        ))

    register_lib_call("pdf", "metadata",
        lambda args: f"{_PP}.open({args[0]}).metadata" if args else "{}")

    register_lib_call("pdf", "crop",
        lambda args: (
            f"{_PP}.open({args[0]}).pages[{args[1]}].crop(({args[2]}, {args[3]}, {args[4]}, {args[5]}))"
            if len(args) >= 6 else "None"
        ))

    register_lib_call("pdf", "lines",
        lambda args: (
            f"[ln for p in {_PP}.open({args[0]}).pages for ln in (p.extract_text() or '').splitlines()]"
            if args else "[]"
        ))
