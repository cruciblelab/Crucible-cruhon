"""
cruhon/core/libs/argparse_.py
=============================
Command-line argument parsing for Cruhon — @argparse.*

Build a parser from a list of argument specs and parse argv in one call —
no multi-line boilerplate.

━━━ ONE-SHOT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @argparse.parse[specs; argv]    → Namespace from parsing argv
  @argparse.parse_dict[specs; argv] → same, but as a plain dict
        specs is a list; each item is either a flag name ("--name") or a
        [name, options-dict] list, e.g. ["--count", {"type": int}].

━━━ OBJECTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @argparse.new[]                 → empty ArgumentParser
  @argparse.new[description]      → ArgumentParser with a description
  @argparse.to_dict[namespace]    → vars(namespace)
"""
from ..registry import register_lib, register_lib_call

# Build a parser, add each spec, parse argv. A spec may be a str (flag
# name) or a list [name, kwargs-dict].
_BUILD = (
    "(lambda _specs, _argv: (lambda _p: ("
    "[_p.add_argument(_s if isinstance(_s, str) else _s[0], "
    "**(_s[1] if not isinstance(_s, str) and len(_s) > 1 else {})) for _s in _specs], "
    "_p.parse_args(_argv))[1])(__import__('argparse').ArgumentParser()))"
)


def register():
    register_lib("argparse", None)

    # ── One-shot ──────────────────────────────────────────────
    register_lib_call("argparse", "parse",
        lambda a: f"{_BUILD}({a[0]}, {a[1]})")
    register_lib_call("argparse", "parse_dict",
        lambda a: f"vars({_BUILD}({a[0]}, {a[1]}))")

    # ── Objects ───────────────────────────────────────────────
    register_lib_call("argparse", "new",
        lambda a: (
            f"__import__('argparse').ArgumentParser(description={a[0]})" if a else
            f"__import__('argparse').ArgumentParser()"
        ))
    register_lib_call("argparse", "to_dict",
        lambda a: f"vars({a[0]})")
