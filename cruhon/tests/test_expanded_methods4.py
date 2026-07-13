"""
Tests for wave-8 method expansions:
@asyncio, @codecs, @colorsys, @ctypes, @tokenize, @zipapp, @runpy, @pdb
"""
import pytest

from cruhon.core.transpiler import Transpiler
from cruhon.core.parser import Parser


def transpile(src):
    return Transpiler().transpile(Parser().parse(src))


def run(src, globs=None):
    g = globs or {}
    exec(compile(transpile(src), "<test>", "exec"), g)
    return g


def compiles(src):
    compile(transpile(src), "<test>", "exec")
    return True


def async_compiles(src):
    """Compile Cruhon source that contains await expressions."""
    code = transpile(src)
    # Wrap every statement in an async function so await is legal.
    wrapped = "async def _f():\n" + "\n".join("    " + l for l in code.splitlines())
    compile(wrapped, "<test>", "exec")
    return True


# ─────────────────────────────────────────────────────────────
# @asyncio — event loop and primitives
# ─────────────────────────────────────────────────────────────

class TestAsyncio:
    def test_run_simple(self):
        # asyncio.run takes a coroutine — compiles fine as a statement
        assert compiles('@asyncio.run[go()]')

    def test_sleep_compiles(self):
        # await is only legal inside async def
        assert async_compiles('@asyncio.sleep[0]')

    def test_gather_compiles(self):
        assert async_compiles('@asyncio.gather[c1; c2]')

    def test_task_compiles(self):
        assert compiles('@var[t; @asyncio.task[coro]]')

    def test_primitives_compile(self):
        assert compiles('@var[lk; @asyncio.lock[]]')
        assert compiles('@var[ev; @asyncio.event[]]')
        assert compiles('@var[sm; @asyncio.semaphore[5]]')
        assert compiles('@var[q; @asyncio.queue[]]')
        assert compiles('@var[q; @asyncio.queue[10]]')

    def test_run_actual(self):
        import asyncio
        async def _main():
            return 42
        g = run('@var[r; @asyncio.run[_main()]]', {"_main": _main})
        assert g["r"] == 42

    def test_iscoroutine(self):
        import asyncio
        async def _co():
            pass
        g = run('@var[ok; @asyncio.iscoroutine[c]]', {"c": _co()})
        assert g["ok"] is True
        g["c"].close()

    def test_new_loop(self):
        import asyncio
        g = run('@var[lp; @asyncio.new_loop[]]')
        assert isinstance(g["lp"], asyncio.AbstractEventLoop)
        g["lp"].close()

    def test_queue_maxsize(self):
        import asyncio
        g = run('@var[q; @asyncio.queue[3]]')
        assert isinstance(g["q"], asyncio.Queue)
        assert g["q"].maxsize == 3


# ─────────────────────────────────────────────────────────────
# @codecs — encode/decode
# ─────────────────────────────────────────────────────────────

class TestCodecs:
    def test_rot13(self):
        g = run('@var[s; @codecs.rot13["hello"]]')
        assert g["s"] == "uryyb"

    def test_rot13_roundtrip(self):
        g = run('@var[s; @codecs.rot13[@codecs.rot13["hello"]]]')
        assert g["s"] == "hello"

    def test_hex_encode(self):
        g = run('@var[h; @codecs.hex[b"abc"]]')
        assert g["h"] == "616263"

    def test_unhex(self):
        g = run('@var[b; @codecs.unhex[b"616263"]]')
        assert g["b"] == b"abc"

    def test_encode_decode_utf8(self):
        src = (
            '@var[b; @codecs.encode["hello"; "utf-8"]]\n'
            '@var[s; @codecs.decode[b; "utf-8"]]'
        )
        g = run(src)
        assert g["s"] == "hello"

    def test_lookup(self):
        import codecs
        g = run('@var[ci; @codecs.lookup["utf-8"]]')
        assert isinstance(g["ci"], codecs.CodecInfo)

    def test_zip_unzip(self):
        src = (
            '@var[z; @codecs.zip[b"hello world"]]\n'
            '@var[u; @codecs.unzip[z]]'
        )
        g = run(src)
        assert g["u"] == b"hello world"


