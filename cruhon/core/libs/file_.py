"""File system stdlib wrappers for Cruhon."""
from ..registry import register_lib, register_lib_call


def _vp(path: str) -> str:
    """Validate path — block traversal outside cwd."""
    import os
    p = os.path.abspath(str(path))
    if not p.startswith(os.getcwd()):
        raise PermissionError(
            f"[Cruhon] @file: '{path}' is outside the working directory. Access blocked."
        )
    return path


def register():
    register_lib("file", "builtins")

    _mod = "cruhon.core.libs.file_"

    register_lib_call("file", "read",
        lambda args: f"open(__import__({_mod!r}, fromlist=['_vp'])._vp({args[0]})).read()")

    register_lib_call("file", "lines",
        lambda args: f"open(__import__({_mod!r}, fromlist=['_vp'])._vp({args[0]})).readlines()")

    register_lib_call("file", "exists",
        lambda args: f"__import__('os').path.exists(__import__({_mod!r}, fromlist=['_vp'])._vp({args[0]}))")

    register_lib_call("file", "delete",
        lambda args: f"__import__('os').remove(__import__({_mod!r}, fromlist=['_vp'])._vp({args[0]}))")

    register_lib_call("file", "write",
        lambda args: (
            f"(open(__import__({_mod!r}, fromlist=['_vp'])._vp({args[0]}), 'w').write({args[1]}), None)[1]"
            if len(args) > 1 else
            f"open(__import__({_mod!r}, fromlist=['_vp'])._vp({args[0]}), 'w').close()"
        ))

    register_lib_call("file", "append",
        lambda args: (
            f"(open(__import__({_mod!r}, fromlist=['_vp'])._vp({args[0]}), 'a').write({args[1]}), None)[1]"
            if len(args) > 1 else
            f"open(__import__({_mod!r}, fromlist=['_vp'])._vp({args[0]}), 'a').close()"
        ))
