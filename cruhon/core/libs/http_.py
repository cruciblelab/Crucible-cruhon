"""
cruhon/core/libs/http_.py
=========================
HTTP library wrapper for Cruhon.

Registered as @http.* calls.
All methods auto-add `import requests` via the AST walk in transpiler.py.

Supported (sync):
  @http.get[url]
  @http.get[url; headers]
  @http.post[url; data]
  @http.post[url; data; headers]
  @http.put[url; data]
  @http.delete[url]
  @http.json[res]
  @http.text[res]
  @http.status[res]

Supported (async — requires httpx):
  @http.async_get[url]
  @http.async_post[url; data]
  @http.async_json[url]
"""


_SSRF_CHECK = (
    "__import__('cruhon.core.libs.http_', fromlist=['_check_url'])._check_url"
)


def _check_url(url: str) -> str:
    """Block SSRF: reject requests to localhost, link-local, and private ranges."""
    import re
    blocked = re.compile(
        r"^https?://(localhost|127\.|0\.0\.0\.0|::1"
        r"|169\.254\."          # link-local (AWS metadata etc.)
        r"|10\."                # RFC-1918
        r"|172\.(1[6-9]|2[0-9]|3[01])\."  # RFC-1918
        r"|192\.168\.)",
        re.IGNORECASE,
    )
    if blocked.match(url):
        raise PermissionError(
            f"[Cruhon] @http: URL '{url}' is blocked (private/loopback address)."
        )
    return url


def _handler_get(args):
    url = args[0] if args else '""'
    check = f"{_SSRF_CHECK}({url})"
    if len(args) > 1:
        return f"requests.get({check}, headers={args[1]}, timeout=30)"
    return f"requests.get({check}, timeout=30)"


def _handler_post(args):
    url = args[0] if args else '""'
    data = args[1] if len(args) > 1 else "None"
    check = f"{_SSRF_CHECK}({url})"
    if len(args) > 2:
        return f"requests.post({check}, json={data}, headers={args[2]}, timeout=30)"
    return f"requests.post({check}, json={data}, timeout=30)"


def _handler_put(args):
    url = args[0] if args else '""'
    data = args[1] if len(args) > 1 else "None"
    check = f"{_SSRF_CHECK}({url})"
    return f"requests.put({check}, json={data}, timeout=30)"


def _handler_delete(args):
    url = args[0] if args else '""'
    check = f"{_SSRF_CHECK}({url})"
    return f"requests.delete({check}, timeout=30)"


def _handler_json(args):
    res = args[0] if args else "res"
    return f"{res}.json()"


def _handler_text(args):
    res = args[0] if args else "res"
    return f"{res}.text"


def _handler_status(args):
    res = args[0] if args else "res"
    return f"{res}.status_code"


# ── Async handlers (httpx) ────────────────────────────────────

def _handler_async_get(args):
    url = args[0] if args else '""'
    check = f"{_SSRF_CHECK}({url})"
    return f"await __import__('httpx').AsyncClient().get({check})"


def _handler_async_post(args):
    url = args[0] if args else '""'
    data = args[1] if len(args) > 1 else "None"
    check = f"{_SSRF_CHECK}({url})"
    return f"await __import__('httpx').AsyncClient().post({check}, json={data})"


def _handler_async_json(args):
    url = args[0] if args else '""'
    check = f"{_SSRF_CHECK}({url})"
    return f"(await __import__('httpx').AsyncClient().get({check})).json()"


HTTP_HANDLERS = {
    "get":        _handler_get,
    "post":       _handler_post,
    "put":        _handler_put,
    "delete":     _handler_delete,
    "json":       _handler_json,
    "text":       _handler_text,
    "status":     _handler_status,
    "async_get":  _handler_async_get,
    "async_post": _handler_async_post,
    "async_json": _handler_async_json,
}