# ─────────────────────────────────────────────────────────────
# @colorsys — color conversion
# ─────────────────────────────────────────────────────────────

class TestColorsys:
    def test_to_hsv(self):
        g = run('@var[hsv; @colorsys.to_hsv[1.0; 0.0; 0.0]]')
        h, s, v = g["hsv"]
        assert abs(h - 0.0) < 1e-9
        assert abs(s - 1.0) < 1e-9
        assert abs(v - 1.0) < 1e-9

    def test_from_hsv_roundtrip(self):
        src = (
            '@var[hsv; @colorsys.to_hsv[0.2; 0.4; 0.6]]\n'
            '@var[rgb; @colorsys.from_hsv[hsv[0]; hsv[1]; hsv[2]]]'
        )
        g = run(src)
        r, gr, b = g["rgb"]
        assert abs(r - 0.2) < 1e-9
        assert abs(gr - 0.4) < 1e-9
        assert abs(b - 0.6) < 1e-9

    def test_to_hls(self):
        g = run('@var[hls; @colorsys.to_hls[0.0; 1.0; 0.0]]')
        h, l, s = g["hls"]
        assert abs(h - 1/3) < 1e-9

    def test_hex_to_rgb(self):
        g = run('@var[rgb; @colorsys.hex_to_rgb["#ff0000"]]')
        r, gr, b = g["rgb"]
        assert abs(r - 1.0) < 1e-6
        assert gr < 1e-9
        assert b < 1e-9

    def test_rgb_to_hex(self):
        g = run('@var[h; @colorsys.rgb_to_hex[1.0; 0.0; 0.0]]')
        assert g["h"] == "#ff0000"

    def test_luminance(self):
        g = run('@var[lum; @colorsys.luminance[1.0; 1.0; 1.0]]')
        assert abs(g["lum"] - 1.0) < 1e-9

    def test_blend(self):
        src = (
            '@var[c1; (0.0, 0.0, 0.0)]\n'
            '@var[c2; (1.0, 1.0, 1.0)]\n'
            '@var[mid; @colorsys.blend[c1; c2; 0.5]]'
        )
        g = run(src)
        mid = list(g["mid"])
        assert all(abs(v - 0.5) < 1e-9 for v in mid)

    def test_to_yiq(self):
        g = run('@var[yiq; @colorsys.to_yiq[1.0; 0.0; 0.0]]')
        assert isinstance(g["yiq"], tuple)
        assert len(g["yiq"]) == 3


# ─────────────────────────────────────────────────────────────
# @ctypes — C types and memory
# ─────────────────────────────────────────────────────────────

class TestCtypes:
    def test_c_int(self):
        import ctypes
        g = run('@var[x; @ctypes.c_int[42]]')
        assert g["x"].value == 42

    def test_c_double(self):
        import ctypes
        g = run('@var[x; @ctypes.c_double[3.14]]')
        assert abs(g["x"].value - 3.14) < 1e-9

    def test_c_char_p(self):
        import ctypes
        g = run('@var[s; @ctypes.c_char_p[b"hi"]]')
        assert g["s"].value == b"hi"

    def test_sizeof(self):
        import ctypes
        g = run('@var[n; @ctypes.sizeof[@ctypes.c_int[]]]')
        assert g["n"] == ctypes.sizeof(ctypes.c_int)

    def test_create_buf(self):
        import ctypes
        g = run('@var[buf; @ctypes.create_buf[10]]')
        assert isinstance(g["buf"], ctypes.Array)
        assert len(g["buf"]) == 10

    def test_val(self):
        import ctypes
        g = run('@var[x; @ctypes.c_int[7]]\n@var[v; @ctypes.val[x]]')
        assert g["v"] == 7

    def test_set_val(self):
        import ctypes
        g = run(
            '@var[x; @ctypes.c_int[0]]\n'
            '@var[x; @ctypes.set_val[x; 99]]'
        )
        assert g["x"].value == 99

    def test_byref_compiles(self):
        assert compiles('@var[r; @ctypes.byref[obj]]')

    def test_pointer_type(self):
        import ctypes
        g = run('@var[pt; @ctypes.pointer_type[@ctypes.c_int[]]]')
        assert issubclass(g["pt"], ctypes._Pointer)

    def test_libc_compiles(self):
        assert compiles('@var[lib; @ctypes.libc[]]')


