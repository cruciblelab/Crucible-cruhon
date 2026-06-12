"""Base64 stdlib wrappers for Cruhon — @base64.*"""
from ..registry import register_lib, register_lib_call

_B64 = "__import__('base64')"


def register():
    register_lib("base64", "base64")

    register_lib_call("base64", "encode",
        lambda a: f"{_B64}.b64encode({a[0]}.encode() if isinstance({a[0]}, str) else {a[0]}).decode()")

    register_lib_call("base64", "decode",
        lambda a: f"{_B64}.b64decode({a[0]}).decode()")

    register_lib_call("base64", "encode_bytes",
        lambda a: f"{_B64}.b64encode({a[0]})")

    register_lib_call("base64", "decode_bytes",
        lambda a: f"{_B64}.b64decode({a[0]})")

    register_lib_call("base64", "urlsafe_encode",
        lambda a: f"{_B64}.urlsafe_b64encode({a[0]}.encode() if isinstance({a[0]}, str) else {a[0]}).decode()")

    register_lib_call("base64", "urlsafe_decode",
        lambda a: f"{_B64}.urlsafe_b64decode({a[0]}).decode()")

    register_lib_call("base64", "b32encode",
        lambda a: f"{_B64}.b32encode({a[0]}.encode() if isinstance({a[0]}, str) else {a[0]}).decode()")

    register_lib_call("base64", "b32decode",
        lambda a: f"{_B64}.b32decode({a[0]}).decode()")

    register_lib_call("base64", "b16encode",
        lambda a: f"{_B64}.b16encode({a[0]}.encode() if isinstance({a[0]}, str) else {a[0]}).decode()")

    register_lib_call("base64", "b16decode",
        lambda a: f"{_B64}.b16decode({a[0]}).decode()")
