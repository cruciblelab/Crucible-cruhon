"""
Tests for v2.5.0 language features:
  @retry, @timeout, @macro/@call, @re.*, @yaml.*, @image.*, @pdf.*
  CLI: lint, test, bundle
  Pro plugin: regex, http, file groups
"""
import sys
import os
import pytest
from cruhon.core import parse, transpile
from cruhon.core.runner import run_source


def _t(src: str) -> str:
    """Transpile a source snippet and return the Python code."""
    return transpile(parse(src))


def _run(src: str):
    """Run a source snippet; return the exec namespace."""
    ns = {}
    code = _t(src)
    exec(compile(code, "<test>", "exec"), ns)
    return ns


def _eval(src: str):
    """Eval a single @var expression and return its value."""
    code = _t(f"@var[__r__; {src}]")
    ns = {}
    exec(compile(code, "<test>", "exec"), ns)
    return ns["__r__"]


# ─────────────────────────────────────────────────────────────
# @retry
# ─────────────────────────────────────────────────────────────

class TestRetryNode:
    def test_retry_transpiles(self):
        code = _t("@retry[3]\n    @print[hi]\n@end")
        assert "for __retry_i_" in code
        assert "range(" in code
        assert "try:" in code
        assert "break" in code
        assert "except Exception:" in code

    def test_retry_with_exc_type(self):
        code = _t("@retry[2; ValueError]\n    @print[x]\n@end")
        assert "except ValueError:" in code

    def test_retry_actually_retries(self):
        src = """\
@var[attempts; 0]
@retry[3]
    @inc[attempts]
    @if[attempts < 3]
        @raise[RuntimeError; "not yet"]
    @end
@end
"""
        ns = _run(src)
        assert ns["attempts"] == 3

    def test_retry_reraises_after_max(self):
        src = """\
@retry[2]
    @raise[ValueError; "always fails"]
@end
"""
        with pytest.raises(ValueError, match="always fails"):
            _run(src)

    def test_retry_success_on_first_try(self):
        src = """\
@var[x; 0]
@retry[5]
    @var[x; 42]
@end
"""
        ns = _run(src)
        assert ns["x"] == 42


# ─────────────────────────────────────────────────────────────
# @timeout
# ─────────────────────────────────────────────────────────────

class TestTimeoutNode:
    def test_timeout_transpiles(self):
        code = _t("@timeout[5]\n    @print[hi]\n@end")
        assert "def __timeout_fn_" in code
        assert "ThreadPoolExecutor" in code
        assert ".result(timeout=5)" in code
        assert "TimeoutError" in code

    def test_timeout_completes_fast(self):
        # @timeout body runs in its own function scope.
        # Use a mutable container to observe the result.
        src = """\
@var[_out; []]
@timeout[2]
    @raw
        _out.append(99)
    @end
@end
"""
        ns = _run(src)
        assert ns["_out"] == [99]

    def test_timeout_raises_on_slow(self):
        src = """\
@timeout[0.05]
    @raw
        import time
        time.sleep(10)
    @end
@end
"""
        with pytest.raises(TimeoutError):
            _run(src)


# ─────────────────────────────────────────────────────────────
# @macro / @call
# ─────────────────────────────────────────────────────────────

