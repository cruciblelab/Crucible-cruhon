"""
Tests for the v2.8.0 method expansions — the additional methods added so
that everything is doable in Cruhon without @raw.
"""
import socket as _socket
import threading

import pytest

from cruhon.core.transpiler import Transpiler
from cruhon.core.parser import Parser


def transpile(src):
    return Transpiler().transpile(Parser().parse(src))


def run(src, globs=None):
    g = globs or {}
    exec(compile(transpile(src), "<test>", "exec"), g)
    return g


def _square(x):
    return x * x


# ─────────────────────────────────────────────────────────────
# @array — mutation
# ─────────────────────────────────────────────────────────────

class TestArrayExpanded:
    def test_append(self):
        g = run('@var[a; @array.append[@array.of["i"; [1, 2]]; 3]]')
        assert list(g["a"]) == [1, 2, 3]

    def test_extend(self):
        g = run('@var[a; @array.extend[@array.of["i"; [1]]; [2, 3]]]')
        assert list(g["a"]) == [1, 2, 3]

    def test_insert(self):
        g = run('@var[a; @array.insert[@array.of["i"; [1, 3]]; 1; 2]]')
        assert list(g["a"]) == [1, 2, 3]

    def test_pop(self):
        g = run('@var[x; @array.pop[@array.of["i"; [1, 2, 3]]]]')
        assert g["x"] == 3

    def test_remove(self):
        g = run('@var[a; @array.remove[@array.of["i"; [1, 2, 3]]; 2]]')
        assert list(g["a"]) == [1, 3]

    def test_set(self):
        g = run('@var[a; @array.set[@array.of["i"; [1, 2, 3]]; 0; 9]]')
        assert list(g["a"]) == [9, 2, 3]

    def test_reverse(self):
        g = run('@var[a; @array.reverse[@array.of["i"; [1, 2, 3]]]]')
        assert list(g["a"]) == [3, 2, 1]

    def test_index(self):
        g = run('@var[i; @array.index[@array.of["i"; [5, 6, 7]]; 6]]')
        assert g["i"] == 1

    def test_count_of(self):
        g = run('@var[n; @array.count_of[@array.of["i"; [1, 1, 2]]; 1]]')
        assert g["n"] == 2

    def test_get(self):
        g = run('@var[x; @array.get[@array.of["i"; [4, 5, 6]]; 2]]')
        assert g["x"] == 6

    def test_slice(self):
        g = run('@var[a; @array.slice[@array.of["i"; [1, 2, 3, 4]]; 1; 3]]')
        assert list(g["a"]) == [2, 3]

    def test_concat(self):
        g = run('@var[a; @array.concat[@array.of["i"; [1]]; @array.of["i"; [2]]]]')
        assert list(g["a"]) == [1, 2]

    def test_file_roundtrip(self, tmp_path):
        p = tmp_path / "arr.bin"
        run(f'@array.to_file[@array.of["i"; [7, 8, 9]]; "{p}"]')
        g = run(f'@var[a; @array.from_file["i"; "{p}"; 3]]')
        assert list(g["a"]) == [7, 8, 9]


# ─────────────────────────────────────────────────────────────
# @socket — server / UDP
# ─────────────────────────────────────────────────────────────

class TestSocketExpanded:
    def test_server_accept_loopback(self):
        g = run('@var[srv; @socket.server["127.0.0.1"; 0]]')
        srv = g["srv"]
        port = srv.getsockname()[1]
        received = {}

        def serve():
            conn, _ = srv.accept()
            received["data"] = conn.recv(64)
            conn.close()

        t = threading.Thread(target=serve)
        t.start()
        client = _socket.create_connection(("127.0.0.1", port))
        client.sendall(b"hello server")
        t.join()
        client.close()
        srv.close()
        assert received["data"] == b"hello server"

    def test_udp_roundtrip(self):
        g = run('@var[s; @socket.udp[]]')
        srv = g["s"]
        srv.bind(("127.0.0.1", 0))
        port = srv.getsockname()[1]
        cli = run('@var[c; @socket.udp[]]')["c"]
        run(f'@socket.send_to[c; b"ping"; "127.0.0.1"; {port}]', {"c": cli})
        g2 = run('@var[r; @socket.recv_from[s; 64]]', {"s": srv})
        srv.close()
        cli.close()
        assert g2["r"][0] == b"ping"

    def test_tcp_unconnected(self):
        g = run('@var[s; @socket.tcp[]]')
        assert g["s"].type == _socket.SOCK_STREAM
        g["s"].close()

    def test_local(self):
        s = _socket.socket()
        s.bind(("127.0.0.1", 0))
        g = run('@var[a; @socket.local[s]]', {"s": s})
        assert g["a"][0] == "127.0.0.1"
        s.close()

    def test_reuse(self):
        s = _socket.socket()
        run('@socket.reuse[s]', {"s": s})
        assert s.getsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR) == 1
        s.close()


