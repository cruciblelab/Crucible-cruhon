"""
Core test suite for Cruhon.

Covers: parser, transpiler, runner, stdlib, semantics, include, async, raw.
"""
import sys
import os
import tempfile
import textwrap
from pathlib import Path

import pytest

# Make the package importable regardless of install state
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core.parser import parse, ParseError
from cruhon.core.transpiler import transpile, TranspileError
from cruhon.core.runner import run_source, run_file, RunError, resolve_includes
from cruhon.core.lexer import tokenize
from cruhon.core.ast_nodes import (
    VarNode, PrintNode, InputNode, IfNode, ForNode, WhileNode,
    FuncNode, ReturnNode, BreakNode, ContinueNode, TryNode,
    AssertNode, RepeatNode, RawNode, FetchNode, ImportNode,
)


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def _transpile(source: str) -> str:
    """Parse + transpile, return generated Python."""
    return transpile(parse(source))


def _run(source: str, capsys=None) -> str:
    """Run source, return generated Python."""
    return run_source(source)


# ─────────────────────────────────────────────────────────────
# LEXER
# ─────────────────────────────────────────────────────────────

class TestLexer:
    def test_at_cmd_token(self):
        tokens = tokenize("@print[hello]")
        types = [t.type for t in tokens]
        assert "AT_CMD" in types
        assert "LBRACKET" in types
        assert "RBRACKET" in types

    def test_namespace_token(self):
        tokens = tokenize("@math.sqrt[16]")
        types = [t.type for t in tokens]
        assert "NAMESPACE" in types
        assert "DOT" in types

    def test_comment_token(self):
        tokens = tokenize("# this is a comment\n@print[hi]")
        types = [t.type for t in tokens]
        assert "COMMENT" in types

    def test_string_token(self):
        tokens = tokenize('@var[x; "hello"]')
        string_tokens = [t for t in tokens if t.type == "STRING"]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "hello"

    def test_number_token(self):
        tokens = tokenize("@var[n; 42]")
        number_tokens = [t for t in tokens if t.type == "NUMBER"]
        assert len(number_tokens) == 1
        assert number_tokens[0].value == "42"

    def test_indent_dedent(self):
        source = "@if[True]\n    @print[yes]\n@end"
        tokens = tokenize(source)
        types = [t.type for t in tokens]
        assert "INDENT" in types
        assert "DEDENT" in types


# ─────────────────────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────────────────────