# ─────────────────────────────────────────────────────────────
# @tokenize — Python source tokenizer
# ─────────────────────────────────────────────────────────────

class TestTokenize:
    def test_tokens(self):
        src_py = "x = 1 + 2"
        g = run('@var[toks; @tokenize.tokens[src]]', {"src": src_py})
        assert len(g["toks"]) > 0

    def test_names(self):
        src_py = "x = foo + bar"
        g = run('@var[ns; @tokenize.names[src]]', {"src": src_py})
        strings = [t.string for t in g["ns"]]
        assert "x" in strings and "foo" in strings and "bar" in strings

    def test_numbers(self):
        src_py = "x = 42 + 3.14"
        g = run('@var[ns; @tokenize.numbers[src]]', {"src": src_py})
        strings = [t.string for t in g["ns"]]
        assert "42" in strings and "3.14" in strings

    def test_comments(self):
        src_py = "x = 1  # a comment"
        g = run('@var[cs; @tokenize.comments[src]]', {"src": src_py})
        assert len(g["cs"]) == 1
        assert "comment" in g["cs"][0].string

    def test_keywords(self):
        src_py = "if True:\n    pass\n"
        g = run('@var[ks; @tokenize.keywords[src]]', {"src": src_py})
        strings = [t.string for t in g["ks"]]
        assert "if" in strings and "pass" in strings

    def test_unique_names(self):
        src_py = "a = a + b"
        g = run('@var[us; @tokenize.unique_names[src]]', {"src": src_py})
        assert "a" in g["us"] and "b" in g["us"]
        assert g["us"] == sorted(set(g["us"]))

    def test_count(self):
        src_py = "x = 1"
        g = run('@var[n; @tokenize.count[src]]', {"src": src_py})
        assert g["n"] > 0

    def test_type_constants(self):
        import tokenize
        g = run(
            '@var[tn; @tokenize.NAME[]]\n'
            '@var[to; @tokenize.OP[]]'
        )
        assert g["tn"] == tokenize.NAME
        assert g["to"] == tokenize.OP

    def test_tok_name(self):
        import tokenize
        g = run('@var[n; @tokenize.tok_name[@tokenize.NAME[]]]')
        assert g["n"] == "NAME"

    def test_token_fields(self):
        src_py = "x = 1"
        g = run(
            '@var[toks; @tokenize.tokens[src]]\n'
            '@var[t; toks[0]]\n'
            '@var[tp; @tokenize.type[t]]\n'
            '@var[ts; @tokenize.string[t]]\n'
            '@var[st; @tokenize.start[t]]',
            {"src": src_py}
        )
        assert isinstance(g["tp"], int)
        assert isinstance(g["ts"], str)
        assert isinstance(g["st"], tuple)


# ─────────────────────────────────────────────────────────────
# @zipapp — ZIP application archives
# ─────────────────────────────────────────────────────────────

