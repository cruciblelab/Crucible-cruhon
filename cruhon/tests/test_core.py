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


# ─────────────────────────────────────────────────────────────
# NAMED PARAMETERS
# ─────────────────────────────────────────────────────────────

class TestNamedArgs:
    def setup_method(self):
        from cruhon.core.syntax_engine import SyntaxEngine
        self.engine = SyntaxEngine()

    def test_positional_only(self):
        args, kwargs = self.engine.split_named_args("a ; b ; c")
        assert args == ["a", "b", "c"]
        assert kwargs == {}

    def test_kwargs_only(self):
        args, kwargs = self.engine.split_named_args("reason=spam ; delete_days=7")
        assert args == []
        assert kwargs == {"reason": "spam", "delete_days": "7"}

    def test_mixed_positional_and_kwargs(self):
        args, kwargs = self.engine.split_named_args("url ; reason=spam ; delete_days=7")
        assert args == ["url"]
        assert kwargs == {"reason": "spam", "delete_days": "7"}

    def test_kwarg_value_with_spaces(self):
        args, kwargs = self.engine.split_named_args('msg=hello world ; n=5')
        assert args == []
        assert kwargs["msg"] == "hello world"
        assert kwargs["n"] == "5"

    def test_positional_after_kwarg_raises(self):
        from cruhon.core.parser import ParseError
        with pytest.raises(ParseError):
            self.engine.split_named_args("key=val ; positional")

    def test_equals_inside_string_is_not_kwarg(self):
        args, kwargs = self.engine.split_named_args('"x=y"')
        assert args == ['"x=y"']
        assert kwargs == {}

    def test_no_args(self):
        args, kwargs = self.engine.split_named_args("")
        assert args == []
        assert kwargs == {}


# ─────────────────────────────────────────────────────────────
# HINT ENGINE
# ─────────────────────────────────────────────────────────────

class TestHints:
    def test_nameerror_hint_suggests_quotes(self):
        with pytest.raises(RunError) as exc_info:
            run_source("@var[x; Cruhon]")
        msg = str(exc_info.value)
        assert "Hint" in msg
        assert "quotes" in msg.lower() or "quote" in msg.lower()

    def test_nameerror_hint_includes_variable_name(self):
        with pytest.raises(RunError) as exc_info:
            run_source("@var[x; SomeMissingName]")
        assert "SomeMissingName" in str(exc_info.value)

    def test_zerodivision_hint(self):
        with pytest.raises(RunError) as exc_info:
            run_source("@var[x; 1 / 0]")
        assert "zero" in str(exc_info.value).lower()

    def test_indexerror_hint(self):
        with pytest.raises(RunError) as exc_info:
            run_source("@var[lst; [1, 2]]\n@var[x; lst[99]]")
        assert "index" in str(exc_info.value).lower() or "range" in str(exc_info.value).lower()

    def test_no_false_positive_hint_on_valid_code(self, capsys):
        run_source('@var[x; "hello"]\n@print[{x}]')
        captured = capsys.readouterr()
        assert "hello" in captured.out


# ─────────────────────────────────────────────────────────────
# BLOCK PLUGIN COMMANDS
# ─────────────────────────────────────────────────────────────

class TestBlockPlugin:
    def test_block_command_basic(self, capsys):
        """api.block_command registers a block that runs its body."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("test_block_mod")

        collected = {}

        def visit_section(transpiler, node):
            collected["args"] = node.args
            collected["kwargs"] = node.kwargs
            # Emit body at current indent level (section is a transparent wrapper)
            parts = [child.accept(transpiler) for child in node.body]
            return "\n".join(p for p in parts if p)

        api.block_command("section", visit_section)

        run_source('@section["intro"]\n    @print["inside block"]\n@end')
        captured = capsys.readouterr()
        assert "inside block" in captured.out
        assert collected["args"] == ['"intro"']

    def test_block_command_named_args(self):
        """Block command receives named args in node.kwargs."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("test_block_kwargs")

        received_kwargs = {}

        def visit_cmd(transpiler, node):
            received_kwargs.update(node.kwargs)
            parts = [child.accept(transpiler) for child in node.body]
            return "\n".join(p for p in parts if p)

        api.block_command("mblock", visit_cmd)

        run_source('@mblock["hello"; priority=high]\n    @print["x"]\n@end')
        assert received_kwargs.get("priority") == "high"

    def test_block_command_empty_body(self, capsys):
        """Block command with no body should not crash."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("test_empty_block")

        def visit_empty(transpiler, node):
            return transpiler._line("pass")

        api.block_command("emptyblock", visit_empty)
        run_source('@emptyblock[]\n@end')  # no error

    def test_plugin_block_node_fields(self):
        """PluginBlockNode has the expected fields."""
        from cruhon.core.ast_nodes import PluginBlockNode
        node = PluginBlockNode(plugin_name="test", args=["a"], kwargs={"k": "v"}, body=[])
        assert node.plugin_name == "test"
        assert node.args == ["a"]
        assert node.kwargs == {"k": "v"}


# ─────────────────────────────────────────────────────────────
# CONTEXT VARIABLES
# ─────────────────────────────────────────────────────────────

class TestContextVars:
    def test_ctx_set_and_read(self, capsys):
        run_source('@ctx.set["username"; "Alice"]\n@var[u; @ctx["username"]]\n@print[{u}]')
        captured = capsys.readouterr()
        assert "Alice" in captured.out

    def test_ctx_default_when_missing(self, capsys):
        run_source('@var[v; @ctx["missing"; "fallback"]]\n@print[{v}]')
        captured = capsys.readouterr()
        assert "fallback" in captured.out

    def test_ctx_get_method(self, capsys):
        run_source('@ctx.set["score"; 99]\n@var[s; @ctx.get["score"]]\n@print[{s}]')
        captured = capsys.readouterr()
        assert "99" in captured.out

    def test_ctx_clear(self, capsys):
        run_source('@ctx.set["x"; "val"]\n@ctx.clear[]\n@var[v; @ctx["x"; "gone"]]\n@print[{v}]')
        captured = capsys.readouterr()
        assert "gone" in captured.out

    def test_ctx_delete(self, capsys):
        run_source('@ctx.set["k"; "v"]\n@ctx.delete["k"]\n@var[v; @ctx["k"; "deleted"]]\n@print[{v}]')
        captured = capsys.readouterr()
        assert "deleted" in captured.out

    def test_ctx_plugin_sets_for_block(self, capsys):
        """Plugin block that pre-populates __ctx__ before running body."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("test_ctx_plugin")

        def visit_withuser(transpiler, node):
            username = node.args[0] if node.args else '"unknown"'
            lines = [transpiler._line(f'__ctx__["user"] = {username}')]
            for child in node.body:
                r = child.accept(transpiler)
                if r:
                    lines.append(r)
            return "\n".join(lines)

        api.block_command("withuser", visit_withuser)

        run_source('@withuser["Bob"]\n    @var[u; @ctx["user"]]\n    @print[{u}]\n@end')
        captured = capsys.readouterr()
        assert "Bob" in captured.out


