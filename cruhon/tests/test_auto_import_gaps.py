"""
Regression tests for a critical bug: @http.*/@requests.*, @json.load/dump,
and @os.env/@os.path emitted bare `requests.get(...)` / `json.dumps(...)` /
`os.environ...` — relying on an "auto-import" mechanism that never actually
covered these namespaces — so executing ANY of them raised
NameError: name 'requests'/'json'/'os' is not defined.

No existing test caught this because every prior HTTP test either only
checked the generated CODE STRING (never executed it) or manually injected
a pre-fetched requests.Response object into the exec globals, bypassing
the actual `requests.get(...)` call path entirely.

@http.* is the language's most prominently documented feature (the
README's very first non-trivial example) — this was broken for every real
user attempting to run that example.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core.runner import run_source


class TestHttpAutoImport:
    def test_inline_get_executes(self):
        """@var[r; @http.get[...]] — the overwhelmingly common inline
        usage pattern — must not raise NameError: name 'requests'."""
        g = _run('@var[r; @http.get["https://httpbin.org/get"]]\n'
                  '@var[s; @http.status[r]]\n'
                  '@var[ok; @http.ok[r]]')
        assert g["s"] == 200
        assert g["ok"] is True

    def test_bare_statement_executes(self):
        """@http.get[...] as a bare top-level statement (not inside @var)."""
        _run('@http.get["https://httpbin.org/get"]')

    def test_post_executes(self):
        g = _run('@var[r; @http.post["https://httpbin.org/post"; {"a": 1}]]\n'
                  '@var[s; @http.status[r]]')
        assert g["s"] == 200

    def test_json_body_roundtrips(self):
        g = _run('@var[r; @http.get["https://httpbin.org/get"]]\n'
                  '@var[body; @http.json[r]]')
        assert isinstance(g["body"], dict)


class TestJsonAutoImport:
    def test_dump_executes(self):
        g = _run('@var[d; {"a": 1, "b": [1, 2, 3]}]\n'
                  '@var[s; @json.dump[d]]')
        assert '"a"' in g["s"] and '"b"' in g["s"]

    def test_load_executes(self):
        g = _run('@var[d; @json.load["{\\"x\\": 42}"]]')
        assert g["d"] == {"x": 42}


class TestOsAutoImport:
    def test_env_executes(self):
        g = _run('@var[h; @os.env["HOME"]]')
        # Just must not raise NameError — value depends on the environment.
        assert "h" in g

    def test_path_executes(self):
        g = _run('@var[p; @os.path["a"; "b"; "c.txt"]]')
        assert g["p"].endswith("c.txt")


def _run(src):
    import io
    import contextlib
    g_holder = {}

    # run_source() builds its own fresh globals internally and doesn't
    # hand them back, so capture via a tiny wrapper around exec by
    # re-parsing + transpiling + exec'ing with our own globals dict —
    # matching exactly what run_source() does, but exposing the result.
    from cruhon.core.parser import parse
    from cruhon.core.transpiler import transpile
    from cruhon.core.mod_loader import get_inject_globals

    code = transpile(parse(src))
    g = {"__name__": "__main__", "__ns__": {}, "__ctx__": {}, "__ctx_stack__": []}
    for k, v in get_inject_globals().items():
        if k not in g:
            g[k] = v
    exec(compile(code, "<test>", "exec"), g)
    return g
