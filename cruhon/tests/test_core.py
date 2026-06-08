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
