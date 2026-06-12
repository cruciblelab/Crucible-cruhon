"""
cruhon-shortcuts-pro — http group
====================================
Higher-level HTTP shortcuts built on @http.* (requests).

Global aliases (source rewrites)
─────────────────────────────────
@http_get[url]              → @http.get[url]
@http_post[url; data]       → @http.post[url; data]
@http_put[url; data]        → @http.put[url; data]
@http_delete[url]           → @http.delete[url]
@http_json[url]             → @http.json[url]
@http_status[url]           → @http.status[url]
@http_ok[url]               → @http.ok[url]

New methods (via api.lib_call) — names distinct from http_.py
───────────────────────────────────────────────────────────────
@http.retry_get[url; n]     → GET with up to n retries on failure
@http.retry_post[url; d; n] → POST with up to n retries on failure
@http.with_headers[url; h]  → GET with custom headers dict
@http.bearer[url; token]    → GET with Authorization: Bearer token
@http.basic[url; u; p]      → GET with HTTP Basic Auth
@http.json_post[url; data]  → POST JSON body, return parsed response JSON
@http.text[url]             → GET and return response.text
@http.form_post[url; data]  → POST form data (not JSON)
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@http_get[":    "@http.get[",
    "@http_post[":   "@http.post[",
    "@http_put[":    "@http.put[",
    "@http_delete[": "@http.delete[",
    "@http_json[":   "@http.json[",
    "@http_status[": "@http.status[",
    "@http_ok[":     "@http.ok[",
}

METHOD_ALIASES: dict[str, str] = {
    "@http.fetch[": "@http.get[",
    "@http.send[":  "@http.post[",
}


def _new_lib_calls(api) -> None:
    # All methods here use names NOT already in http_.py to avoid overwriting.
    api.lib_call("http", "retry_get", lambda a: (
        f"(lambda __url, __n: next("
        f"(r for _ in range(__n) for r in [requests.get(__url, timeout=30)] "
        f"if r.status_code < 500), "
        f"requests.get(__url, timeout=30)"
        f"))({a[0]}, {a[1] if len(a) > 1 else 3})"
        if a else "None"
    ))

    api.lib_call("http", "retry_post", lambda a: (
        f"(lambda __url, __d, __n: next("
        f"(r for _ in range(__n) for r in [requests.post(__url, json=__d, timeout=30)] "
        f"if r.status_code < 500), "
        f"requests.post(__url, json=__d, timeout=30)"
        f"))({a[0]}, {a[1] if len(a) > 1 else '{}'}, {a[2] if len(a) > 2 else 3})"
        if a else "None"
    ))

    api.lib_call("http", "with_headers", lambda a: (
        f"requests.get({a[0]}, headers={a[1]}, timeout=30)"
        if len(a) >= 2 else f"requests.get({a[0]}, timeout=30)" if a else "None"
    ))

    api.lib_call("http", "bearer", lambda a: (
        f"requests.get({a[0]}, headers={{'Authorization': 'Bearer ' + str({a[1]})}}, timeout=30)"
        if len(a) >= 2 else f"requests.get({a[0]}, timeout=30)" if a else "None"
    ))

    api.lib_call("http", "basic", lambda a: (
        f"requests.get({a[0]}, auth=({a[1]}, {a[2]}), timeout=30)"
        if len(a) >= 3 else f"requests.get({a[0]}, timeout=30)" if a else "None"
    ))

    api.lib_call("http", "json_post", lambda a: (
        f"requests.post({a[0]}, json={a[1]}, timeout=30).json()"
        if len(a) >= 2 else f"requests.post({a[0]}, timeout=30).json()" if a else "None"
    ))

    api.lib_call("http", "form_post", lambda a: (
        f"requests.post({a[0]}, data={a[1]}, timeout=30)"
        if len(a) >= 2 else "None"
    ))

    api.lib_call("http", "text", lambda a: (
        f"requests.get({a[0]}, timeout=30).text"
        if a else "''"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
