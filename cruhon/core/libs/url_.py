"""URL parsing/encoding wrappers for Cruhon — @url.*"""
from ..registry import register_lib, register_lib_call

_UP = "__import__('urllib.parse', fromlist=['parse'])"


def register():
    register_lib("url", None)

    register_lib_call("url", "parse",
        lambda a: f"__import__('urllib.parse', fromlist=['urlparse']).urlparse({a[0]})")

    register_lib_call("url", "join",
        lambda a: f"__import__('urllib.parse', fromlist=['urljoin']).urljoin({a[0]}, {a[1]})" if len(a) > 1 else f"__import__('urllib.parse', fromlist=['urljoin']).urljoin({a[0]}, '')")

    register_lib_call("url", "quote",
        lambda a: f"__import__('urllib.parse', fromlist=['quote']).quote({a[0]}{', safe=' + a[1] if len(a)>1 else ''})")

    register_lib_call("url", "unquote",
        lambda a: f"__import__('urllib.parse', fromlist=['unquote']).unquote({a[0]})")

    register_lib_call("url", "encode",
        lambda a: f"__import__('urllib.parse', fromlist=['urlencode']).urlencode({a[0]})")

    register_lib_call("url", "decode",
        lambda a: f"dict(__import__('urllib.parse', fromlist=['parse_qsl']).parse_qsl({a[0]}))")

    register_lib_call("url", "parse_qs",
        lambda a: f"__import__('urllib.parse', fromlist=['parse_qs']).parse_qs({a[0]})")

    register_lib_call("url", "build",
        lambda a: f"__import__('urllib.parse', fromlist=['urlencode']).urlencode({a[0]})")

    register_lib_call("url", "split",
        lambda a: f"__import__('urllib.parse', fromlist=['urlsplit']).urlsplit({a[0]})")

    register_lib_call("url", "unsplit",
        lambda a: f"__import__('urllib.parse', fromlist=['urlunsplit']).urlunsplit({a[0]})")

    register_lib_call("url", "scheme",
        lambda a: f"__import__('urllib.parse', fromlist=['urlparse']).urlparse({a[0]}).scheme")

    register_lib_call("url", "netloc",
        lambda a: f"__import__('urllib.parse', fromlist=['urlparse']).urlparse({a[0]}).netloc")

    register_lib_call("url", "path",
        lambda a: f"__import__('urllib.parse', fromlist=['urlparse']).urlparse({a[0]}).path")

    register_lib_call("url", "query",
        lambda a: f"__import__('urllib.parse', fromlist=['urlparse']).urlparse({a[0]}).query")
