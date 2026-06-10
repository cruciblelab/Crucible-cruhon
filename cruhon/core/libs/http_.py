"""
HTTP stdlib wrappers for Cruhon — @http.*

Covers requests (sync) and httpx (async) with SSRF protection on every
URL argument. A non-coder can call APIs, download files, post forms and
handle responses without knowing the requests API.

━━━ SYNC REQUESTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @http.get[url]
  @http.get[url; headers=; timeout=; params=]
  @http.post[url; data]
  @http.post[url; data; headers=; timeout=]
  @http.put[url; data]
  @http.put[url; data; headers=; timeout=]
  @http.patch[url; data]
  @http.patch[url; data; headers=; timeout=]
  @http.delete[url]
  @http.delete[url; headers=; timeout=]
  @http.head[url]
  @http.options[url]
  @http.form[url; data]          — POST application/x-www-form-urlencoded

━━━ RESPONSE ACCESSORS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @http.json[res]                → res.json()
  @http.text[res]                → res.text
  @http.bytes[res]               → res.content
  @http.status[res]              → res.status_code
  @http.ok[res]                  → bool (status < 400)
  @http.headers[res]             → dict of response headers
  @http.cookies[res]             → dict of response cookies
  @http.url[res]                 → final URL (after redirects)
  @http.raise_for_status[res]    — raise if 4xx/5xx

━━━ DOWNLOAD ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @http.download[url; path]      — download binary file to disk

━━━ ASYNC (requires httpx) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @http.async_get[url]
  @http.async_get[url; headers=; timeout=]
  @http.async_post[url; data]
  @http.async_post[url; data; headers=]
  @http.async_put[url; data]
  @http.async_patch[url; data]
  @http.async_delete[url]
  @http.async_json[url]          — GET + .json() in one call
  @http.async_text[url]          — GET + .text in one call
"""

_SSRF_CHECK = (
    "__import__('cruhon.core.libs.http_', fromlist=['_check_url'])._check_url"
)

_DEFAULT_TIMEOUT = 30


def _check_url(url: str) -> str:
    """Block SSRF: reject requests to localhost, link-local, and private ranges."""
    import re
    blocked = re.compile(
        r"^https?://(localhost|127\.|0\.0\.0\.0|::1"
        r"|169\.254\."
        r"|10\."
        r"|172\.(1[6-9]|2[0-9]|3[01])\."
        r"|192\.168\.)",
        re.IGNORECASE,
    )
    if blocked.match(str(url)):
        raise PermissionError(
            f"[Cruhon] @http: URL '{url}' is blocked (private/loopback address)."
        )
    return url


def _chk(url_expr: str) -> str:
    return f"{_SSRF_CHECK}({url_expr})"


def _kwargs(args: list, start: int) -> str:
    """Join args[start:] as extra kwargs (already key=value strings)."""
    extra = ", ".join(args[start:])
    return (", " + extra) if extra else ""


# ── SYNC ─────────────────────────────────────────────────────────────────────

def _handler_get(args):
    url = args[0] if args else '""'
    kw = _kwargs(args, 1)
    return f"requests.get({_chk(url)}, timeout={_DEFAULT_TIMEOUT}{kw})"


def _handler_post(args):
    url  = args[0] if args else '""'
    data = args[1] if len(args) > 1 else "None"
    kw   = _kwargs(args, 2)
    return f"requests.post({_chk(url)}, json={data}, timeout={_DEFAULT_TIMEOUT}{kw})"


def _handler_put(args):
    url  = args[0] if args else '""'
    data = args[1] if len(args) > 1 else "None"
    kw   = _kwargs(args, 2)
    return f"requests.put({_chk(url)}, json={data}, timeout={_DEFAULT_TIMEOUT}{kw})"


def _handler_patch(args):
    url  = args[0] if args else '""'
    data = args[1] if len(args) > 1 else "None"
    kw   = _kwargs(args, 2)
    return f"requests.patch({_chk(url)}, json={data}, timeout={_DEFAULT_TIMEOUT}{kw})"


def _handler_delete(args):
    url = args[0] if args else '""'
    kw  = _kwargs(args, 1)
    return f"requests.delete({_chk(url)}, timeout={_DEFAULT_TIMEOUT}{kw})"