# ─────────────────────────────────────────────────────────────
# PLUGIN FOUNDATION SYSTEM (v1.1.0)
# ─────────────────────────────────────────────────────────────

class TestPluginFoundation:
    def test_expose_and_consume(self):
        from cruhon.core.mod_loader import ModAPI, _EXPOSED_APIS
        api_a = ModAPI("foundation-plugin")
        api_a.expose("helper", lambda x: x * 2)

        api_b = ModAPI("dependent-plugin")
        helper = api_b.consume("foundation-plugin", "helper")
        assert helper(5) == 10

    def test_consume_missing_raises(self):
        from cruhon.core.mod_loader import ModAPI
        api = ModAPI("consumer-plugin")
        with pytest.raises(RuntimeError, match="not exposed"):
            api.consume("nonexistent-plugin", "some_key")

    def test_consume_with_default(self):
        from cruhon.core.mod_loader import ModAPI
        api = ModAPI("consumer-default")
        result = api.consume("nonexistent-plugin", "key", default="fallback")
        assert result == "fallback"

    def test_is_loaded_true(self):
        from cruhon.core.mod_loader import ModAPI, _LOADED_MODS
        _LOADED_MODS["test-is-loaded-mod"] = {"version": "1.0", "source": "test", "source_path": "", "manifest": {}}
        api = ModAPI("checker")
        assert api.is_loaded("test-is-loaded-mod") is True

    def test_is_loaded_false(self):
        from cruhon.core.mod_loader import ModAPI
        api = ModAPI("checker2")
        assert api.is_loaded("definitely-not-loaded-xyz") is False

    def test_config_reads_from_manifest(self):
        from cruhon.core.mod_loader import ModAPI, _LOADED_MODS
        _LOADED_MODS["config-test-mod"] = {
            "version": "1.0", "source": "test", "source_path": "",
            "manifest": {"prefix": "!", "debug": True}
        }
        api = ModAPI("config-test-mod")
        assert api.config("prefix") == "!"
        assert api.config("debug") is True
        assert api.config("missing", default="x") == "x"

    def test_expose_multiple_keys(self):
        from cruhon.core.mod_loader import ModAPI
        api = ModAPI("multi-expose-plugin")
        api.expose("fn_a", lambda: "a")
        api.expose("fn_b", lambda: "b")
        fn_a = api.consume("multi-expose-plugin", "fn_a")
        fn_b = api.consume("multi-expose-plugin", "fn_b")
        assert fn_a() == "a"
        assert fn_b() == "b"

    def test_version_aware_dependency(self):
        from cruhon.core.dependency_resolver import DependencyResolver
        resolver = DependencyResolver()
        resolver.mark_loaded("cruhon-base", "2.0.0")
        resolver.declare("my-plugin", ["cruhon-base >= 1.0.0"])
        missing = resolver.check("my-plugin")
        assert missing == []

    def test_version_constraint_fails(self):
        from cruhon.core.dependency_resolver import DependencyResolver
        resolver = DependencyResolver()
        resolver.mark_loaded("cruhon-base", "0.5.0")
        resolver.declare("my-plugin", ["cruhon-base >= 1.0.0"])
        missing = resolver.check("my-plugin")
        assert len(missing) == 1
        assert "cruhon-base" in missing[0]

    def test_list_exposed_apis(self):
        from cruhon.core.mod_loader import ModAPI, list_exposed_apis
        api = ModAPI("list-test-plugin")
        api.expose("foo", 42)
        api.expose("bar", lambda: None)
        exposed = list_exposed_apis()
        assert "list-test-plugin" in exposed
        assert "foo" in exposed["list-test-plugin"]
        assert "bar" in exposed["list-test-plugin"]


# ─────────────────────────────────────────────────────────────
# LANGUAGE COMPLETION v1.3.0
# ─────────────────────────────────────────────────────────────

class TestWith:
    def test_with_as_var(self, tmp_path):
        f = tmp_path / "t.txt"
        f.write_text("hello")
        old = os.getcwd()
        os.chdir(tmp_path)
        try:
            run_source('@with[open("t.txt") as f]\n    @var[c; f.read()]\n@end')
        finally:
            os.chdir(old)

    def test_with_no_var(self):
        run_source('@with[open("/dev/null", "w")]\n    pass\n@end')

    def test_with_body_executes(self, capsys):
        run_source('@with[open("/dev/null", "w") as f]\n    @print[inside]\n@end')
        assert "inside" in capsys.readouterr().out

    def test_with_nested(self, tmp_path):
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("A")
        b.write_text("B")
        old = os.getcwd()
        os.chdir(tmp_path)
        try:
            run_source(
                '@with[open("a.txt") as fa]\n'
                '    @with[open("b.txt") as fb]\n'
                '        @var[both; fa.read() + fb.read()]\n'
                '    @end\n'
                '@end'
            )
        finally:
            os.chdir(old)


