"""YAML (@yaml.*) stdlib wrappers for Cruhon. Requires: pip install pyyaml"""
from ..registry import register_lib, register_lib_call

_BUILTIN = "__builtin__"
_YM = "__import__('yaml')"


def register():
    register_lib("yaml", _BUILTIN)

    register_lib_call("yaml", "loads",
        lambda args: f"{_YM}.safe_load({args[0]})" if args else f"{_YM}.safe_load('')")

    register_lib_call("yaml", "dumps",
        lambda args: f"{_YM}.dump({args[0]}, default_flow_style=False)" if args else f"{_YM}.dump(None)")

    register_lib_call("yaml", "load_file",
        lambda args: (
            f"(lambda __f: {_YM}.safe_load(__f))(open({args[0]}, 'r', encoding='utf-8').read())"
            if args else f"{_YM}.safe_load('')"
        ))

    register_lib_call("yaml", "dump_file",
        lambda args: (
            f"(open({args[1]}, 'w', encoding='utf-8').write({_YM}.dump({args[0]}, default_flow_style=False)), None)[1]"
            if len(args) >= 2 else "None"
        ))

    register_lib_call("yaml", "parse",
        lambda args: f"{_YM}.safe_load({args[0]})" if args else f"{_YM}.safe_load('')")

    register_lib_call("yaml", "stringify",
        lambda args: f"{_YM}.dump({args[0]}, default_flow_style=False)" if args else "''")

    register_lib_call("yaml", "load_all",
        lambda args: f"list({_YM}.safe_load_all({args[0]}))" if args else "[]")

    register_lib_call("yaml", "get",
        lambda args: (
            f"({_YM}.safe_load({args[0]}) or {{}}).get({args[1]})"
            if len(args) >= 2 else "None"
        ))

    register_lib_call("yaml", "to_json",
        lambda args: (
            f"__import__('json').dumps({_YM}.safe_load({args[0]}))"
            if args else "'null'"
        ))

    register_lib_call("yaml", "from_json",
        lambda args: (
            f"{_YM}.dump(__import__('json').loads({args[0]}), default_flow_style=False)"
            if args else "''"
        ))