class TestMacroCallNode:
    def test_macro_transpiles(self):
        code = _t("@macro[greet; name]\n    @print[f'Hi {name}']\n@end")
        assert "def __macro_greet(name):" in code

    def test_call_transpiles(self):
        code = _t(
            "@macro[greet; name]\n    @print[f'Hi {name}']\n@end\n@call[greet; 'Bob']"
        )
        assert "__macro_greet(" in code
        assert "Bob" in code

    def test_macro_no_params(self):
        code = _t("@macro[banner]\n    @print[=====]\n@end")
        assert "def __macro_banner():" in code

    def test_macro_executes(self):
        src = """\
@macro[double; x]
    @return[x * 2]
@end
@var[result; @call[double; 5]]
"""
        ns = _run(src)
        assert ns["result"] == 10

    def test_macro_multiple_calls(self):
        src = """\
@macro[add; a; b]
    @return[a + b]
@end
@var[x; @call[add; 3; 4]]
@var[y; @call[add; 10; 20]]
"""
        ns = _run(src)
        assert ns["x"] == 7
        assert ns["y"] == 30

    def test_call_inline(self):
        src = """\
@macro[sq; n]
    @return[n * n]
@end
@var[result; @call[sq; 6]]
"""
        ns = _run(src)
        assert ns["result"] == 36

    def test_macro_side_effects(self):
        src = """\
@var[total; 0]
@macro[add_to_total; n]
    @raw
        global total
        total += n
    @end
@end
@call[add_to_total; 5]
@call[add_to_total; 3]
"""
        ns = _run(src)
        assert ns["total"] == 8


# ─────────────────────────────────────────────────────────────
# @re.*
# ─────────────────────────────────────────────────────────────

class TestReLib:
    def test_is_match_true(self):
        assert _eval('@re.is_match[r"\\d+"; "abc123"]') is True

    def test_is_match_false(self):
        assert _eval('@re.is_match[r"\\d+"; "abc"]') is False

    def test_findall(self):
        result = _eval('@re.findall[r"\\d+"; "a1 b22 c333"]')
        assert result == ["1", "22", "333"]

    def test_sub(self):
        result = _eval('@re.sub[r"\\d"; "X"; "a1b2c3"]')
        assert result == "aXbXcX"

    def test_split(self):
        result = _eval('@re.split[r"[,;]"; "a,b;c"]')
        assert result == ["a", "b", "c"]

    def test_groups(self):
        result = _eval('@re.groups[r"(\\w+)@(\\w+)"; "user@host"]')
        assert result == ("user", "host")

    def test_count(self):
        result = _eval('@re.count[r"\\d+"; "a1 b22 c3"]')
        assert result == 3

    def test_escape(self):
        result = _eval('@re.escape["a.b+c"]')
        assert "." not in result.replace("\\.", "") or result == "a\\.b\\+c"

    def test_replace_first(self):
        result = _eval('@re.replace_first[r"\\d"; "X"; "a1b2c3"]')
        assert result == "aXb2c3"

    def test_named_groups(self):
        result = _eval('@re.named[r"(?P<user>\\w+)@(?P<host>\\w+)"; "user@host"]')
        assert result.get("user") == "user"
        assert result.get("host") == "host"

    def test_no_match_groups_returns_empty(self):
        result = _eval('@re.groups[r"(\\d+)"; "abc"]')
        assert result == ()


# ─────────────────────────────────────────────────────────────
# @yaml.*  (requires pyyaml — skip if not installed)
# ─────────────────────────────────────────────────────────────

try:
    import yaml as _yaml_check
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
class TestYamlLib:
    def test_loads(self):
        result = _eval('@yaml.loads["name: Alice\\nage: 30"]')
        assert result == {"name": "Alice", "age": 30}

    def test_dumps(self):
        result = _eval('@yaml.dumps[{"key": "val"}]')
        assert "key" in result
        assert "val" in result

    def test_get(self):
        result = _eval('@yaml.get["name: Alice"; "name"]')
        assert result == "Alice"

    def test_to_json(self):
        import json
        result = _eval('@yaml.to_json["x: 1"]')
        assert json.loads(result) == {"x": 1}


# ─────────────────────────────────────────────────────────────
# Pattern matching guards (already supported — regression test)
# ─────────────────────────────────────────────────────────────

class TestMatchGuards:
    def test_case_with_guard(self):
        src = """\
@var[x; 15]
@var[label; "none"]
@match[x]
    @case[n if n > 10]
        @var[label; "big"]
    @case[n if n > 0]
        @var[label; "small"]
    @default
        @var[label; "zero"]
@end
"""
        ns = _run(src)
        assert ns["label"] == "big"

    def test_case_guard_falls_through(self):
        src = """\
@var[x; 5]
@var[label; "none"]
@match[x]
    @case[n if n > 10]
        @var[label; "big"]
    @case[n if n > 0]
        @var[label; "small"]
    @default
        @var[label; "zero"]
@end
"""
        ns = _run(src)
        assert ns["label"] == "small"


