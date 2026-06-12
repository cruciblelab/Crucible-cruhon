"""Regex (@re.*) stdlib wrappers for Cruhon."""
from ..registry import register_lib, register_lib_call

_RE = "__import__('re')"


def register():
    # Keep "re" as importable so @import[re] still works for re.IGNORECASE etc.
    register_lib("re", "re")

    register_lib_call("re", "match",
        lambda args: f"{_RE}.match({args[0]}, {args[1]})" if len(args) > 1 else f"{_RE}.match({args[0]}, '')")

    register_lib_call("re", "search",
        lambda args: f"{_RE}.search({args[0]}, {args[1]})" if len(args) > 1 else f"{_RE}.search({args[0]}, '')")

    register_lib_call("re", "fullmatch",
        lambda args: f"{_RE}.fullmatch({args[0]}, {args[1]})" if len(args) > 1 else f"{_RE}.fullmatch({args[0]}, '')")

    register_lib_call("re", "findall",
        lambda args: f"{_RE}.findall({args[0]}, {args[1]})" if len(args) > 1 else f"{_RE}.findall({args[0]}, '')")

    register_lib_call("re", "finditer",
        lambda args: f"{_RE}.finditer({args[0]}, {args[1]})" if len(args) > 1 else f"{_RE}.finditer({args[0]}, '')")

    register_lib_call("re", "sub",
        lambda args: (
            f"{_RE}.sub({args[0]}, {args[1]}, {args[2]})" if len(args) >= 3
            else f"{_RE}.sub({args[0]}, {args[1]}, '')" if len(args) == 2
            else f"{_RE}.sub({args[0]}, '', '')"
        ))

    register_lib_call("re", "subn",
        lambda args: (
            f"{_RE}.subn({args[0]}, {args[1]}, {args[2]})" if len(args) >= 3
            else f"{_RE}.subn({args[0]}, {args[1]}, '')"
        ))

    register_lib_call("re", "split",
        lambda args: f"{_RE}.split({args[0]}, {args[1]})" if len(args) > 1 else f"{_RE}.split({args[0]}, '')")

    register_lib_call("re", "compile",
        lambda args: f"{_RE}.compile({args[0]})" if args else f"{_RE}.compile('')")

    register_lib_call("re", "escape",
        lambda args: f"{_RE}.escape({args[0]})" if args else f"{_RE}.escape('')")

    register_lib_call("re", "is_match",
        lambda args: f"bool({_RE}.search({args[0]}, {args[1]}))" if len(args) > 1 else "False")

    register_lib_call("re", "groups",
        lambda args: (
            f"(lambda __m: __m.groups() if __m else ())({_RE}.search({args[0]}, {args[1]}))"
            if len(args) > 1 else "()"
        ))

    register_lib_call("re", "group1",
        lambda args: (
            f"(lambda __m: __m.group(1) if __m else None)({_RE}.search({args[0]}, {args[1]}))"
            if len(args) > 1 else "None"
        ))

    register_lib_call("re", "named",
        lambda args: (
            f"(lambda __m: __m.groupdict() if __m else {{}})({_RE}.search({args[0]}, {args[1]}))"
            if len(args) > 1 else "{}"
        ))

    register_lib_call("re", "count",
        lambda args: f"len({_RE}.findall({args[0]}, {args[1]}))" if len(args) > 1 else "0")

    register_lib_call("re", "replace_first",
        lambda args: (
            f"{_RE}.sub({args[0]}, {args[1]}, {args[2]}, count=1)" if len(args) >= 3
            else f"{_RE}.sub({args[0]}, {args[1]}, '', count=1)"
        ))