def _handler_head(args):
    url = args[0] if args else '""'
    return f"requests.head({_chk(url)}, timeout={_DEFAULT_TIMEOUT})"


def _handler_options(args):
    url = args[0] if args else '""'
    return f"requests.options({_chk(url)}, timeout={_DEFAULT_TIMEOUT})"


def _handler_form(args):
    url  = args[0] if args else '""'
    data = args[1] if len(args) > 1 else "None"
    return f"requests.post({_chk(url)}, data={data}, timeout={_DEFAULT_TIMEOUT})"


# ── RESPONSE ACCESSORS ────────────────────────────────────────────────────────

def _handler_json(args):
    return f"{args[0] if args else 'res'}.json()"


def _handler_text(args):
    return f"{args[0] if args else 'res'}.text"


def _handler_bytes(args):
    return f"{args[0] if args else 'res'}.content"


def _handler_status(args):
    return f"{args[0] if args else 'res'}.status_code"


def _handler_ok(args):
    return f"{args[0] if args else 'res'}.ok"


def _handler_headers(args):
    return f"dict({args[0] if args else 'res'}.headers)"


def _handler_cookies(args):
    return f"dict({args[0] if args else 'res'}.cookies)"


def _handler_url(args):
    return f"str({args[0] if args else 'res'}.url)"


def _handler_raise_for_status(args):
    return f"{args[0] if args else 'res'}.raise_for_status()"


# ── DOWNLOAD ─────────────────────────────────────────────────────────────────

def _handler_download(args):
    url  = args[0] if args else '""'
    path = args[1] if len(args) > 1 else '"download"'
    return (
        f"(lambda _url, _path: ("
        f"  __import__('os').makedirs(__import__('os').path.dirname(__import__('os').path.abspath(_path)) or '.', exist_ok=True),"
        f"  open(_path, 'wb').write(requests.get({_SSRF_CHECK}(_url), timeout=60, stream=True).content)"
        f")[1])({url}, {path})"
    )


# ── ASYNC (httpx) ─────────────────────────────────────────────────────────────

def _handler_async_get(args):
    url = args[0] if args else '""'
    kw  = _kwargs(args, 1)
    return f"await __import__('httpx').AsyncClient().get({_chk(url)}{kw})"


def _handler_async_post(args):
    url  = args[0] if args else '""'
    data = args[1] if len(args) > 1 else "None"
    kw   = _kwargs(args, 2)
    return f"await __import__('httpx').AsyncClient().post({_chk(url)}, json={data}{kw})"


def _handler_async_put(args):
    url  = args[0] if args else '""'
    data = args[1] if len(args) > 1 else "None"
    return f"await __import__('httpx').AsyncClient().put({_chk(url)}, json={data})"


def _handler_async_patch(args):
    url  = args[0] if args else '""'
    data = args[1] if len(args) > 1 else "None"
    return f"await __import__('httpx').AsyncClient().patch({_chk(url)}, json={data})"


def _handler_async_delete(args):
    url = args[0] if args else '""'
    return f"await __import__('httpx').AsyncClient().delete({_chk(url)})"


def _handler_async_json(args):
    url = args[0] if args else '""'
    return f"(await __import__('httpx').AsyncClient().get({_chk(url)})).json()"


def _handler_async_text(args):
    url = args[0] if args else '""'
    return f"(await __import__('httpx').AsyncClient().get({_chk(url)})).text"


HTTP_HANDLERS = {
    # sync
    "get":              _handler_get,
    "post":             _handler_post,
    "put":              _handler_put,
    "patch":            _handler_patch,
    "delete":           _handler_delete,
    "head":             _handler_head,
    "options":          _handler_options,
    "form":             _handler_form,
    # response
    "json":             _handler_json,
    "text":             _handler_text,
    "bytes":            _handler_bytes,
    "status":           _handler_status,
    "ok":               _handler_ok,
    "headers":          _handler_headers,
    "cookies":          _handler_cookies,
    "url":              _handler_url,
    "raise_for_status": _handler_raise_for_status,
    # download
    "download":         _handler_download,
    # async
    "async_get":        _handler_async_get,
    "async_post":       _handler_async_post,
    "async_put":        _handler_async_put,
    "async_patch":      _handler_async_patch,
    "async_delete":     _handler_async_delete,
    "async_json":       _handler_async_json,
    "async_text":       _handler_async_text,
}