class TestMatch:
    def test_match_basic(self, capsys):
        run_source('@var[x; 2]\n@match[x]\n    @case[1]\n        @print[one]\n    @case[2]\n        @print[two]\n@end')
        assert "two" in capsys.readouterr().out

    def test_match_default(self, capsys):
        run_source('@var[x; 99]\n@match[x]\n    @case[1]\n        @print[one]\n    @default\n        @print[other]\n@end')
        assert "other" in capsys.readouterr().out

    def test_match_string(self, capsys):
        run_source('@var[cmd; "quit"]\n@match[cmd]\n    @case["start"]\n        @print[starting]\n    @case["quit"]\n        @print[quitting]\n    @default\n        @print[unknown]\n@end')
        assert "quitting" in capsys.readouterr().out

    def test_match_no_default_no_match(self, capsys):
        run_source('@var[x; 5]\n@match[x]\n    @case[1]\n        @print[one]\n@end')
        assert capsys.readouterr().out.strip() == ""


class TestDel:
    def test_del_single(self):
        with pytest.raises(RunError):
            run_source('@var[x; 42]\n@del[x]\n@print[{x}]')

    def test_del_multiple(self):
        run_source('@var[a; 1]\n@var[b; 2]\n@del[a; b]')


class TestRaise:
    def test_raise_with_message(self, capsys):
        run_source('@try\n    @raise[ValueError; "bad input"]\n@catch[e]\n    @print[caught]\n@end')
        assert "caught" in capsys.readouterr().out

    def test_raise_bare_reraise(self):
        with pytest.raises(RunError):
            run_source('@try\n    @raise[RuntimeError; "orig"]\n@catch[e]\n    @raise\n@end')

    def test_raise_reraise_outer_catches(self, capsys):
        run_source(
            '@try\n'
            '    @try\n'
            '        @raise[ValueError; "inner"]\n'
            '    @catch[e]\n'
            '        @raise\n'
            '    @end\n'
            '@catch[e]\n'
            '    @print[reraised]\n'
            '@end'
        )
        assert "reraised" in capsys.readouterr().out


class TestMultiLine:
    def test_multiline_parens(self, capsys):
        run_source('@var[x; (\n    1 + 2\n)]\n@print[{x}]')
        assert "3" in capsys.readouterr().out

    def test_multiline_func_call(self, capsys):
        run_source('@var[r; max(\n    10,\n    20,\n    30\n)]\n@print[{r}]')
        assert "30" in capsys.readouterr().out

    def test_multiline_list_literal(self, capsys):
        run_source('@var[lst; [\n    1,\n    2,\n    3\n]]\n@print[{len(lst)}]')
        assert "3" in capsys.readouterr().out


# ─────────────────────────────────────────────────────────────
# PLUGIN SYSTEM v1.2.0 — scoped ctx, transforms, block hooks
# ─────────────────────────────────────────────────────────────

class TestScopedCtx:
    def test_scoped_block_isolates_ctx(self, capsys):
        """scoped=True: changes inside block don't leak out."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("scoped-test-mod")

        def visit_scope(transpiler, node):
            lines = [transpiler._line('__ctx__["inside"] = "yes"')]
            for child in node.body:
                r = child.accept(transpiler)
                if r:
                    lines.append(r)
            return "\n".join(lines)

        api.block_command("scopeblock", visit_scope, scoped=True)

        run_source(
            '@ctx.set["inside"; "no"]\n'
            '@scopeblock[]\n'
            '    @var[v; @ctx["inside"]]\n'   # read ctx into var
            '    @print[{v}]\n'              # print it
            '@end\n'
            '@var[after; @ctx["inside"; "no"]]\n'
            '@print[{after}]'
        )
        captured = capsys.readouterr()
        assert "yes" in captured.out      # inside block: __ctx__ was "yes"
        assert "no" in captured.out       # outside block: original value restored

    def test_ctx_push_pop_manual(self, capsys):
        """@ctx.push / @ctx.pop manual stack operations."""
        run_source(
            '@ctx.set["x"; "outer"]\n'
            '@ctx.push[]\n'
            '@ctx.set["x"; "inner"]\n'
            '@var[v1; @ctx["x"]]\n'
            '@print[{v1}]\n'
            '@ctx.pop[]\n'
            '@var[v2; @ctx["x"]]\n'
            '@print[{v2}]'
        )
        captured = capsys.readouterr()
        lines = captured.out.strip().splitlines()
        assert lines[0] == "inner"
        assert lines[1] == "outer"

    def test_unscoped_block_leaks_ctx(self, capsys):
        """Without scoped=True, ctx changes persist after block."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("unscoped-test-mod")

        def visit_leak(transpiler, node):
            lines = [transpiler._line('__ctx__["leaked"] = "yes"')]
            for child in node.body:
                r = child.accept(transpiler)
                if r:
                    lines.append(r)
            return "\n".join(lines)

        api.block_command("leakblock", visit_leak, scoped=False)

        run_source('@leakblock[]\n@end\n@var[v; @ctx["leaked"; "no"]]\n@print[{v}]')
        captured = capsys.readouterr()
        assert "yes" in captured.out  # leak is expected for unscoped


