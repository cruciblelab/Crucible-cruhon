"""JSON stdlib wrappers for Cruhon."""
from ..registry import register_lib, register_lib_call
from .file_ import _vp


def register():
    register_lib("json", "json")

    _fmod = "cruhon.core.libs.file_"

    register_lib_call("json", "parse",
        lambda args: f"__import__('json').loads({args[0]})")

    register_lib_call("json", "stringify",
        lambda args: f"__import__('json').dumps({args[0]})")

    register_lib_call("json", "pretty",
        lambda args: f"__import__('json').dumps({args[0]}, indent=2)")

    register_lib_call("json", "read",
        lambda args: f"__import__('json').loads(open(__import__({_fmod!r}, fromlist=['_vp'])._vp({args[0]})).read())")

    register_lib_call("json", "write",
        lambda args: (
            f"(open(__import__({_fmod!r}, fromlist=['_vp'])._vp({args[0]}), 'w').write(__import__('json').dumps({args[1]})), None)[1]"
            if len(args) > 1 else "None"
        ))