class TestZipapp:
    def test_create(self, tmp_path):
        app = tmp_path / "myapp"
        app.mkdir()
        (app / "__main__.py").write_text('print("hello")\n')
        target = tmp_path / "myapp.pyz"
        run('@zipapp.create[src; tgt]', {"src": str(app), "tgt": str(target)})
        assert target.exists()

    def test_is_archive(self, tmp_path):
        app = tmp_path / "app"
        app.mkdir()
        (app / "__main__.py").write_text('pass\n')
        target = tmp_path / "app.pyz"
        run('@zipapp.create[src; tgt]', {"src": str(app), "tgt": str(target)})
        g = run('@var[ok; @zipapp.is_archive[tgt]]', {"tgt": str(target)})
        assert g["ok"] is True

    def test_interpreter(self, tmp_path):
        app = tmp_path / "app2"
        app.mkdir()
        (app / "__main__.py").write_text('pass\n')
        target = tmp_path / "app2.pyz"
        import sys
        interp = sys.executable
        run(
            '@zipapp.create[src; tgt; None; interp]',
            {"src": str(app), "tgt": str(target), "interp": interp}
        )
        g = run('@var[i; @zipapp.interpreter[tgt]]', {"tgt": str(target)})
        assert g["i"] == interp

    def test_is_archive_false(self, tmp_path):
        f = tmp_path / "plain.txt"
        f.write_text("not a zip")
        g = run('@var[ok; @zipapp.is_archive[p]]', {"p": str(f)})
        assert g["ok"] is False


# ─────────────────────────────────────────────────────────────
# @runpy — dynamic module/path execution
# ─────────────────────────────────────────────────────────────

class TestRunpy:
    def test_module_ns(self):
        # Not os.path: on Python 3.10, os.path is an alias for posixpath/
        # ntpath, and runpy.run_module("os.path") raises "loader for
        # posixpath cannot handle os.path" — a real CPython 3.10 quirk,
        # not a Cruhon bug. urllib.parse is a plain dotted submodule with
        # no such aliasing and exercises the same "dotted module name"
        # code path.
        g = run('@var[ns; @runpy.module_ns["urllib.parse"]]')
        assert isinstance(g["ns"], dict)
        assert "__spec__" in g["ns"] or "__name__" in g["ns"]

    def test_is_module_true(self):
        g = run('@var[ok; @runpy.is_module["os"]]')
        assert g["ok"] is True

    def test_is_module_false(self):
        g = run('@var[ok; @runpy.is_module["_nonexistent_cruhon_xyz"]]')
        assert g["ok"] is False

    def test_path_ns(self, tmp_path):
        script = tmp_path / "demo.py"
        script.write_text('result = 2 + 2\n')
        g = run('@var[ns; @runpy.path_ns[p]]', {"p": str(script)})
        assert g["ns"]["result"] == 4

    def test_find_module(self):
        import importlib
        g = run('@var[spec; @runpy.find["sys"]]')
        assert g["spec"] is not None

    def test_result(self):
        g = run('@var[ns; {"x": 42}]\n@var[v; @runpy.result[ns; "x"]]')
        assert g["v"] == 42


# ─────────────────────────────────────────────────────────────
# @pdb — debugger (compile-only for interactive commands)
# ─────────────────────────────────────────────────────────────

class TestPdb:
    def test_bp_compiles(self):
        assert compiles('@pdb.bp[]')

    def test_breakpoint_compiles(self):
        assert compiles('@pdb.breakpoint[]')

    def test_pm_compiles(self):
        assert compiles('@pdb.pm[]')
        assert compiles('@pdb.pm[tb]')

    def test_run_compiles(self):
        assert compiles('@pdb.run["pass"]')

    def test_runeval_compiles(self):
        assert compiles('@pdb.runeval["1+1"]')

    def test_new(self):
        import pdb
        g = run('@var[d; @pdb.new[]]')
        assert isinstance(g["d"], pdb.Pdb)

    def test_set_clear_bp_compile(self):
        assert compiles('@pdb.set_bp[dbg; "file.py"; 10]')
        assert compiles('@pdb.clear_bp[dbg; "file.py"; 10]')
        assert compiles('@pdb.clear_all[dbg]')
        assert compiles('@pdb.list_bps[dbg]')