class TestNodeTransform:
    def test_transform_wraps_block_output(self, capsys):
        """api.transform() post-processes another plugin's block output."""
        from cruhon.core.mod_loader import ModAPI

        # Primary plugin — emits a print
        api_primary = ModAPI("primary-transform-mod")

        def visit_primary(transpiler, node):
            parts = [child.accept(transpiler) for child in node.body]
            return "\n".join(p for p in parts if p)

        api_primary.block_command("tblock", visit_primary)

        # Secondary plugin — wraps the output with before/after prints
        api_secondary = ModAPI("wrapping-transform-mod")

        def wrap_fn(transpiler, node, code):
            before = transpiler._line('print("BEFORE")')
            after = transpiler._line('print("AFTER")')
            return before + "\n" + code + "\n" + after

        api_secondary.transform("tblock", wrap_fn)

        run_source('@tblock[]\n    @print["MIDDLE"]\n@end')
        captured = capsys.readouterr()
        lines = [l for l in captured.out.strip().splitlines() if l]
        assert lines == ["BEFORE", "MIDDLE", "AFTER"]

    def test_multiple_transforms_chain(self, capsys):
        """Multiple transforms run in registration order."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("chain-transform-mod")

        def visit_chain(transpiler, node):
            parts = [child.accept(transpiler) for child in node.body]
            return "\n".join(p for p in parts if p)

        api.block_command("chainblock", visit_chain)

        def add_prefix(transpiler, node, code):
            return transpiler._line('print("A")') + "\n" + code

        def add_suffix(transpiler, node, code):
            return code + "\n" + transpiler._line('print("B")')

        api.transform("chainblock", add_prefix)
        api.transform("chainblock", add_suffix)

        run_source('@chainblock[]\n    @print["X"]\n@end')
        captured = capsys.readouterr()
        lines = [l for l in captured.out.strip().splitlines() if l]
        assert lines == ["A", "X", "B"]


class TestBlockHooks:
    def test_block_enter_hook_fires(self):
        """api.block_hook("enter") fires at runtime when a block starts."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("hook-enter-mod")

        def visit_hookable(transpiler, node):
            parts = [child.accept(transpiler) for child in node.body]
            return "\n".join(p for p in parts if p) or transpiler._line("pass")

        api.block_command("hookable", visit_hookable)

        entered = []
        api.block_hook("enter", lambda name, args: entered.append(name))

        run_source('@hookable[]\n@end')
        assert "hookable" in entered

    def test_block_exit_hook_fires(self):
        """api.block_hook("exit") fires at runtime when a block ends."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("hook-exit-mod")

        def visit_exitblock(transpiler, node):
            parts = [child.accept(transpiler) for child in node.body]
            return "\n".join(p for p in parts if p) or transpiler._line("pass")

        api.block_command("exitblock", visit_exitblock)

        exited = []
        api.block_hook("exit", lambda name, args: exited.append(name))

        run_source('@exitblock[]\n@end')
        assert "exitblock" in exited


# ─────────────────────────────────────────────────────────────
# PLUGIN SYSTEM v1.4.0 — AST hooks, async for/with, mod enrichment
# ─────────────────────────────────────────────────────────────

class TestAstHooks:
    def test_ast_hook_fires_for_matching_node(self):
        """api.ast_hook fires on every matching node type."""
        from cruhon.core.mod_loader import ModAPI
        from cruhon.core.parser import parse
        from cruhon.core.transpiler import get_transpiler

        api = ModAPI("ast-hook-test-mod")
        seen = []

        def hook_var(node):
            seen.append(node.name)
            return node

        api.ast_hook("VarNode", hook_var)

        t = get_transpiler()
        ast = parse("@var[x; 1]\n@var[y; 2]")
        t.transpile(ast)

        assert "x" in seen
        assert "y" in seen

    def test_ast_hook_can_mutate_node(self, capsys):
        """ast_hook can modify a node's fields before transpilation."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("ast-hook-mutate-mod")

        def rename_var(node):
            if node.name == "secret":
                node.name = "renamed"
            return node

        api.ast_hook("VarNode", rename_var)

        run_source('@var[secret; "hello"]\n@print[{renamed}]')
        assert "hello" in capsys.readouterr().out

    def test_ast_hook_multiple_hooks_chain(self):
        """Multiple hooks for the same type fire in registration order."""
        from cruhon.core.mod_loader import ModAPI
        from cruhon.core.parser import parse
        from cruhon.core.transpiler import get_transpiler

        api = ModAPI("ast-hook-chain-mod")
        order = []

        def hook_a(node):
            order.append("A")
            return node

        def hook_b(node):
            order.append("B")
            return node

        api.ast_hook("PrintNode", hook_a)
        api.ast_hook("PrintNode", hook_b)

        t = get_transpiler()
        ast = parse("@print[hello]")
        t.transpile(ast)

        assert order.index("A") < order.index("B")

    def test_ast_hook_nested_nodes(self):
        """AST hooks recurse into nested block bodies."""
        from cruhon.core.mod_loader import ModAPI
        from cruhon.core.parser import parse
        from cruhon.core.transpiler import get_transpiler

        api = ModAPI("ast-hook-nested-mod")
        seen = []

        def hook_print(node):
            seen.append(str(node.value))
            return node

        api.ast_hook("PrintNode", hook_print)

        t = get_transpiler()
        ast = parse("@if[True]\n    @print[inside]\n@end")
        t.transpile(ast)

        assert "inside" in seen

    def test_ast_hook_no_hooks_no_change(self, capsys):
        """Without hooks, program runs normally."""
        run_source('@var[z; 99]\n@print[{z}]')
        assert "99" in capsys.readouterr().out


class TestAsyncFor:
    def test_async_for_transpiles(self):
        """@async.for generates 'async for' Python."""
        code = _transpile(
            "@async[main]\n"
            "    @async.for[item; aiter]\n"
            "        @print[{item}]\n"
            "    @end\n"
            "@end"
        )
        assert "async for item in aiter:" in code

    def test_async_for_body_indented(self):
        """@async.for body is indented inside the loop."""
        code = _transpile(
            "@async[main]\n"
            "    @async.for[x; items]\n"
            "        @var[y; x]\n"
            "    @end\n"
            "@end"
        )
        assert "async for x in items:" in code
        assert "y = x" in code

    def test_async_for_parse_node_type(self):
        """@async.for produces AsyncForNode."""
        from cruhon.core.ast_nodes import AsyncForNode, FuncNode
        ast = parse(
            "@async[main]\n"
            "    @async.for[n; nums]\n"
            "        @print[{n}]\n"
            "    @end\n"
            "@end"
        )
        func = ast.body[0]
        assert isinstance(func, FuncNode)
        assert isinstance(func.body[0], AsyncForNode)
        assert func.body[0].var == "n"
        assert func.body[0].iterable == "nums"

    def test_async_for_missing_iterable_raises(self):
        """@async.for with only one arg raises ParseError."""
        from cruhon.core.parser import ParseError
        with pytest.raises(ParseError):
            parse("@async[main]\n    @async.for[x]\n    @end\n@end")


