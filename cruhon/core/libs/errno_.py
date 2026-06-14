"""
cruhon/core/libs/errno_.py
==========================
OS error-code helpers for Cruhon — @errno.*

Map between errno integers and their symbolic names.

━━━ LOOK UP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @errno.name[n]                  → "ENOENT" for error code n
  @errno.description[n]           → human-readable description string
  @errno.code[name]               → integer value for "ENOENT" etc.
  @errno.all[]                    → dict of name → code for every error

━━━ COMMON CODES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @errno.ENOENT[]  @errno.EEXIST[]  @errno.EACCES[]
  @errno.EPERM[]   @errno.ENOTEMPTY[]
"""
from ..registry import register_lib, register_lib_call

_EN = "__import__('errno')"
_OS = "__import__('os')"


def register():
    register_lib("errno", None)

    register_lib_call("errno", "name",
        lambda a: f"{_EN}.errorcode.get({a[0]}, None)")
    register_lib_call("errno", "description",
        lambda a: f"{_OS}.strerror({a[0]})")
    register_lib_call("errno", "code",
        lambda a: f"getattr({_EN}, {a[0]})")
    register_lib_call("errno", "all",
        lambda a: f"{_EN}.errorcode")

    for _sym in ("ENOENT", "EEXIST", "EACCES", "EPERM", "ENOTEMPTY",
                 "EINVAL", "EBADF", "EISDIR", "ENOTDIR", "EAGAIN"):
        register_lib_call("errno", _sym,
            (lambda s: (lambda a: f"getattr({_EN}, '{s}')"))(_sym))
