"""IO stdlib wrappers for Cruhon — @io.*"""
from ..registry import register_lib, register_lib_call

_IO = "__import__('io')"


def register():
    register_lib("io", "io")

    register_lib_call("io", "StringIO",
        lambda a: f"{_IO}.StringIO({a[0] if a else ''})")

    register_lib_call("io", "BytesIO",
        lambda a: f"{_IO}.BytesIO({a[0]})" if a else f"{_IO}.BytesIO(b'')")

    register_lib_call("io", "read",
        lambda a: f"{a[0]}.read({a[1] if len(a)>1 else ''})")

    register_lib_call("io", "readline",
        lambda a: f"{a[0]}.readline()")

    register_lib_call("io", "readlines",
        lambda a: f"{a[0]}.readlines()")

    register_lib_call("io", "write",
        lambda a: f"{a[0]}.write({a[1]})" if len(a) > 1 else f"{a[0]}.write('')")

    register_lib_call("io", "writelines",
        lambda a: f"{a[0]}.writelines({a[1]})" if len(a) > 1 else f"{a[0]}.writelines([])")

    register_lib_call("io", "getvalue",
        lambda a: f"{a[0]}.getvalue()")

    register_lib_call("io", "seek",
        lambda a: f"{a[0]}.seek({a[1] if len(a)>1 else 0})")

    register_lib_call("io", "tell",
        lambda a: f"{a[0]}.tell()")

    register_lib_call("io", "truncate",
        lambda a: f"{a[0]}.truncate({a[1] if len(a)>1 else ''})")

    register_lib_call("io", "close",
        lambda a: f"{a[0]}.close()")

    register_lib_call("io", "closed",
        lambda a: f"{a[0]}.closed")

    register_lib_call("io", "flush",
        lambda a: f"{a[0]}.flush()")

    register_lib_call("io", "open",
        lambda a: (
            f"open({a[0]}, {a[1]})" if len(a) > 1 else
            f"open({a[0]}, 'r')"
        ))

    register_lib_call("io", "open_bytes",
        lambda a: f"open({a[0]}, 'rb')")

    register_lib_call("io", "open_write",
        lambda a: f"open({a[0]}, 'w')")

    register_lib_call("io", "open_append",
        lambda a: f"open({a[0]}, 'a')")
