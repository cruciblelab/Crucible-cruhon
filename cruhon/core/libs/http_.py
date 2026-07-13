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
    return str(url)


def _chk(url_expr: str) -> str:
    return f"{_SSRF_CHECK}({url_expr})"


def _kw(args: list, start: int) -> str:
    """Join args[start:] as extra kwargs. Already key=value strings."""
    extra = args[start:]
    return (", " + ", ".join(extra)) if extra else ""


_KWARG_RE = __import__("re").compile(r'^[A-Za-z_][A-Za-z0-9_]*=(?!=)')


def _is_kwarg(arg) -> bool:
    """True if arg is a pre-formatted `key=value` fragment (produced by
    @cmd[...; key=value] named-parameter syntax) rather than a positional
    expression — so handlers don't mistake e.g. `reason="spam"` for the
    positional data/body argument when the caller skips straight to named
    params without providing one."""
    return bool(_KWARG_RE.match(str(arg).strip()))


def _data_arg(args: list, pos: int):
    """Return (data_expr, kwargs_start_index) for handlers whose optional
    positional "data" argument sits at `pos`. If args[pos] is actually a
    key=value kwarg fragment, data was omitted — treat it as None and let
    kwargs start at `pos` instead of `pos + 1`."""
    if len(args) > pos and not _is_kwarg(args[pos]):
        return args[pos], pos + 1
    return "None", pos


def _timeout(args: list, start: int) -> str:
    """Return timeout kwarg — use default unless user already passed timeout=."""
    has = any(str(a).startswith("timeout=") for a in args[start:])
    return "" if has else f", timeout={_DEFAULT_TIMEOUT}"


# ── SYNC ─────────────────────────────────────────────────────────────────────

def _handler_get(args):
    url = args[0] if args else '""'
    return f"requests.get({_chk(url)}{_timeout(args,1)}{_kw(args,1)})"


def _handler_post(args):
    url = args[0] if args else '""'
    data, start = _data_arg(args, 1)
    return f"requests.post({_chk(url)}, json={data}{_timeout(args,start)}{_kw(args,start)})"


def _handler_put(args):
    url = args[0] if args else '""'
    data, start = _data_arg(args, 1)
    return f"requests.put({_chk(url)}, json={data}{_timeout(args,start)}{_kw(args,start)})"


def _handler_patch(args):
    url = args[0] if args else '""'
    data, start = _data_arg(args, 1)
    return f"requests.patch({_chk(url)}, json={data}{_timeout(args,start)}{_kw(args,start)})"


def _handler_delete(args):
    url = args[0] if args else '""'
    return f"requests.delete({_chk(url)}{_timeout(args,1)}{_kw(args,1)})"


def _handler_head(args):
    url = args[0] if args else '""'
    return f"requests.head({_chk(url)}{_timeout(args,1)}{_kw(args,1)})"


def _handler_options(args):
    url = args[0] if args else '""'
    return f"requests.options({_chk(url)}{_timeout(args,1)}{_kw(args,1)})"


def _handler_form(args):
    url = args[0] if args else '""'
    data, start = _data_arg(args, 1)
    return f"requests.post({_chk(url)}, data={data}{_timeout(args,start)}{_kw(args,start)})"


def _handler_upload(args):
    url   = args[0] if args else '""'
    field = args[1] if len(args) > 1 else '"file"'
    path  = args[2] if len(args) > 2 else '"file"'
    return (
        f"(lambda _u, _f, _p: requests.post({_chk('_u')}, "
        f"files={{_f: open(_p, 'rb')}}{_timeout(args,3)}{_kw(args,3)}))({url}, {field}, {path})"
    )


def _handler_auth_get(args):
    url  = args[0] if args else '""'
    user = args[1] if len(args) > 1 else '""'
    pw   = args[2] if len(args) > 2 else '""'
    return f"requests.get({_chk(url)}, auth=({user}, {pw}){_timeout(args,3)}{_kw(args,3)})"


def _handler_auth_post(args):
    url  = args[0] if args else '""'
    data = args[1] if len(args) > 1 else "None"
    user = args[2] if len(args) > 2 else '""'
    pw   = args[3] if len(args) > 3 else '""'
    return f"requests.post({_chk(url)}, json={data}, auth=({user}, {pw}){_timeout(args,4)}{_kw(args,4)})"


def _handler_elapsed(args):
    return f"{args[0] if args else 'res'}.elapsed.total_seconds()"


def _handler_encoding(args):
    return f"{args[0] if args else 'res'}.encoding"


# ── SESSION ───────────────────────────────────────────────────────────────────

def _handler_session(args):
    return "requests.Session()"


def _handler_session_get(args):
    s, url = (args[0], args[1]) if len(args) > 1 else ("s", '""')
    return f"{s}.get({_chk(url)}{_timeout(args,2)}{_kw(args,2)})"


def _handler_session_post(args):
    s, url = (args[0], args[1]) if len(args) > 1 else ("s", '""')
    data, start = _data_arg(args, 2)
    return f"{s}.post({_chk(url)}, json={data}{_timeout(args,start)}{_kw(args,start)})"


def _handler_session_put(args):
    s, url = (args[0], args[1]) if len(args) > 1 else ("s", '""')
    data, start = _data_arg(args, 2)
    return f"{s}.put({_chk(url)}, json={data}{_timeout(args,start)}{_kw(args,start)})"


def _handler_session_patch(args):
    s, url = (args[0], args[1]) if len(args) > 1 else ("s", '""')
    data, start = _data_arg(args, 2)
    return f"{s}.patch({_chk(url)}, json={data}{_timeout(args,start)}{_kw(args,start)})"


def _handler_session_delete(args):
    s, url = (args[0], args[1]) if len(args) > 1 else ("s", '""')
    return f"{s}.delete({_chk(url)}{_timeout(args,2)}{_kw(args,2)})"


def _handler_session_close(args):
    s = args[0] if args else "s"
    return f"{s}.close()"


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
    kw  = _kw(args, 1)
    return f"await __import__('httpx').AsyncClient().get({_chk(url)}{kw})"


def _handler_async_post(args):
    url = args[0] if args else '""'
    data, start = _data_arg(args, 1)
    return f"await __import__('httpx').AsyncClient().post({_chk(url)}, json={data}{_kw(args,start)})"


def _handler_async_put(args):
    url = args[0] if args else '""'
    data, start = _data_arg(args, 1)
    return f"await __import__('httpx').AsyncClient().put({_chk(url)}, json={data}{_kw(args,start)})"


def _handler_async_patch(args):
    url = args[0] if args else '""'
    data, start = _data_arg(args, 1)
    return f"await __import__('httpx').AsyncClient().patch({_chk(url)}, json={data}{_kw(args,start)})"


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
    # session
    "session":          _handler_session,
    "session_get":      _handler_session_get,
    "session_post":     _handler_session_post,
    "session_put":      _handler_session_put,
    "session_patch":    _handler_session_patch,
    "session_delete":   _handler_session_delete,
    "session_close":    _handler_session_close,
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
    # upload / auth
    "upload":           _handler_upload,
    "auth_get":         _handler_auth_get,
    "auth_post":        _handler_auth_post,
    # download
    "download":         _handler_download,
    # response extras
    "elapsed":          _handler_elapsed,
    "encoding":         _handler_encoding,
    # async
    "async_get":        _handler_async_get,
    "async_post":       _handler_async_post,
    "async_put":        _handler_async_put,
    "async_patch":      _handler_async_patch,
    "async_delete":     _handler_async_delete,
    "async_json":       _handler_async_json,
    "async_text":       _handler_async_text,
}