class TestParser:
    def test_parse_print(self):
        ast = parse("@print[hello]")
        assert len(ast.body) == 1
        assert isinstance(ast.body[0], PrintNode)
        assert ast.body[0].value == "hello"

    def test_parse_var(self):
        ast = parse("@var[x; 42]")
        node = ast.body[0]
        assert isinstance(node, VarNode)
        assert node.name == "x"
        assert node.value == "42"

    def test_parse_input(self):
        ast = parse("@input[Enter your name: ]")
        node = ast.body[0]
        assert isinstance(node, InputNode)
        assert "Enter" in node.prompt

    def test_parse_input_no_prompt(self):
        ast = parse("@input[]")
        node = ast.body[0]
        assert isinstance(node, InputNode)

    def test_parse_if(self):
        ast = parse("@if[x > 0]\n    @print[yes]\n@end")
        node = ast.body[0]
        assert isinstance(node, IfNode)
        assert node.condition == "x > 0"

    def test_parse_for(self):
        ast = parse("@for[i; range(3)]\n    @print[i]\n@end")
        node = ast.body[0]
        assert isinstance(node, ForNode)
        assert node.var == "i"

    def test_parse_while(self):
        ast = parse("@while[x > 0]\n    @print[x]\n@end")
        node = ast.body[0]
        assert isinstance(node, WhileNode)

    def test_parse_func(self):
        ast = parse("@func[greet; name]\n    @print[hello]\n@end")
        node = ast.body[0]
        assert isinstance(node, FuncNode)
        assert node.name == "greet"
        assert "name" in node.params

    def test_parse_return(self):
        ast = parse("@func[f]\n    @return[42]\n@end")
        func_node = ast.body[0]
        ret_node = func_node.body[0]
        assert isinstance(ret_node, ReturnNode)

    def test_parse_break_continue(self):
        src = "@for[i; range(3)]\n    @break\n    @continue\n@end"
        ast = parse(src)
        body = ast.body[0].body
        assert isinstance(body[0], BreakNode)
        assert isinstance(body[1], ContinueNode)

    def test_parse_try_catch(self):
        src = "@try\n    @print[ok]\n@catch[e]\n    @print[err]\n@end"
        ast = parse(src)
        node = ast.body[0]
        assert isinstance(node, TryNode)
        assert node.catch_var == "e"

    def test_parse_assert(self):
        ast = parse('@assert[x > 0; "must be positive"]')
        node = ast.body[0]
        assert isinstance(node, AssertNode)

    def test_parse_repeat(self):
        ast = parse("@repeat[5]\n    @print[hi]\n@end")
        node = ast.body[0]
        assert isinstance(node, RepeatNode)
        assert node.count == "5"

    def test_parse_unknown_command_raises(self):
        with pytest.raises(ParseError):
            parse("@nonexistent[arg]")

    def test_parse_var_missing_value_raises(self):
        with pytest.raises(ParseError):
            parse("@var[x]")

    def test_parse_unknown_inline_raises(self):
        with pytest.raises(ParseError):
            parse("@var[x; @nonexistent[arg]]")

    def test_parse_dict_odd_args_raises(self):
        with pytest.raises(ParseError):
            parse("@var[d; @dict[k1; v1; k3]]")

    def test_parse_raw_block(self):
        src = "@raw\n    x = 1 + 1\n@end"
        ast = parse(src)
        node = ast.body[0]
        assert isinstance(node, RawNode)
        assert "x = 1 + 1" in node.code

    def test_parse_fetch(self):
        ast = parse('@fetch["https://example.com"]')
        node = ast.body[0]
        assert isinstance(node, FetchNode)

    def test_parse_import(self):
        ast = parse("@import[requests]")
        node = ast.body[0]
        assert isinstance(node, ImportNode)
        assert node.lib == "requests"

    def test_parse_import_alias(self):
        ast = parse("@import[requests; req]")
        node = ast.body[0]
        assert node.alias == "req"

    def test_parse_inline_env(self):
        ast = parse("@var[val; @env[HOME]]")
        node = ast.body[0]
        assert isinstance(node, VarNode)
        assert "os.environ" in node.value

    def test_parse_inline_list(self):
        ast = parse("@var[lst; @list[1; 2; 3]]")
        node = ast.body[0]
        assert "[1, 2, 3]" in node.value

    def test_parse_inline_dict(self):
        ast = parse("@var[d; @dict[k; v]]")
        node = ast.body[0]
        assert "k" in node.value and "v" in node.value


# ─────────────────────────────────────────────────────────────
# TRANSPILER
# ─────────────────────────────────────────────────────────────

