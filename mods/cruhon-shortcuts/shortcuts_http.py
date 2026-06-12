"""
cruhon-shortcuts — http group
==============================
Shortcuts for @http.* operations.

Global aliases (source rewrites)
─────────────────────────────────
@get[url]               → @http.get[url]
@post[url; data]        → @http.post[url; data]
@put[url; data]         → @http.put[url; data]
@patch[url; data]       → @http.patch[url; data]
@http_delete[url]       → @http.delete[url]
@fetch[url]             → @http.get[url]
@download[url; path]    → @http.download[url; path]
@upload[url; path]      → @http.upload[url; path]
@http_head[url]         → @http.head[url]
@http_options[url]      → @http.options[url]
@http_form[url; data]   → @http.form[url; data]
@async_get[url]         → @http.async_get[url]
@async_post[url; data]  → @http.async_post[url; data]

Namespace method aliases
─────────────────────────
@http.fetch[url]         → @http.get[url]
@http.request[url]       → @http.get[url]
@http.download_to[u; p]  → @http.download[u; p]

New methods (via api.lib_call)
───────────────────────────────
@http.fetch_json[url]           → GET + .json() in one call
@http.fetch_json[url; headers=] → with extra headers
@http.fetch_text[url]           → GET + .text in one call
@http.is_ok[res]                → res.status_code < 400  (bool)
@http.status_code[res]          → alias for @http.status[res]
@http.response_url[res]         → alias for @http.url[res]
@http.content_type[res]         → Content-Type header value
@http.elapsed_ms[res]           → response time in milliseconds (float)
@http.raise_on_error[res]       → alias for @http.raise_for_status[res]
@http.to_file[res; path]        → write response bytes to file
@http.base_url[url]             → scheme + netloc only
@http.add_params[url; params]   → append query-string dict to URL
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@get[":          "@http.get[",
    "@post[":         "@http.post[",
    "@put[":          "@http.put[",
    "@patch[":        "@http.patch[",
    "@http_delete[":  "@http.delete[",
    # @fetch is a core Cruhon built-in — use @http_fetch instead
    "@http_fetch[":   "@http.get[",
    "@download[":     "@http.download[",
    "@upload[":       "@http.upload[",
    "@http_head[":    "@http.head[",
    "@http_options[": "@http.options[",
    "@http_form[":    "@http.form[",
    "@async_get[":    "@http.async_get[",
    "@async_post[":   "@http.async_post[",
}

METHOD_ALIASES: dict[str, str] = {
    "@http.fetch[":       "@http.get[",
    "@http.request[":     "@http.get[",
    "@http.download_to[": "@http.download[",
}

_REQ = "__import__('requests')"
_UP  = "__import__('urllib.parse', fromlist=['urlencode', 'urlparse', 'urlunparse'])"


def _new_lib_calls(api) -> None:

    api.lib_call("http", "fetch_json", lambda a: (
        f"{_REQ}.get({a[0]}, headers={a[1]}, timeout=30).json()"
        if len(a) > 1 else
        f"{_REQ}.get({a[0]}, timeout=30).json()"
    ))

    api.lib_call("http", "fetch_text", lambda a: (
        f"{_REQ}.get({a[0]}, timeout=30).text"
    ))

    api.lib_call("http", "is_ok", lambda a: (
        f"({a[0]}.status_code < 400)"
    ))

    api.lib_call("http", "status_code", lambda a: (
        f"{a[0]}.status_code"
    ))

    api.lib_call("http", "response_url", lambda a: (
        f"{a[0]}.url"
    ))

    api.lib_call("http", "content_type", lambda a: (
        f"{a[0]}.headers.get('Content-Type', '')"
    ))

    api.lib_call("http", "elapsed_ms", lambda a: (
        f"{a[0]}.elapsed.total_seconds() * 1000"
    ))

    api.lib_call("http", "raise_on_error", lambda a: (
        f"(lambda _r: (_r.raise_for_status(), _r)[1])({a[0]})"
    ))

    api.lib_call("http", "to_file", lambda a: (
        f"open({a[1]}, 'wb').write({a[0]}.content)"
        if len(a) > 1 else
        f"None"
    ))

    api.lib_call("http", "base_url", lambda a: (
        f"(lambda _u: _u.scheme + '://' + _u.netloc)"
        f"({_UP}.urlparse({a[0]}))"
    ))

    api.lib_call("http", "add_params", lambda a: (
        f"(lambda _u, _p: _u + ('&' if '?' in _u else '?') + "
        f"{_UP}.urlencode(_p))({a[0]}, {a[1]})"
        if len(a) > 1 else
        f"{a[0]}"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
