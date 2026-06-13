"""
cruhon/core/libs/stat_.py
=========================
Stat wrappers for Cruhon — @stat.*

File mode inspection — parses raw stat() mode integers into human-readable
forms, and checks access permissions.

━━━ RAW ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @stat.of[path]                  → os.stat_result object
  @stat.mode[path]                → file mode integer

━━━ MODE PARSING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @stat.filemode[mode]            → "-rwxr-xr-x" string
  @stat.octal[mode]               → "755" (no leading zero)
  @stat.perms[path]               → "rwxr-xr-x" (without leading type char)
  @stat.is_file[mode]             → bool
  @stat.is_dir[mode]              → bool
  @stat.is_link[mode]             → bool (symlink)
  @stat.is_exec[mode]             → bool (owner-executable bit)
  @stat.is_readable[mode]         → bool (owner-readable bit)
  @stat.is_writable[mode]         → bool (owner-writable bit)

━━━ ACCESS (LIVE CHECK) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @stat.readable[path]            → bool (os.access)
  @stat.writable[path]            → bool
  @stat.executable[path]          → bool
"""
from ..registry import register_lib, register_lib_call

_ST = "__import__('stat')"
_OS = "__import__('os')"


def register():
    register_lib("stat", None)

    # ── Raw ───────────────────────────────────────────────────
    register_lib_call("stat", "of",
        lambda a: f"{_OS}.stat({a[0]})")

    register_lib_call("stat", "mode",
        lambda a: f"{_OS}.stat({a[0]}).st_mode")

    # ── Mode parsing ──────────────────────────────────────────
    register_lib_call("stat", "filemode",
        lambda a: f"{_ST}.filemode({a[0]})")

    register_lib_call("stat", "octal",
        lambda a: f"oct({a[0]})[-3:]")

    register_lib_call("stat", "perms",
        lambda a: f"{_ST}.filemode({_OS}.stat({a[0]}).st_mode)[1:]")

    register_lib_call("stat", "is_file",
        lambda a: f"{_ST}.S_ISREG({a[0]})")

    register_lib_call("stat", "is_dir",
        lambda a: f"{_ST}.S_ISDIR({a[0]})")

    register_lib_call("stat", "is_link",
        lambda a: f"{_ST}.S_ISLNK({a[0]})")

    register_lib_call("stat", "is_exec",
        lambda a: f"bool({a[0]} & {_ST}.S_IXUSR)")

    register_lib_call("stat", "is_readable",
        lambda a: f"bool({a[0]} & {_ST}.S_IRUSR)")

    register_lib_call("stat", "is_writable",
        lambda a: f"bool({a[0]} & {_ST}.S_IWUSR)")

    # ── Access (live check) ───────────────────────────────────
    register_lib_call("stat", "readable",
        lambda a: f"{_OS}.access({a[0]}, {_OS}.R_OK)")

    register_lib_call("stat", "writable",
        lambda a: f"{_OS}.access({a[0]}, {_OS}.W_OK)")

    register_lib_call("stat", "executable",
        lambda a: f"{_OS}.access({a[0]}, {_OS}.X_OK)")