class TestTranspiler:
    def test_print_bare_text(self):
        code = _transpile("@print[hello world]")
        assert 'print("hello world")' in code

    def test_print_fstring(self):
        code = _transpile("@print[Hello, {name}!]")
        assert 'f"Hello, {name}!"' in code

    def test_var_number(self):
        code = _transpile("@var[x; 42]")
        assert "x = 42" in code

    def test_var_string(self):
        code = _transpile('@var[msg; "hello"]')
        assert 'msg = "hello"' in code

    def test_var_expression(self):
        code = _transpile("@var[result; a + b]")
        assert "result = a + b" in code

    def test_var_fstring(self):
        code = _transpile("@var[msg; Hello {name}]")
        assert 'msg = f"Hello {name}"' in code

    def test_input_with_prompt(self):
        code = _transpile("@input[Enter name: ]")
        assert "input(" in code
        assert "Enter name:" in code

    def test_input_no_prompt(self):
        code = _transpile("@input[]")
        assert "input(" in code

    def test_const(self):
        code = _transpile("@const[MAX; 100]")
        assert "MAX = 100" in code
        assert "# const" in code

    def test_if_else(self):
        src = "@if[x > 0]\n    @print[pos]\n@else\n    @print[neg]\n@end"
        code = _transpile(src)
        assert "if x > 0:" in code
        assert "else:" in code

    def test_elif(self):
        src = "@if[x > 0]\n    @print[pos]\n@elif[x == 0]\n    @print[zero]\n@end"
        code = _transpile(src)
        assert "elif x == 0:" in code

    def test_for_loop(self):
        code = _transpile("@for[i; range(3)]\n    @print[i]\n@end")
        assert "for i in range(3):" in code

    def test_while_loop(self):
        code = _transpile("@while[x > 0]\n    @print[x]\n@end")
        assert "while x > 0:" in code

    def test_repeat_loop(self):
        code = _transpile("@repeat[5]\n    @print[hi]\n@end")
        assert "for _ in range(5):" in code

    def test_func_def(self):
        code = _transpile("@func[add; a; b]\n    @return[a + b]\n@end")
        assert "def add(a, b):" in code
        assert "return a + b" in code

    def test_async_func(self):
        code = _transpile("@async[main]\n    @print[ok]\n@end")
        assert "async def main():" in code

    def test_class_def(self):
        code = _transpile("@class[Animal]\n    @print[created]\n@end")
        assert "class Animal:" in code

    def test_class_with_parent(self):
        code = _transpile("@class[Dog; Animal]\n    @print[woof]\n@end")
        assert "class Dog(Animal):" in code

    def test_try_catch(self):
        src = "@try\n    @print[ok]\n@catch[e]\n    @print[err]\n@end"
        code = _transpile(src)
        assert "try:" in code
        assert "except Exception as e:" in code

    def test_try_finally(self):
        src = "@try\n    @print[ok]\n@catch[e]\n    @print[err]\n@finally\n    @print[done]\n@end"
        code = _transpile(src)
        assert "finally:" in code

    def test_assert(self):
        code = _transpile('@assert[x > 0; "must be positive"]')
        assert "assert x > 0" in code

    def test_import(self):
        code = _transpile("@import[requests]")
        assert "import requests" in code

    def test_import_alias(self):
        code = _transpile("@import[requests; req]")
        assert "import requests as req" in code

    def test_import_unknown_raises(self):
        with pytest.raises(TranspileError):
            _transpile("@import[nonexistent_lib_xyz]")

    def test_env_auto_import(self):
        code = _transpile("@var[h; @env[HOME]]")
        assert "import os" in code

    def test_fetch_auto_import(self):
        code = _transpile('@fetch["https://example.com"]')
        assert "import requests" in code

    def test_raw_block(self):
        src = "@raw\n    x = 1 + 1\n@end"
        code = _transpile(src)
        assert "x = 1 + 1" in code

    def test_inline_list(self):
        code = _transpile("@var[lst; @list[1; 2; 3]]")
        assert "lst = [1, 2, 3]" in code

    def test_inline_dict(self):
        code = _transpile("@var[d; @dict[name; Alice; age; 30]]")
        assert "name" in code and "Alice" in code

    def test_namespace_lib_call(self):
        code = _transpile("@math.sqrt[16]")
        assert "sqrt" in code
        assert "16" in code

    def test_store_helpers_injected(self):
        code = _transpile("@store.set[key; val]")
        assert "__cruhon_store_set" in code


# ─────────────────────────────────────────────────────────────
# EVAL VALUE RULES
# ─────────────────────────────────────────────────────────────