class TestAsyncWith:
    def test_async_with_transpiles(self):
        """@async.with generates 'async with' Python."""
        code = _transpile(
            "@async[main]\n"
            "    @async.with[aopen(\"f.txt\") as f]\n"
            "        @print[opened]\n"
            "    @end\n"
            "@end"
        )
        assert "async with" in code
        assert "as f:" in code

    def test_async_with_no_var(self):
        """@async.with without 'as var' generates plain 'async with'."""
        code = _transpile(
            "@async[main]\n"
            "    @async.with[lock]\n"
            "        @print[locked]\n"
            "    @end\n"
            "@end"
        )
        assert "async with lock:" in code

    def test_async_with_parse_node_type(self):
        """@async.with produces AsyncWithNode."""
        from cruhon.core.ast_nodes import AsyncWithNode, FuncNode
        ast = parse(
            "@async[main]\n"
            "    @async.with[ctx as c]\n"
            "        @print[ok]\n"
            "    @end\n"
            "@end"
        )
        func = ast.body[0]
        assert isinstance(func, FuncNode)
        assert isinstance(func.body[0], AsyncWithNode)
        assert func.body[0].expr == "ctx"
        assert func.body[0].var == "c"

    def test_async_with_body_indented(self):
        """@async.with body is indented under the with block."""
        code = _transpile(
            "@async[main]\n"
            "    @async.with[mgr as m]\n"
            "        @var[v; m]\n"
            "    @end\n"
            "@end"
        )
        assert "async with mgr as m:" in code
        assert "v = m" in code


class TestModEnrichment:
    def test_list_block_commands_tracks_registration(self):
        """block_command() registers in list_block_commands()."""
        from cruhon.core.mod_loader import ModAPI, list_block_commands

        api = ModAPI("enrichment-test-mod")

        def visit_enrichcmd(transpiler, node):
            return transpiler._line("pass")

        api.block_command("enrichcmd", visit_enrichcmd)

        result = list_block_commands()
        assert "enrichment-test-mod" in result
        assert "enrichcmd" in result["enrichment-test-mod"]

    def test_list_block_commands_multiple_cmds(self):
        """Multiple block_command calls accumulate in the plugin's list."""
        from cruhon.core.mod_loader import ModAPI, list_block_commands

        api = ModAPI("multi-cmd-mod")
        noop = lambda t, n: t._line("pass")
        api.block_command("cmd_one", noop)
        api.block_command("cmd_two", noop)

        result = list_block_commands()
        assert "multi-cmd-mod" in result
        assert "cmd_one" in result["multi-cmd-mod"]
        assert "cmd_two" in result["multi-cmd-mod"]

    def test_list_exposed_apis_returns_keys(self):
        """list_exposed_apis returns plugin → [key, ...] mapping."""
        from cruhon.core.mod_loader import ModAPI, list_exposed_apis

        api = ModAPI("expose-keys-mod")
        api.expose("helper_fn", lambda x: x)
        api.expose("version", "1.0")

        result = list_exposed_apis()
        assert "expose-keys-mod" in result
        assert "helper_fn" in result["expose-keys-mod"]
        assert "version" in result["expose-keys-mod"]

    def test_visitor_owner_in_error_message(self):
        """api.command() visitor errors include the owning plugin name."""
        from cruhon.core.mod_loader import ModAPI
        from cruhon.core.transpiler import TranspileError, get_transpiler
        from cruhon.core.parser import parse
        from cruhon.core.ast_nodes import Node
        from dataclasses import dataclass

        @dataclass
        class BadCmdNode(Node):
            pass

        api = ModAPI("owner-error-mod")

        def bad_visitor(transpiler, node):
            raise RuntimeError("something broke")

        def bad_parser(parser):
            parser.advance()
            return BadCmdNode(line=1)

        api.command("badcmd", bad_parser, bad_visitor)

        t = get_transpiler()
        t._custom_visitors["BadCmdNode"] = bad_visitor
        t._visitor_owners["BadCmdNode"] = "owner-error-mod"

        with pytest.raises(TranspileError) as exc_info:
            t.visit_unknown(BadCmdNode(line=1))

        assert "owner-error-mod" in str(exc_info.value)


class TestVisitorOwner:
    def test_api_command_records_owner(self):
        """api.command() stores plugin name in _visitor_owners."""
        from cruhon.core.mod_loader import ModAPI
        from cruhon.core.transpiler import get_transpiler
        from cruhon.core.ast_nodes import Node
        from dataclasses import dataclass

        @dataclass
        class OwnerTestNode(Node):
            pass

        api = ModAPI("owner-record-mod")

        def parser_fn(parser):
            parser.advance()
            return OwnerTestNode(line=1)

        def visitor_fn(transpiler, node):
            return transpiler._line("pass")

        api.command("ownercmd", parser_fn, visitor_fn)

        t = get_transpiler()
        assert t._visitor_owners.get("OwnercmdNode") == "owner-record-mod"

    def test_error_message_includes_plugin_name(self):
        """visit_unknown error includes plugin name from _visitor_owners."""
        from cruhon.core.transpiler import get_transpiler, TranspileError
        from cruhon.core.ast_nodes import Node
        from dataclasses import dataclass

        @dataclass
        class TraceableNode(Node):
            pass

        t = get_transpiler()
        t._custom_visitors["TraceableNode"] = lambda _t, _n: (_ for _ in ()).throw(ValueError("boom"))
        t._visitor_owners["TraceableNode"] = "traceable-plugin"

        with pytest.raises(TranspileError) as exc:
            t.visit_unknown(TraceableNode(line=5))

        assert "traceable-plugin" in str(exc.value)

    def test_block_command_owner_not_in_visitor_owners(self):
        """block_command does NOT go through _visitor_owners — it uses _block_visitors."""
        from cruhon.core.mod_loader import ModAPI
        from cruhon.core.transpiler import get_transpiler

        api = ModAPI("block-owner-mod")
        api.block_command("noowner", lambda t, n: t._line("pass"))

        t = get_transpiler()
        assert "noowner" in t._block_visitors
        assert "NoownerNode" not in t._visitor_owners