# ─────────────────────────────────────────────────────────────
# Pro plugin: regex group (unit tests via before_parse rewrite)
# ─────────────────────────────────────────────────────────────

class TestProRegexRewrites:
    def test_re_find_alias(self):
        from cruhon.core.mod_loader import load_all_mods
        load_all_mods()
        code = _t('@var[r; @re_find[r"\\d+"; "a1b2"]]')
        assert "findall" in code

    def test_re_is_match_alias(self):
        from cruhon.core.mod_loader import load_all_mods
        load_all_mods()
        code = _t('@var[r; @re_is_match[r"\\d"; "a1"]]')
        assert "re" in code.lower()


# ─────────────────────────────────────────────────────────────
# CLI: cruhon lint
# ─────────────────────────────────────────────────────────────

class TestCliLint:
    def test_lint_clean_file(self, tmp_path):
        f = tmp_path / "clean.clpy"
        f.write_text("@var[x; 42]\n@print[x]\n", encoding="utf-8")
        from cruhon.cli import _lint_file
        issues = _lint_file(f)
        assert issues == []

    def test_lint_long_line(self, tmp_path):
        f = tmp_path / "long.clpy"
        f.write_text("@var[x; " + "a" * 130 + "]\n", encoding="utf-8")
        from cruhon.cli import _lint_file
        issues = _lint_file(f)
        assert any("too long" in i for i in issues)

    def test_lint_syntax_error(self, tmp_path):
        f = tmp_path / "bad.clpy"
        # Unknown command — parse succeeds but transpile fails (or raises ParseError)
        f.write_text("@unknowncommand_xyz[x]\n", encoding="utf-8")
        from cruhon.cli import _lint_file
        issues = _lint_file(f)
        assert len(issues) > 0


# ─────────────────────────────────────────────────────────────
# CLI: cruhon bundle
# ─────────────────────────────────────────────────────────────

class TestCliBundle:
    def test_bundle_creates_file(self, tmp_path):
        src = tmp_path / "main.clpy"
        src.write_text("@var[x; 42]\n@print[x]\n", encoding="utf-8")
        out = tmp_path / "main.bundle.py"

        import types
        args = types.SimpleNamespace(file=str(src), output=str(out))
        from cruhon.cli import cmd_bundle
        cmd_bundle(args)

        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "__ctx__" in content
        assert "42" in content

    def test_bundle_is_runnable(self, tmp_path):
        src = tmp_path / "hello.clpy"
        src.write_text("@var[result; 7 * 6]\n", encoding="utf-8")
        out = tmp_path / "hello.bundle.py"

        import types
        args = types.SimpleNamespace(file=str(src), output=str(out))
        from cruhon.cli import cmd_bundle
        cmd_bundle(args)

        ns = {}
        exec(compile(out.read_text(encoding="utf-8"), str(out), "exec"), ns)
        assert ns.get("result") == 42


# ─────────────────────────────────────────────────────────────
# CLI: cruhon test
# ─────────────────────────────────────────────────────────────

class TestCliTest:
    def test_discovers_test_files(self, tmp_path):
        f = tmp_path / "my.test.clpy"
        f.write_text("@assert[1 == 1]\n", encoding="utf-8")

        import types
        args = types.SimpleNamespace(path=str(tmp_path), verbose=False)
        from cruhon.cli import cmd_test
        cmd_test(args)  # should not raise

    def test_failing_test_raises(self, tmp_path):
        f = tmp_path / "bad.test.clpy"
        f.write_text('@assert[1 == 2; "must fail"]\n', encoding="utf-8")

        import types
        args = types.SimpleNamespace(path=str(tmp_path), verbose=False)
        from cruhon.cli import cmd_test

        with pytest.raises(SystemExit):
            cmd_test(args)