class TestEvalValue:
    """Tests for the single _eval_value() semantic rule."""

    def _ev(self, value, context="expr"):
        from cruhon.core.transpiler import Transpiler
        return Transpiler()._eval_value(value, context)

    def test_rule1_quoted_no_braces(self):
        assert self._ev('"hello"') == '"hello"'

    def test_rule2_quoted_with_braces(self):
        assert self._ev('"Hello {name}"') == 'f"Hello {name}"'

    def test_rule2_unquoted_fstring(self):
        result = self._ev("Hello {name}")
        assert 'f"Hello {name}"' == result

    def test_rule3_integer(self):
        assert self._ev("42") == "42"

    def test_rule3_float(self):
        assert self._ev("3.14") == "3.14"

    def test_rule4_true(self):
        assert self._ev("True") == "True"

    def test_rule4_false(self):
        assert self._ev("False") == "False"

    def test_rule4_none(self):
        assert self._ev("None") == "None"

    def test_rule5_list_literal(self):
        assert self._ev("[1, 2, 3]") == "[1, 2, 3]"

    def test_rule5_dict_literal(self):
        assert self._ev('{"key": "val"}') == '{"key": "val"}'

    def test_rule6_expression(self):
        assert self._ev("a + b") == "a + b"

    def test_rule6_function_call(self):
        assert self._ev("len(lst)") == "len(lst)"

    def test_rule7a_identifier_expr(self):
        assert self._ev("myvar", "expr") == "myvar"

    def test_rule7b_identifier_display(self):
        assert self._ev("myvar", "display") == '"myvar"'

    def test_rule8_bare_text(self):
        assert self._ev("hello world") == '"hello world"'

    def test_dict_not_confused_with_fstring(self):
        result = self._ev('{"key": value}')
        assert result == '{"key": value}'

    def test_func_call_with_dict_arg(self):
        result = self._ev('func({"key": val})')
        assert result == 'func({"key": val})'


# ─────────────────────────────────────────────────────────────
# RUNNER (execution)
# ─────────────────────────────────────────────────────────────

class TestRunner:
    def test_hello_world(self, capsys):
        run_source("@print[Hello World]")
        captured = capsys.readouterr()
        assert "Hello World" in captured.out

    def test_var_and_print(self, capsys):
        # Strings must be quoted in expr context — see semantics.md Rule 7a
        run_source('@var[name; "Alice"]\n@print[Hi {name}!]')
        captured = capsys.readouterr()
        assert "Hi Alice!" in captured.out

    def test_for_loop_runs(self, capsys):
        run_source("@for[i; range(3)]\n    @print[{i}]\n@end")
        captured = capsys.readouterr()
        assert "0" in captured.out
        assert "1" in captured.out
        assert "2" in captured.out

    def test_repeat_runs(self, capsys):
        run_source("@repeat[3]\n    @print[hi]\n@end")
        captured = capsys.readouterr()
        assert captured.out.count("hi") == 3

    def test_func_and_call(self, capsys):
        src = "@func[greet; name]\n    @print[Hello {name}!]\n@end\ngreet('Bob')"
        run_source(src)
        captured = capsys.readouterr()
        assert "Hello Bob!" in captured.out

    def test_if_true_branch(self, capsys):
        run_source("@var[x; 5]\n@if[x > 3]\n    @print[big]\n@end")
        captured = capsys.readouterr()
        assert "big" in captured.out

    def test_if_false_branch(self, capsys):
        run_source("@var[x; 1]\n@if[x > 3]\n    @print[big]\n@else\n    @print[small]\n@end")
        captured = capsys.readouterr()
        assert "small" in captured.out

    def test_assert_passes(self):
        run_source("@var[x; 5]\n@assert[x > 0]")

    def test_assert_fails(self):
        with pytest.raises((RunError, AssertionError)):
            run_source("@var[x; -1]\n@assert[x > 0]")

    def test_try_catch(self, capsys):
        src = "@try\n    @var[x; int(\"bad\")]\n@catch[e]\n    @print[caught]\n@end"
        run_source(src)
        captured = capsys.readouterr()
        assert "caught" in captured.out

    def test_raw_block(self, capsys):
        run_source("@raw\n    print('raw output')\n@end")
        captured = capsys.readouterr()
        assert "raw output" in captured.out

    def test_math_lib(self, capsys):
        run_source("@var[r; @math.sqrt[25.0]]\n@print[{r}]")
        captured = capsys.readouterr()
        assert "5.0" in captured.out

    def test_color_lib(self, capsys):
        run_source('@var[c; @color.red["hello"]]\n@print[{c}]')
        captured = capsys.readouterr()
        assert "hello" in captured.out

    def test_time_lib(self, capsys):
        run_source("@var[ts; @time.timestamp[]]\n@print[{ts}]")
        captured = capsys.readouterr()
        assert len(captured.out.strip()) > 0

    def test_json_parse(self, capsys):
        # Use json.loads directly in raw context to avoid quoting issues
        src = "@raw\n    import json\n    data = json.loads('{\"x\": 1}')\n    print(data)\n@end"
        run_source(src)
        captured = capsys.readouterr()
        assert "x" in captured.out

    def test_store_set_get(self, capsys):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            old = os.getcwd()
            os.chdir(d)
            try:
                run_source('@store.set["mykey"; 42]\n@var[v; @store.get["mykey"]]\n@print[{v}]')
                captured = capsys.readouterr()
                assert "42" in captured.out
            finally:
                os.chdir(old)