# ─────────────────────────────────────────────────────────────
# @multiprocessing / @futures — expanded
# ─────────────────────────────────────────────────────────────

class TestConcurrencyExpanded:
    def test_mp_apply(self):
        g = run('@var[r; @multiprocessing.apply[fn; (6,)]]', {"fn": _square})
        assert g["r"] == 36

    def test_mp_imap(self):
        g = run('@var[r; @multiprocessing.imap[fn; [1, 2, 3]]]', {"fn": _square})
        assert g["r"] == [1, 4, 9]

    def test_mp_pipe(self):
        g = run('@var[p; @multiprocessing.pipe[]]')
        a, b = g["p"]
        a.send("hi")
        assert b.recv() == "hi"

    def test_mp_event(self):
        import multiprocessing
        g = run('@var[e; @multiprocessing.event[]]')
        assert isinstance(g["e"], type(multiprocessing.Event()))

    def test_mp_start_join(self):
        import multiprocessing
        src = (
            '@var[p; @multiprocessing.process[fn; (1,)]]\n'
            '@multiprocessing.start[p]\n'
            '@multiprocessing.join[p]\n'
            '@var[code; p.exitcode]'
        )
        g = run(src, {"fn": _square})
        assert g["code"] == 0

    def test_futures_map(self):
        src = (
            '@var[ex; @futures.threads[2]]\n'
            '@var[r; @futures.map[ex; fn; [1, 2, 3]]]\n'
            '@futures.shutdown[ex]'
        )
        g = run(src, {"fn": _square})
        assert g["r"] == [1, 4, 9]

    def test_futures_exception(self):
        def boom():
            raise ValueError("x")
        src = (
            '@var[ex; @futures.threads[1]]\n'
            '@var[f; @futures.submit[ex; fn; ()]]\n'
            '@var[e; @futures.exception[f]]\n'
            '@futures.shutdown[ex]'
        )
        g = run(src, {"fn": boom})
        assert isinstance(g["e"], ValueError)

    def test_futures_as_done(self):
        src = (
            '@var[ex; @futures.threads[2]]\n'
            '@var[f1; @futures.submit[ex; fn; (1,)]]\n'
            '@var[f2; @futures.submit[ex; fn; (2,)]]\n'
            '@var[done; @futures.as_done[[f1, f2]]]\n'
            '@futures.shutdown[ex]'
        )
        g = run(src, {"fn": _square})
        assert len(g["done"]) == 2

    def test_futures_on_done(self):
        seen = []
        src = (
            '@var[ex; @futures.threads[1]]\n'
            '@var[f; @futures.submit[ex; fn; (3,)]]\n'
            '@futures.on_done[f; cb]\n'
            '@var[r; @futures.result[f]]\n'
            '@futures.shutdown[ex]'
        )
        run(src, {"fn": _square, "cb": lambda fut: seen.append(fut.result())})
        assert seen == [9]


# ─────────────────────────────────────────────────────────────
# @ast / @inspect / @types / @importlib / @dis — expanded
# ─────────────────────────────────────────────────────────────

class TestDevExpanded:
    def test_ast_functions(self):
        g = run('@var[f; @ast.functions["def foo():\\n    pass\\ndef bar():\\n    pass"]]')
        assert set(g["f"]) == {"foo", "bar"}

    def test_ast_imports(self):
        g = run('@var[i; @ast.imports["import os\\nimport sys"]]')
        assert "os" in g["i"] and "sys" in g["i"]

    def test_ast_is_valid_true(self):
        g = run('@var[b; @ast.is_valid["x = 1"]]')
        assert g["b"] is True

    def test_ast_is_valid_false(self):
        g = run('@var[b; @ast.is_valid["def ("]]')
        assert g["b"] is False

    def test_ast_docstring(self):
        g = run('@var[d; @ast.docstring[code]]', {"code": '"""hi"""\nx = 1'})
        assert g["d"] == "hi"

    def test_ast_constants(self):
        g = run('@var[c; @ast.constants["x = 1 + 2"]]')
        assert 1 in g["c"] and 2 in g["c"]

    def test_inspect_source_file(self):
        import textwrap as _tw
        g = run('@var[p; @inspect.source_file[fn]]', {"fn": _tw.shorten})
        assert g["p"] is not None and "textwrap" in g["p"]

    def test_inspect_defaults(self):
        def f(a, b=5, c=10):
            return a
        g = run('@var[d; @inspect.defaults[fn]]', {"fn": f})
        assert g["d"] == {"b": 5, "c": 10}

    def test_inspect_is_abstract(self):
        from collections.abc import Mapping
        g = run('@var[b; @inspect.is_abstract[c]]', {"c": Mapping})
        assert g["b"] is True

    def test_types_module(self):
        import types
        g = run('@var[m; @types.module["mymod"]]')
        assert isinstance(g["m"], types.ModuleType) and g["m"].__name__ == "mymod"

    def test_types_is_code(self):
        g = run('@var[b; @types.is_code[c]]', {"c": (lambda: 1).__code__})
        assert g["b"] is True

    def test_importlib_exists_true(self):
        g = run('@var[b; @importlib.exists["json"]]')
        assert g["b"] is True

    def test_importlib_exists_false(self):
        g = run('@var[b; @importlib.exists["no_such_module_xyz"]]')
        assert g["b"] is False

    def test_importlib_from_path(self, tmp_path):
        mod = tmp_path / "mymod.py"
        mod.write_text("VALUE = 42\n")
        g = run(f'@var[m; @importlib.from_path["mymod"; "{mod}"]]')
        assert g["m"].VALUE == 42

    def test_dis_varnames(self):
        def f(a, b):
            c = a + b
            return c
        g = run('@var[v; @dis.varnames[fn]]', {"fn": f})
        assert "a" in g["v"] and "c" in g["v"]

    def test_dis_stack_size(self):
        g = run('@var[s; @dis.stack_size[fn]]', {"fn": _square})
        assert isinstance(g["s"], int) and g["s"] >= 1

    def test_dis_code_info(self):
        g = run('@var[i; @dis.code_info[fn]]', {"fn": _square})
        assert isinstance(g["i"], str) and "Name" in g["i"]


