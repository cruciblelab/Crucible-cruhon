"""ANSI color stdlib wrappers for Cruhon. No external dependencies."""
from ..registry import register_lib, register_lib_call

_RESET = "\\033[0m"

_CODES = {
    "red":    "\\033[31m",
    "green":  "\\033[32m",
    "yellow": "\\033[33m",
    "blue":   "\\033[34m",
    "cyan":   "\\033[36m",
    "bold":   "\\033[1m",
    "dim":    "\\033[2m",
}


def _color_handler(code: str):
    """Returns a handler that wraps text with ANSI color codes.
    Uses string concatenation — NOT nested f-strings.
    """
    def handler(args):
        if not args:
            return f'"{code}"'
        text = args[0]
        return f'("{code}" + str({text}) + "{_RESET}")'
    return handler


def register():
    register_lib("color", None)  # Builtin namespace, no @import needed

    for name, code in _CODES.items():
        register_lib_call("color", name, _color_handler(code))

    register_lib_call("color", "reset",
        lambda args: f'"{_RESET}"')