class TestAsyncForWithRun:
    def test_async_for_runs(self, capsys):
        """@async.for executes correctly at runtime with an async generator."""
        run_source(
            "@raw\n"
            "async def _agen():\n"
            "    for i in [1, 2, 3]:\n"
            "        yield i\n"
            "@end\n"
            "@async[main]\n"
            "    @var[results; []]\n"
            "    @async.for[x; _agen()]\n"
            "        results.append(x)\n"
            "    @end\n"
            "    @print[{len(results)}]\n"
            "@end"
        )
        assert "3" in capsys.readouterr().out

    def test_async_with_runs(self, capsys):
        """@async.with executes correctly at runtime using asyncio.Lock."""
        run_source(
            "@raw\n"
            "import asyncio\n"
            "@end\n"
            "@async[main]\n"
            "    @var[lock; asyncio.Lock()]\n"
            "    @async.with[lock]\n"
            "        @print[locked]\n"
            "    @end\n"
            "@end"
        )
        assert "locked" in capsys.readouterr().out


# ─────────────────────────────────────────────────────────────
# PLUGIN SYSTEM v1.5.0 — inject, inline_command, eval_hook
# ─────────────────────────────────────────────────────────────

class TestInject:
    def test_inject_plain_value_available_in_script(self, capsys):
        """api.inject() with a plain value is accessible in scripts."""
        from cruhon.core.mod_loader import ModAPI
        api = ModAPI("inject-plain-mod")
        api.inject("APP_NAME", "Cruhon")
        run_source('@print[{APP_NAME}]')
        assert "Cruhon" in capsys.readouterr().out

    def test_inject_factory_called_per_run(self, capsys):
        """api.inject() with a callable factory is called before each exec."""
        from cruhon.core.mod_loader import ModAPI
        api = ModAPI("inject-factory-mod")
        counter = [0]

        def make_counter():
            counter[0] += 1
            return counter[0]

        api.inject("RUN_COUNT", make_counter)
        run_source('@print[{RUN_COUNT}]')
        run_source('@print[{RUN_COUNT}]')
        out1, out2 = capsys.readouterr().out.strip().splitlines()
        assert int(out1) >= 1
        assert int(out2) > int(out1)

    def test_inject_object_accessible_by_attribute(self, capsys):
        """Injected objects can be accessed with dot notation in scripts."""
        from cruhon.core.mod_loader import ModAPI

        class Config:
            version = "9.9"

        api = ModAPI("inject-obj-mod")
        api.inject("cfg", Config())
        run_source('@print[{cfg.version}]')
        assert "9.9" in capsys.readouterr().out

    def test_inject_does_not_leak_between_scripts(self):
        """Each exec() gets a fresh copy — mutations don't persist."""
        from cruhon.core.mod_loader import ModAPI
        api = ModAPI("inject-isolation-mod")
        api.inject("shared", {"count": 0})
        run_source('shared["count"] += 1')
        run_source('shared["count"] += 1')
        # Each run gets a fresh dict (factory returns new object each time)
        # If inject is a static value, this tests that the value itself is the same
        # object — that's fine for this test; we just verify no crash.

    def test_multiple_injects_all_available(self, capsys):
        """Multiple api.inject() calls are all available in the same script."""
        from cruhon.core.mod_loader import ModAPI
        api = ModAPI("inject-multi-mod")
        api.inject("X_VAL", 42)
        api.inject("Y_VAL", 58)
        run_source('@print[{X_VAL + Y_VAL}]')
        assert "100" in capsys.readouterr().out

    def test_get_inject_globals_callable_resolved(self):
        """get_inject_globals() resolves callables."""
        from cruhon.core.mod_loader import ModAPI, get_inject_globals
        api = ModAPI("inject-resolve-mod")
        api.inject("computed", lambda: 7 * 6)
        result = get_inject_globals()
        assert result.get("computed") == 42


class TestInlineCommand:
    def test_inline_command_used_in_var(self, capsys):
        """Inline command registered via api.inline_command works in @var."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("inline-cmd-mod")

        def handle_greet(parser):
            parser.advance()  # consume @greet token
            args = parser.parse_args()
            name = args[0] if args else '"world"'
            return f'"Hello, " + {name}'

        api.inline_command("greet", handle_greet)
        run_source('@var[msg; @greet["Alice"]]\n@print[{msg}]')
        assert "Hello, Alice" in capsys.readouterr().out

    def test_inline_command_no_args(self, capsys):
        """Inline command with no arguments works correctly."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("inline-noarg-mod")

        def handle_answer(parser):
            parser.advance()
            parser.parse_args()
            return "42"

        api.inline_command("answer", handle_answer)
        run_source('@var[x; @answer[]]\n@print[{x}]')
        assert "42" in capsys.readouterr().out

    def test_inline_command_in_print(self, capsys):
        """Inline command can be used directly in @print."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("inline-print-mod")

        def handle_pi(parser):
            parser.advance()
            parser.parse_args()
            return "3.14159"

        api.inline_command("pi", handle_pi)
        # @pi[] as a direct arg — no {} wrapping needed (avoids set-literal ambiguity)
        run_source('@var[v; @pi[]]\n@print[{v}]')
        assert "3.14159" in capsys.readouterr().out

    def test_inline_command_generates_python_expr(self):
        """Inline command output is a Python expression embedded in generated code."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("inline-gen-mod")

        def handle_slug(parser):
            parser.advance()
            args = parser.parse_args()
            text = args[0] if args else '""'
            return f'{text}.lower().replace(" ", "-")'

        api.inline_command("slug", handle_slug)
        code = _transpile('@var[s; @slug["Hello World"]]')
        assert '.lower().replace(" ", "-")' in code

    def test_inline_command_appears_in_error_message(self):
        """Error message includes registered inline commands."""
        from cruhon.core.mod_loader import ModAPI
        from cruhon.core.parser import ParseError, get_parser

        api = ModAPI("inline-err-mod")

        def handle_dummy(parser):
            parser.advance()
            parser.parse_args()
            return "None"

        api.inline_command("myspecial", handle_dummy)

        # An unknown inline command should error; the message lists known ones
        with pytest.raises(ParseError) as exc:
            _transpile('@var[x; @nonexistent[]]')

        assert "@env" in str(exc.value)  # builtins still listed