# ─────────────────────────────────────────────────────────────
# @shutil / @filecmp / @configparser / @linecache — expanded
# ─────────────────────────────────────────────────────────────

class TestFileExpanded:
    def test_shutil_terminal_size(self):
        g = run('@var[s; @shutil.terminal_size[]]')
        assert isinstance(g["s"], tuple) and len(g["s"]) == 2

    def test_shutil_archive_formats(self):
        g = run('@var[f; @shutil.archive_formats[]]')
        assert isinstance(g["f"], list) and len(g["f"]) > 0

    def test_shutil_copy_mode(self, tmp_path):
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("x"); b.write_text("y")
        a.chmod(0o600)
        run(f'@shutil.copy_mode["{a}"; "{b}"]')
        assert (b.stat().st_mode & 0o777) == 0o600

    def test_filecmp_compare(self, tmp_path):
        d1, d2 = tmp_path / "d1", tmp_path / "d2"
        d1.mkdir(); d2.mkdir()
        (d1 / "same.txt").write_text("hi")
        (d2 / "same.txt").write_text("hi")
        (d1 / "diff.txt").write_text("a")
        (d2 / "diff.txt").write_text("b")
        g = run(f'@var[r; @filecmp.compare["{d1}"; "{d2}"; ["same.txt", "diff.txt"]]]')
        match, mismatch, errors = g["r"]
        assert match == ["same.txt"] and mismatch == ["diff.txt"]

    def test_filecmp_common(self, tmp_path):
        d1, d2 = tmp_path / "d1", tmp_path / "d2"
        d1.mkdir(); d2.mkdir()
        (d1 / "x.txt").write_text("a")
        (d2 / "x.txt").write_text("b")
        g = run(f'@var[c; @filecmp.common["{d1}"; "{d2}"]]')
        assert "x.txt" in g["c"]

    def test_configparser_to_dict(self):
        import textwrap
        ini = textwrap.dedent("""\
            [a]
            x = 1
            [b]
            y = 2
        """)
        g = run('@var[c; @configparser.loads[ini]]\n@var[d; @configparser.to_dict[c]]',
                {"ini": ini})
        assert g["d"] == {"a": {"x": "1"}, "b": {"y": "2"}}

    def test_configparser_remove_section(self):
        import textwrap
        ini = "[a]\nx = 1\n[b]\ny = 2\n"
        src = (
            '@var[c; @configparser.loads[ini]]\n'
            '@configparser.remove_section[c; "a"]\n'
            '@var[s; @configparser.sections[c]]'
        )
        g = run(src, {"ini": ini})
        assert g["s"] == ["b"]

    def test_configparser_read_dict(self):
        src = (
            '@var[c; @configparser.new[]]\n'
            '@configparser.read_dict[c; {"sec": {"k": "v"}}]\n'
            '@var[v; @configparser.get[c; "sec"; "k"]]'
        )
        g = run(src)
        assert g["v"] == "v"

    def test_linecache_count(self, tmp_path):
        p = tmp_path / "f.txt"
        p.write_text("a\nb\nc\n")
        g = run(f'@var[n; @linecache.count["{p}"]]')
        assert g["n"] == 3


# ─────────────────────────────────────────────────────────────
# @cmath — inverse hyperbolics
# ─────────────────────────────────────────────────────────────

class TestCmathExpanded:
    def test_asinh(self):
        import cmath
        g = run('@var[z; @cmath.asinh[@cmath.complex[0; 0]]]')
        assert g["z"] == complex(0, 0)

    def test_acosh(self):
        g = run('@var[z; @cmath.acosh[1]]')
        assert abs(g["z"].real) < 1e-9

    def test_atanh(self):
        g = run('@var[z; @cmath.atanh[0]]')
        assert g["z"] == complex(0, 0)
