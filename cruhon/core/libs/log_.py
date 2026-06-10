"""
Logging stdlib wrappers for Cruhon — @log.*

Covers the logging module so a non-coder can add structured logging to
any project with one-liners, without knowing Handler / Formatter / Logger.

━━━ SETUP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @log.setup[]                         — INFO to stdout, default format
  @log.setup[level]                    — "DEBUG" / "INFO" / "WARNING" / "ERROR"
  @log.setup[level; file]              — also write to file
  @log.setup[level; file; fmt]         — custom format string
  @log.to_file[path]                   — add file handler to root logger
  @log.to_file[path; level]            — file handler with specific level
  @log.format[fmt]                     — update root logger format
  @log.set_level[level]                — change root logger level at runtime

━━━ LOG MESSAGES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @log.debug[msg]
  @log.info[msg]
  @log.warning[msg]
  @log.error[msg]
  @log.critical[msg]
  @log.exception[msg]     — ERROR + current exception traceback

━━━ NAMED LOGGERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @log.get[name]           → logging.getLogger(name)
  @log.child[logger; name] → logger.getChild(name)

━━━ UTILITY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @log.disable[]           — disable all logging
  @log.enable[]            — re-enable (set level NOTSET)
  @log.handlers[]          → list of root logger handlers
  @log.clear[]             — remove all root logger handlers
"""
from ..registry import register_lib, register_lib_call

_LG = "__import__('logging')"

_DEFAULT_FMT = "'%(asctime)s [%(levelname)s] %(message)s'"


def register():
    register_lib("log", None)

    # ── SETUP ────────────────────────────────────────────────
    register_lib_call("log", "setup",
        lambda a: (
            f"{_LG}.basicConfig("
            f"level=getattr({_LG}, {a[0]}.upper(), {_LG}.INFO), "
            f"filename={a[1]}, "
            f"format={a[2] if len(a)>2 else _DEFAULT_FMT}, "
            f"encoding='utf-8', force=True)"
            if len(a) > 1 else
            f"{_LG}.basicConfig("
            f"level=getattr({_LG}, {a[0]}.upper(), {_LG}.INFO), "
            f"format={_DEFAULT_FMT}, force=True)"
            if len(a) == 1 else
            f"{_LG}.basicConfig(level={_LG}.INFO, format={_DEFAULT_FMT}, force=True)"
        ))

    register_lib_call("log", "to_file",
        lambda a: (
            f"(lambda _h: ({_LG}.getLogger().addHandler(_h), _h)[1])"
            f"((__import__('logging').FileHandler({a[0]}, encoding='utf-8')))"
            if len(a) == 1 else
            f"(lambda _h: (_h.setLevel(getattr({_LG}, {a[1]}.upper(), {_LG}.DEBUG)), "
            f"{_LG}.getLogger().addHandler(_h), _h)[2])"
            f"((__import__('logging').FileHandler({a[0]}, encoding='utf-8')))"
        ))

    register_lib_call("log", "format",
        lambda a: (
            f"[_h.setFormatter(__import__('logging').Formatter({a[0]})) "
            f"for _h in {_LG}.getLogger().handlers] or None"
        ))

    register_lib_call("log", "set_level",
        lambda a: f"{_LG}.getLogger().setLevel(getattr({_LG}, {a[0]}.upper(), {_LG}.INFO))")

    # ── LOG MESSAGES ─────────────────────────────────────────
    for lvl in ("debug", "info", "warning", "error", "critical", "exception"):
        register_lib_call("log", lvl,
            (lambda l: lambda a: f"{_LG}.{l}(str({a[0]}))")(lvl))

    # ── NAMED LOGGERS ────────────────────────────────────────
    _root = '"root"'
    register_lib_call("log", "get",
        lambda a: f"{_LG}.getLogger({a[0] if a else _root})")

    register_lib_call("log", "child",
        lambda a: f"{a[0]}.getChild({a[1]})")

    # ── UTILITY ──────────────────────────────────────────────
    register_lib_call("log", "disable",
        lambda a: f"{_LG}.disable({_LG}.CRITICAL)")

    register_lib_call("log", "enable",
        lambda a: f"{_LG}.disable({_LG}.NOTSET)")

    register_lib_call("log", "handlers",
        lambda a: f"{_LG}.getLogger().handlers")

    register_lib_call("log", "clear",
        lambda a: f"{_LG}.getLogger().handlers.clear()")