# ─────────────────────────────────────────────────────────────
# @input COMMAND
# ─────────────────────────────────────────────────────────────

class TestInput:
    def test_input_transpiles(self):
        code = _transpile("@input[Enter: ]")
        assert "input(" in code

    def test_input_transpiles_to_call(self):
        code = _transpile("@input[Enter name: ]")
        assert "input(" in code

    def test_input_no_prompt_transpiles(self):
        code = _transpile("@input[]")
        assert "input(" in code

    def test_input_bare_text_prompt(self):
        code = _transpile("@input[Your name: ]")
        assert "input(" in code
        assert "Your name:" in code


# ─────────────────────────────────────────────────────────────
# @include RESOLUTION
# ─────────────────────────────────────────────────────────────

class TestInclude:
    def test_basic_include(self, tmp_path, capsys):
        included = tmp_path / "greet.clpy"
        included.write_text("@print[from included file]\n")
        main = tmp_path / "main.clpy"
        main.write_text(f'@include[greet.clpy]\n')
        run_file(str(main))
        captured = capsys.readouterr()
        assert "from included file" in captured.out

    def test_include_not_found_raises(self, tmp_path):
        main = tmp_path / "main.clpy"
        main.write_text("@include[nonexistent.clpy]\n")
        with pytest.raises(RunError):
            run_file(str(main))

    def test_direct_circular_include_raises(self, tmp_path):
        a = tmp_path / "a.clpy"
        b = tmp_path / "b.clpy"
        a.write_text("@include[b.clpy]\n")
        b.write_text("@include[a.clpy]\n")
        with pytest.raises(RunError, match="Circular"):
            run_file(str(a))

    def test_indirect_circular_include_raises(self, tmp_path):
        a = tmp_path / "a.clpy"
        b = tmp_path / "b.clpy"
        c = tmp_path / "c.clpy"
        a.write_text("@include[b.clpy]\n")
        b.write_text("@include[c.clpy]\n")
        c.write_text("@include[a.clpy]\n")
        with pytest.raises(RunError, match="Circular"):
            run_file(str(a))


# ─────────────────────────────────────────────────────────────
# STDLIB — FILE
# ─────────────────────────────────────────────────────────────