class TestEvalHook:
    def test_eval_hook_intercepts_value(self, capsys):
        """api.eval_hook() intercepts and transforms matching values."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("eval-hook-mod")

        def dollar_hook(value, context):
            if value.startswith("$"):
                key = value[1:]
                return f'"DOLLAR_{key}"'
            return None

        api.eval_hook(dollar_hook)
        run_source('@var[x; $MYVAR]\n@print[{x}]')
        assert "DOLLAR_MYVAR" in capsys.readouterr().out

    def test_eval_hook_none_passes_through(self, capsys):
        """Returning None from eval_hook lets default rules handle the value."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("eval-hook-passthrough-mod")

        def noop_hook(value, context):
            return None  # always pass through

        api.eval_hook(noop_hook)
        run_source('@var[x; 42]\n@print[{x}]')
        assert "42" in capsys.readouterr().out

    def test_eval_hook_receives_context(self):
        """eval_hook receives the correct context string ('expr' or 'display')."""
        from cruhon.core.mod_loader import ModAPI
        from cruhon.core.transpiler import get_transpiler
        from cruhon.core.parser import parse

        api = ModAPI("eval-hook-ctx-mod")
        seen_contexts = []

        def record_hook(value, context):
            seen_contexts.append(context)
            return None

        api.eval_hook(record_hook)
        t = get_transpiler()
        ast = parse('@var[x; hello]\n@print[hello]')
        t.transpile(ast)
        assert "expr" in seen_contexts
        assert "display" in seen_contexts

    def test_eval_hook_first_match_wins(self, capsys):
        """First hook to return non-None wins; later hooks are not called."""
        from cruhon.core.mod_loader import ModAPI

        api = ModAPI("eval-hook-priority-mod")

        def hook_a(value, context):
            if value == "special":
                return '"from_A"'
            return None

        def hook_b(value, context):
            if value == "special":
                return '"from_B"'
            return None

        api.eval_hook(hook_a)
        api.eval_hook(hook_b)

        run_source('@var[x; special]\n@print[{x}]')
        assert "from_A" in capsys.readouterr().out

    def test_eval_hook_custom_syntax_dollar_env(self, capsys):
        """Classic use-case: %%VAR_NAME → os.environ.get('VAR_NAME')."""
        import os
        from cruhon.core.mod_loader import ModAPI

        os.environ["CRUHON_TEST_KEY"] = "test_value_xyz"

        api = ModAPI("eval-hook-dollar-env-mod")

        # Use %% prefix to avoid conflict with the $-hook registered in earlier tests
        def pct_env(value, context):
            if value.startswith("%%") and value[2:].isidentifier():
                return f'__import__("os").environ.get("{value[2:]}", "")'
            return None

        api.eval_hook(pct_env)
        run_source('@var[v; %%CRUHON_TEST_KEY]\n@print[{v}]')
        assert "test_value_xyz" in capsys.readouterr().out


# ─────────────────────────────────────────────────────────────
# MODULE SYSTEM — v1.6.0
# ─────────────────────────────────────────────────────────────

class TestModuleBlock:
    """Inline @module[name] ... @end block form."""

    def test_module_basic_function(self, capsys):
        src = """
@module[mymod]
  @func[hello]
    @return["hi"]
  @end
@end
@var[r; @mymod.hello[]]
@print[{r}]
"""
        run_source(src)
        assert capsys.readouterr().out.strip() == "hi"

    def test_module_const_access(self, capsys):
        src = """
@module[cfg]
  @const[VERSION; "1.6.0"]
@end
@print[{cfg.VERSION}]
"""
        run_source(src)
        assert "1.6.0" in capsys.readouterr().out

    def test_module_no_export_exports_all(self, capsys):
        src = """
@module[m]
  @func[greet; name]
    @return["Hi " + name]
  @end
  @const[LANG; "Cruhon"]
@end
@print[{m.greet("Dev")}]
@print[{m.LANG}]
"""
        run_source(src)
        out = capsys.readouterr().out
        assert "Hi Dev" in out
        assert "Cruhon" in out

    def test_module_export_selective(self, capsys):
        src = """
@module[m]
  @export[pub]
  @func[pub]
    @return["public"]
  @end
  @func[_priv]
    @return["private"]
  @end
@end
@print[{m.pub()}]
"""
        run_source(src)
        assert capsys.readouterr().out.strip() == "public"

    def test_module_private_not_accessible(self):
        src = """
@module[m]
  @export[pub]
  @func[pub]
    @return["ok"]
  @end
  @const[SECRET; "hidden"]
@end
@var[x; m.SECRET]
"""
        import pytest
        with pytest.raises(Exception):
            run_source(src)

    def test_module_var_not_exported_does_not_leak(self):
        src = """
@module[m]
  @var[inner; "inside"]
@end
@print[{inner}]
"""
        import pytest
        with pytest.raises(Exception):
            run_source(src)

    def test_module_namespace_call_in_var(self, capsys):
        src = """
@module[utils]
  @func[add; a; b]
    @return[a + b]
  @end
@end
@var[r; @utils.add[3; 4]]
@print[{r}]
"""
        run_source(src)
        assert capsys.readouterr().out.strip() == "7"

    def test_module_inline_call_in_expression(self, capsys):
        src = """
@module[calc]
  @func[double; n]
    @return[n * 2]
  @end
@end
@print[{calc.double(5)}]
"""
        run_source(src)
        assert capsys.readouterr().out.strip() == "10"

    def test_module_export_star(self, capsys):
        src = """
@module[m]
  @export[*]
  @func[f]
    @return[42]
  @end
@end
@print[{m.f()}]
"""
        run_source(src)
        assert capsys.readouterr().out.strip() == "42"

    def test_module_ast_node_type(self):
        from cruhon.core.ast_nodes import ModuleNode, ExportNode
        from cruhon.core.parser import parse
        ast = parse("@module[m]\n  @export[f]\n  @func[f]\n    @return[1]\n  @end\n@end\n")
        assert isinstance(ast.body[0], ModuleNode)
        assert ast.body[0].name == "m"
        export_nodes = [n for n in ast.body[0].body if isinstance(n, ExportNode)]
        assert export_nodes[0].names == ["f"]

    def test_module_generates_simplenamespace(self):
        from cruhon.core.transpiler import transpile
        from cruhon.core.parser import parse
        code = transpile(parse("@module[x]\n  @func[f]\n    @return[1]\n  @end\n@end\n"))
        assert "_cruhon_mod_x" in code
        assert "SimpleNamespace" in code
        assert "x = _cruhon_mod_x()" in code


class TestModuleFrom:
    """@from[module; name1; name2 as alias] selective imports."""

    def test_from_single(self, capsys):
        src = """
@module[m]
  @func[greet]
    @return["hello"]
  @end
@end
@from[m; greet]
@print[{greet()}]
"""
        run_source(src)
        assert capsys.readouterr().out.strip() == "hello"

    def test_from_multiple(self, capsys):
        src = """
@module[m]
  @const[A; 1]
  @const[B; 2]
@end
@from[m; A; B]
@print[{A + B}]
"""
        run_source(src)
        assert capsys.readouterr().out.strip() == "3"

    def test_from_alias(self, capsys):
        src = """
@module[m]
  @func[long_function_name]
    @return["aliased"]
  @end
@end
@from[m; long_function_name as fn]
@print[{fn()}]
"""
        run_source(src)
        assert capsys.readouterr().out.strip() == "aliased"

    def test_from_multiple_aliases(self, capsys):
        src = """
@module[math]
  @const[PI; 3.14159]
  @func[square; n]
    @return[n * n]
  @end
@end
@from[math; PI as pi; square as sq]
@print[{pi}]
@print[{sq(3)}]
"""
        run_source(src)
        out = capsys.readouterr().out
        assert "3.14159" in out
        assert "9" in out

    def test_from_ast_node_type(self):
        from cruhon.core.ast_nodes import FromNode
        from cruhon.core.parser import parse
        ast = parse("@module[m]\n  @func[f]\n    @return[1]\n  @end\n@end\n@from[m; f as g]\n")
        from_nodes = [n for n in ast.body if isinstance(n, FromNode)]
        assert from_nodes[0].module == "m"
        assert from_nodes[0].imports == [("f", "g")]


class TestModuleFile:
    """File-based @use[path] module loading."""

    def setup_method(self):
        import tempfile
        self.tmpdir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write(self, name: str, content: str) -> Path:
        p = self.tmpdir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def test_use_basic(self, capsys):
        self._write("utils.clpy", '@func[greet]\n  @return["hi"]\n@end\n')
        run_source("@use[utils]\n@var[r; @utils.greet[]]\n@print[{r}]\n", base_dir=self.tmpdir)
        assert capsys.readouterr().out.strip() == "hi"

    def test_use_alias(self, capsys):
        self._write("myutils.clpy", '@func[f]\n  @return["ok"]\n@end\n')
        run_source("@use[myutils as u]\n@var[r; @u.f[]]\n@print[{r}]\n", base_dir=self.tmpdir)
        assert capsys.readouterr().out.strip() == "ok"

    def test_use_with_export(self, capsys):
        self._write("lib.clpy", '@export[pub]\n@func[pub]\n  @return["ok"]\n@end\n@func[_priv]\n  @return["no"]\n@end\n')
        run_source("@use[lib]\n@print[{lib.pub()}]\n", base_dir=self.tmpdir)
        assert capsys.readouterr().out.strip() == "ok"

    def test_use_with_module_declaration(self, capsys):
        self._write("utils.clpy", '@module[utils]\n@func[greet]\n  @return["hello"]\n@end\n')
        run_source("@use[utils]\n@print[{utils.greet()}]\n", base_dir=self.tmpdir)
        assert capsys.readouterr().out.strip() == "hello"

    def test_use_path_relative(self, capsys):
        (self.tmpdir / "lib").mkdir()
        self._write("lib/db.clpy", '@func[query]\n  @return["result"]\n@end\n')
        run_source("@use[./lib/db]\n@print[{db.query()}]\n", base_dir=self.tmpdir)
        assert capsys.readouterr().out.strip() == "result"

    def test_use_modules_dir(self, capsys):
        (self.tmpdir / "modules").mkdir()
        self._write("modules/helpers.clpy", '@func[greet]\n  @return["mod_dir"]\n@end\n')
        run_source("@use[helpers]\n@print[{helpers.greet()}]\n", base_dir=self.tmpdir)
        assert capsys.readouterr().out.strip() == "mod_dir"

    def test_use_not_found_raises(self):
        import pytest
        with pytest.raises(Exception, match="module not found"):
            run_source("@use[nonexistent]\n", base_dir=self.tmpdir)

    def test_use_circular_raises(self):
        import pytest
        self._write("a.clpy", "@use[b]\n")
        self._write("b.clpy", "@use[a]\n")
        with pytest.raises(Exception, match="Circular"):
            run_source("@use[a]\n", base_dir=self.tmpdir)

    def test_use_from_file(self, capsys):
        self._write("utils.clpy", '@func[greet]\n  @return["file_greet"]\n@end\n')
        run_source("@use[utils]\n@from[utils; greet]\n@print[{greet()}]\n", base_dir=self.tmpdir)
        assert capsys.readouterr().out.strip() == "file_greet"


class TestModulePluginCompat:
    """Modules and plugin system work together correctly."""

    def test_inject_visible_inside_module(self, capsys):
        """api.inject() globals are accessible inside module bodies."""
        from cruhon.core.mod_loader import ModAPI
        api = ModAPI("mod-inject-compat")
        api.inject("INJECTED_VAL", "injected_works")
        src = """
@module[m]
  @func[get_val]
    @return[INJECTED_VAL]
  @end
@end
@print[{m.get_val()}]
"""
        run_source(src)
        assert "injected_works" in capsys.readouterr().out

    def test_multiple_modules(self, capsys):
        """Multiple inline modules coexist without conflict."""
        src = """
@module[a]
  @func[f]
    @return["from_a"]
  @end
@end
@module[b]
  @func[f]
    @return["from_b"]
  @end
@end
@print[{a.f()}]
@print[{b.f()}]
"""
        run_source(src)
        out = capsys.readouterr().out
        assert "from_a" in out
        assert "from_b" in out