class TestFileLib:
    def test_file_read(self, tmp_path, capsys):
        f = tmp_path / "test.txt"
        f.write_text("hello from file")
        old = os.getcwd()
        os.chdir(tmp_path)
        try:
            run_source("@var[content; @file.read[\"test.txt\"]]\n@print[{content}]")
            captured = capsys.readouterr()
            assert "hello from file" in captured.out
        finally:
            os.chdir(old)

    def test_file_write_and_exists(self, tmp_path, capsys):
        old = os.getcwd()
        os.chdir(tmp_path)
        try:
            run_source("@file.write[\"out.txt\"; \"written\"]\n@var[ok; @file.exists[\"out.txt\"]]\n@print[{ok}]")
            captured = capsys.readouterr()
            assert "True" in captured.out
        finally:
            os.chdir(old)

    def test_file_path_traversal_blocked(self, tmp_path):
        old = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises((RunError, PermissionError)):
                run_source("@var[x; @file.read[\"../../../etc/passwd\"]]")
        finally:
            os.chdir(old)


# ─────────────────────────────────────────────────────────────
# SYNTAX ENGINE
# ─────────────────────────────────────────────────────────────

class TestSyntaxEngine:
    def setup_method(self):
        from cruhon.core.syntax_engine import SyntaxEngine
        self.engine = SyntaxEngine()

    def test_split_simple(self):
        assert self.engine.split_args("a; b; c") == ["a", "b", "c"]

    def test_split_nested_brackets(self):
        result = self.engine.split_args("name; [1; 2; 3]")
        assert result == ["name", "[1; 2; 3]"]

    def test_split_function_call(self):
        result = self.engine.split_args("name; add(3, 4)")
        assert result == ["name", "add(3, 4)"]

    def test_split_quoted_semicolon(self):
        result = self.engine.split_args('name; "x; y"')
        assert result == ["name", '"x; y"']

    def test_validate_arg_balanced(self):
        self.engine.validate_arg("len(x)")  # should not raise

    def test_validate_arg_unbalanced_raises(self):
        from cruhon.core.parser import ParseError
        with pytest.raises(ParseError):
            self.engine.validate_arg("len(x")


# ─────────────────────────────────────────────────────────────
# MOD SYSTEM
# ─────────────────────────────────────────────────────────────

class TestModSystem:
    def test_registry_register_and_get(self):
        from cruhon.core.registry import register_lib, get_lib
        register_lib("testlib_xyz", "testlib_xyz")
        assert get_lib("testlib_xyz") == "testlib_xyz"

    def test_registry_lib_call(self):
        from cruhon.core.registry import register_lib_call, get_lib_call
        handler = lambda args: f"testfn({args[0]})"
        register_lib_call("testns", "testmethod", handler)
        retrieved = get_lib_call("testns", "testmethod")
        assert retrieved is not None
        assert retrieved(["x"]) == "testfn(x)"

    def test_namespace_isolation(self):
        from cruhon.core.namespace_runtime import Namespace, reset_registry
        ns = Namespace("test_ns")
        ns.state["secret"] = "value"
        with pytest.raises(RuntimeError):
            ns.access_state("secret", "other_ns")

    def test_namespace_allow_peer(self):
        from cruhon.core.namespace_runtime import Namespace
        ns = Namespace("owner_ns")
        ns.state["key"] = "value"
        ns.allow_peer("trusted_ns")
        result = ns.access_state("key", "trusted_ns")
        assert result == "value"

    def test_namespace_self_access(self):
        from cruhon.core.namespace_runtime import Namespace
        ns = Namespace("myns")
        ns.state["x"] = 99
        assert ns.access_state("x", "myns") == 99

    def test_namespace_write_blocked(self):
        from cruhon.core.namespace_runtime import Namespace
        ns = Namespace("myns")
        with pytest.raises(RuntimeError):
            ns.write_state("x", 1, "other_ns")
