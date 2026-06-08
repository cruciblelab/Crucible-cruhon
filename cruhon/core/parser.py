"""
cruhon/core/parser.py
=====================
Token list → AST (Abstract Syntax Tree)

Each @command is handled by a dedicated parse method.
Mods can add new command parsers via register_command().
"""

from __future__ import annotations
from typing import List, Optional, Callable
from .lexer import Token, tokenize
from .syntax_engine import get_syntax_engine
from .ast_nodes import *


# ─────────────────────────────────────────────────────────────
# PARSE ERROR
# ─────────────────────────────────────────────────────────────

class ParseError(Exception):
    def __init__(self, msg: str, line: int = 0):
        super().__init__(f"[ParseError] Line {line} — {msg}")
        self.line = line


# ─────────────────────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────────────────────

class Parser:
    """
    Converts a token list to an AST.

    Mod system:
      - register_command(name, fn) for new @commands
      - register_block_command(name, fn) for block-opening commands
      - pre/post hooks operate on tokens / AST
    """

    def __init__(self):
        self.tokens: List[Token] = []
        self.pos: int = 0
        self._commands: dict[str, Callable] = {}
        self._block_commands: dict[str, Callable] = {}
        self._pre_hooks: list = []
        self._post_hooks: list = []
        # Track inline expressions that require auto-imports
        self._needs_os: bool = False
        self._needs_requests: bool = False
        # Source lines preserved for @raw block reconstruction
        self._source_lines: list = []
        self._register_core_commands()

    # ── Mod API ───────────────────────────────────────────────

    def register_command(self, name: str, fn: Callable):
        """
        Register a new inline command.
        fn(parser) -> Node
        """
        self._commands[name] = fn

    def register_block_command(self, name: str, fn: Callable):
        """Register a block-opening command (closed by @end)."""
        self._block_commands[name] = fn

    def add_pre_hook(self, fn: Callable):
        """Token manipulation before parsing."""
        self._pre_hooks.append(fn)

    def add_post_hook(self, fn: Callable):
        """AST manipulation after parsing."""
        self._post_hooks.append(fn)

    # ── Core command registration ─────────────────────────────

    def _register_core_commands(self):
        self._commands = {
            "print":    self._parse_print,
            "var":      self._parse_var,
            "const":    self._parse_const,
            "assert":   self._parse_assert,
            "env":      self._parse_env,
            "include":  self._parse_include,
            "return":   self._parse_return,
            "break":    self._parse_break,
            "continue": self._parse_continue,
            "import":   self._parse_import,
            "await":    self._parse_await,
            "fetch":    self._parse_fetch,
            "input":    self._parse_input,
            "del":      self._parse_del,
            "raise":    self._parse_raise,
        }
        self._block_commands = {
            "if":     self._parse_if,
            "for":    self._parse_for,
            "while":  self._parse_while,
            "func":   self._parse_func,
            "class":  self._parse_class,
            "try":    self._parse_try,
            "async":  self._parse_async_func,
            "repeat": self._parse_repeat,
            "raw":    self._parse_raw,
            "with":   self._parse_with,
            "match":  self._parse_match,
        }

    # ── Token navigation ──────────────────────────────────────

    @property
    def current(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token("EOF", "", 0)

    def peek(self, offset=1) -> Token:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else Token("EOF", "", 0)

    def advance(self) -> Token:
        tok = self.current
        self.pos += 1
        return tok

    def skip_newlines(self):
        while self.current.type in ("NEWLINE", "COMMENT"):
            self.advance()

    def expect(self, type_: str, value: str = None) -> Token:
        tok = self.current
        if tok.type != type_:
            raise ParseError(f"Expected {type_!r}, got {tok.type!r} ({tok.value!r})", tok.line)
        if value and tok.value != value:
            raise ParseError(f"Expected {value!r}, got {tok.value!r}", tok.line)
        return self.advance()

    # ── Main parse ────────────────────────────────────────────

    def parse(self, source: str) -> ProgramNode:
        self.tokens = tokenize(source)
        self.pos = 0
        self._needs_os = False
        self._needs_requests = False
        # Store source lines so @raw can reconstruct original indented content
        self._source_lines = source.splitlines()

        for hook in self._pre_hooks:
            self.tokens = hook(self.tokens)

        program = ProgramNode(line=1)
        program.body = self._parse_block()

        for hook in self._post_hooks:
            program = hook(program)

        return program

    def _parse_block(self, stop_at: tuple = ()) -> List[Node]:
        """Parse all statements in a block."""
        nodes = []

        while self.current.type != "EOF":
            self.skip_newlines()

            if self.current.type == "EOF":
                break

            # Block closing keywords
            if self.current.type == "AT_CMD" and self.current.value in (
                "end", "else", "elif", "catch", "finally", "case", "default"
            ):
                break

            if self.current.type in ("DEDENT",):
                self.advance()
                continue

            node = self._parse_statement()
            if node:
                nodes.append(node)

        return nodes

    def _parse_statement(self) -> Optional[Node]:
        """Parse a single statement."""
        self.skip_newlines()

        if self.current.type == "EOF":
            return None

        if self.current.type == "INDENT":
            self.advance()
            return None

        # Namespace command: @requests.get[...]
        if self.current.type == "NAMESPACE":
            return self._parse_namespace_call()

        # @ command
        if self.current.type == "AT_CMD":
            cmd = self.current.value

            if cmd in self._block_commands:
                return self._block_commands[cmd]()

            if cmd in self._commands:
                return self._commands[cmd]()

            custom_node = get_custom_node(cmd)
            if custom_node:
                self.advance()
                args = self.parse_args()
                return custom_node(*args, line=self.current.line)

            raise ParseError(f"Unknown command: @{cmd}", self.current.line)

        tok = self.advance()
        return ExprNode(expr=tok.value, line=tok.line)

    # ── Argument reader ───────────────────────────────────────

    def _parse_namespace_inline(self) -> str:
        """
        Parse a namespaced inline call inside an argument context.
        e.g. @store.get["key"]     → __cruhon_store_get("key")  (stdlib)
             @http.get["url"]      → requests.get("url")         (stdlib)
             @discord.get_user[id] → __ns__["discord"].call("get_user", id) (mod)
        Returns the Python expression string.
        """
        from .registry import get_lib_call, get_lib
        line = self.current.line
        namespace = self.advance().value  # NAMESPACE token
        self.advance()                    # DOT
        method = self.advance().value     # AT_CMD token
        args = self.parse_args()

        # Stdlib lib call
        handler = get_lib_call(namespace, method)
        if handler:
            return handler(args)

        # Mod namespace inline — emit runtime dispatch expression
        from .registry import is_lib_namespace
        if not is_lib_namespace(namespace):
            args_str = ", ".join(args)
            if args_str:
                return f'__ns__["{namespace}"].call("{method}", {args_str})'
            return f'__ns__["{namespace}"].call("{method}")'

        # Fallback
        args_str = ", ".join(args)
        return f"{namespace}.{method}({args_str})"

    def _parse_inline_expr(self) -> str:
        """
        Parse a nested inline @command inside an argument context.
        Returns its Python expression string directly so it can be
        embedded as a value in @var, @print, etc.

        Called when we see AT_CMD inside parse_args().
        """
        cmd = self.current.value
        line = self.current.line

        # Inline expression commands — produce a Python expression string
        inline_expr_cmds = {"env", "list", "dict", "fetch", "ctx"}

        if cmd in inline_expr_cmds:
            if cmd == "env":
                self.advance()  # @env
                self._needs_os = True
                args = self.parse_args()
                key = args[0].strip('"') if args else ""
                if len(args) > 1:
                    return f'os.environ.get("{key}", {args[1]})'
                return f'os.environ.get("{key}")'

            elif cmd == "list":
                self.advance()  # @list
                args = self.parse_args()
                items = ", ".join(args)
                return f"[{items}]"

            elif cmd == "dict":
                self.advance()  # @dict
                args = self.parse_args()
                if len(args) % 2 != 0:
                    raise ParseError("@dict requires an even number of arguments (key; value pairs)", line)
                pairs = []
                for i in range(0, len(args), 2):
                    pairs.append(f"{args[i]}: {args[i+1]}")
                return "{" + ", ".join(pairs) + "}"

            elif cmd == "fetch":
                self.advance()  # @fetch
                self._needs_requests = True
                args = self.parse_args()
                url = args[0] if args else '""'
                return f"requests.get({url})"

            elif cmd == "ctx":
                self.advance()  # @ctx
                args = self.parse_args()
                key = args[0] if args else '""'
                default = args[1] if len(args) > 1 else "None"
                return f"__ctx__.get({key}, {default})"

        # Unknown inline command — raise error with line info
        raise ParseError(
            f"@{cmd} cannot be used as an inline expression. "
            f"Supported inline commands: @env, @list, @dict, @fetch",
            self.current.line,
        )

    def parse_args(self) -> List[str]:
        """
        @command[arg1; arg2; arg3] → ['arg1', 'arg2', 'arg3']

        The token stream is consumed until the closing ] at depth 0.
        Inline @commands and @namespace.method calls are resolved first.
        The remaining raw content is split by SyntaxEngine.split_args(),
        which correctly handles nested brackets, parens, braces and strings.
        """
        if self.current.type != "LBRACKET":
            return []

        self.advance()  # consume the opening [

        # Collect raw parts. We track bracket depth so nested [...]
        # inside an argument value are not confused with the closing ] of
        # the @command argument list.
        raw_parts: list = []
        has_inline = False
        depth = 0  # depth > 0 means we are inside a nested bracket

        while self.current.type not in ("EOF",):
            tok = self.current

            # The closing ] at depth 0 ends the argument list
            if tok.type == "RBRACKET" and depth == 0:
                self.advance()
                break

            if tok.type in ("NEWLINE", "INDENT", "DEDENT", "COMMENT"):
                self.advance()
                continue

            # Inline @command — resolve now, treat as opaque expression
            if tok.type == "AT_CMD" and depth == 0:
                inline = self._parse_inline_expr()
                raw_parts.append(inline)
                has_inline = True
                continue

            # Inline @namespace.method[...] — resolve now
            if tok.type == "NAMESPACE" and depth == 0:
                inline = self._parse_namespace_inline()
                raw_parts.append(inline)
                has_inline = True
                continue

            # Track bracket depth for nested [...] inside argument values
            if tok.type == "LBRACKET":
                depth += 1
                raw_parts.append("[")
                self.advance()
                continue

            if tok.type == "RBRACKET":
                # depth > 0 here (checked depth==0 at loop top)
                depth -= 1
                raw_parts.append("]")
                self.advance()
                continue

            # STRING token — reconstruct with quotes so split_args sees it quoted
            if tok.type == "STRING":
                raw_parts.append(f'"{tok.value}"')
            elif tok.type == "SEMICOLON":
                # Keep semicolons in the raw string — split_args handles them
                raw_parts.append(";")
            else:
                raw_parts.append(tok.value)

            self.advance()

        # Join all collected parts and split at top-level ; using SyntaxEngine
        raw_source = " ".join(raw_parts)
        engine = get_syntax_engine()
        args = engine.split_args(raw_source)

        # Validate each argument for unbalanced parentheses.
        # Skip when all parts came from inline resolution (already valid Python).
        if not (has_inline and len(args) == 1):
            for arg in args:
                engine.validate_arg(arg, self.current.line)

        return args

    def parse_plugin_block(self, plugin_name: str) -> "PluginBlockNode":
        """
        Convenience parser for plugin block commands registered via
        api.block_command(). Handles args + body + @end automatically.

        Plugins that use api.block_command() never call this directly —
        it is called by the lambda registered in the parser.
        """
        line = self.current.line
        self.advance()  # consume the command token
        args, kwargs = self.parse_named_args()

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return PluginBlockNode(plugin_name=plugin_name, args=args, kwargs=kwargs, body=body, line=line)

    def parse_named_args(self) -> tuple[list[str], dict[str, str]]:
        """
        Parse @command[pos1; pos2; key=value; key2=value2]
        Returns (positional_args, kwargs).

        Positional args are returned as strings (same as parse_args).
        Keyword args are returned as {key: value_string} dict.

        Usage:
            args, kwargs = self.parse_named_args()
            url   = args[0]
            reason = kwargs.get("reason", "")
        """
        raw_args = self.parse_args()
        engine = get_syntax_engine()
        # Re-join and re-split to apply named-arg detection.
        # parse_args() already resolved inline @commands, so join them
        # back with ; and run split_named_args on the result.
        rejoined = " ; ".join(raw_args)
        return engine.split_named_args(rejoined)

    def _parse_single_arg(self) -> str:
        """Read a single argument."""
        args = self.parse_args()
        return args[0] if args else ""

    # ── Core command parse methods ────────────────────────────

    def _parse_print(self) -> PrintNode:
        line = self.current.line
        self.advance()  # @print
        args = self.parse_args()
        value = args[0] if args else ""
        return PrintNode(value=value, line=line)

    def _parse_var(self) -> VarNode:
        line = self.current.line
        self.advance()  # @var
        args = self.parse_args()
        if len(args) < 2:
            raise ParseError("@var requires [name; value]", line)
        return VarNode(name=args[0], value=args[1], line=line)

    def _parse_const(self) -> ConstNode:
        line = self.current.line
        self.advance()  # @const
        args = self.parse_args()
        if len(args) < 2:
            raise ParseError("@const requires [NAME; value]", line)
        return ConstNode(name=args[0], value=args[1], line=line)

    def _parse_assert(self) -> AssertNode:
        line = self.current.line
        self.advance()  # @assert
        args = self.parse_args()
        if not args:
            raise ParseError("@assert requires [condition; message]", line)
        condition = args[0]
        message = args[1] if len(args) > 1 else '""'
        return AssertNode(condition=condition, message=message, line=line)

    def _parse_env(self) -> EnvNode:
        line = self.current.line
        self.advance()  # @env
        args = self.parse_args()
        if not args:
            raise ParseError("@env requires [KEY] or [KEY; default]", line)
        key = args[0].strip('"')
        default = args[1] if len(args) > 1 else None
        return EnvNode(key=key, default=default, line=line)

    def _parse_include(self) -> IncludeNode:
        line = self.current.line
        self.advance()  # @include
        args = self.parse_args()
        if not args:
            raise ParseError("@include requires [filepath.clpy]", line)
        path = args[0].strip('"')
        return IncludeNode(path=path, line=line)

    def _parse_fetch(self) -> FetchNode:
        line = self.current.line
        self.advance()  # @fetch
        args = self.parse_args()
        url = args[0] if args else '""'
        return FetchNode(url=url, line=line)

    def _parse_input(self) -> InputNode:
        line = self.current.line
        self.advance()  # @input
        args = self.parse_args()
        prompt = args[0] if args else '""'
        return InputNode(prompt=prompt, line=line)

    def _parse_return(self) -> ReturnNode:
        line = self.current.line
        self.advance()
        args = self.parse_args()
        return ReturnNode(value=args[0] if args else "None", line=line)

    def _parse_break(self) -> BreakNode:
        line = self.current.line
        self.advance()
        return BreakNode(line=line)

    def _parse_continue(self) -> ContinueNode:
        line = self.current.line
        self.advance()
        return ContinueNode(line=line)

    def _parse_import(self) -> ImportNode:
        line = self.current.line
        self.advance()
        args = self.parse_args()
        lib = args[0] if args else ""
        alias = args[1] if len(args) > 1 else None
        return ImportNode(lib=lib, alias=alias, line=line)

    def _parse_await(self) -> AwaitNode:
        line = self.current.line
        self.advance()
        args = self.parse_args()
        return AwaitNode(expr=args[0] if args else "", line=line)

    def _parse_if(self) -> IfNode:
        line = self.current.line
        self.advance()  # @if
        condition = self._parse_single_arg()

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block(stop_at=("end", "else", "elif"))
        elif_branches = []
        else_body = []

        while self.current.type == "AT_CMD" and self.current.value == "elif":
            self.advance()
            elif_cond = self._parse_single_arg()
            self.skip_newlines()
            if self.current.type == "INDENT":
                self.advance()
            elif_body = self._parse_block(stop_at=("end", "else", "elif"))
            elif_branches.append((elif_cond, elif_body))

        if self.current.type == "AT_CMD" and self.current.value == "else":
            self.advance()
            self.skip_newlines()
            if self.current.type == "INDENT":
                self.advance()
            else_body = self._parse_block(stop_at=("end",))

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return IfNode(
            condition=condition,
            body=body,
            elif_branches=elif_branches,
            else_body=else_body,
            line=line
        )

    def _parse_for(self) -> ForNode:
        line = self.current.line
        self.advance()  # @for
        args = self.parse_args()
        if len(args) < 2:
            raise ParseError("@for requires [var; iterable]", line)

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return ForNode(var=args[0], iterable=args[1], body=body, line=line)

    def _parse_while(self) -> WhileNode:
        line = self.current.line
        self.advance()  # @while
        condition = self._parse_single_arg()

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return WhileNode(condition=condition, body=body, line=line)

    def _parse_repeat(self) -> RepeatNode:
        line = self.current.line
        self.advance()  # @repeat
        args = self.parse_args()
        if not args:
            raise ParseError("@repeat requires [n]", line)
        count = args[0]

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return RepeatNode(count=count, body=body, line=line)

    def _parse_func(self) -> FuncNode:
        line = self.current.line
        self.advance()  # @func
        args = self.parse_args()
        if not args:
            raise ParseError("@func requires at least a name", line)

        name = args[0]
        params = args[1:]

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return FuncNode(name=name, params=params, body=body, line=line)

    def _parse_async_func(self) -> FuncNode:
        line = self.current.line
        self.advance()  # @async
        args = self.parse_args()
        if not args:
            raise ParseError("@async requires at least a name", line)

        name = args[0]
        params = args[1:]

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return FuncNode(name=name, params=params, body=body, is_async=True, line=line)

    def _parse_class(self) -> ClassNode:
        line = self.current.line
        self.advance()  # @class
        args = self.parse_args()
        if not args:
            raise ParseError("@class requires a name", line)

        name = args[0]
        parent = args[1] if len(args) > 1 else None

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return ClassNode(name=name, parent=parent, body=body, line=line)

    def _parse_try(self) -> TryNode:
        line = self.current.line
        self.advance()  # @try

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()
        catch_var = "e"
        catch_body = []
        finally_body = []

        if self.current.type == "AT_CMD" and self.current.value == "catch":
            self.advance()
            args = self.parse_args()
            catch_var = args[0] if args else "e"
            self.skip_newlines()
            if self.current.type == "INDENT":
                self.advance()
            catch_body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "finally":
            self.advance()
            self.skip_newlines()
            if self.current.type == "INDENT":
                self.advance()
            finally_body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return TryNode(
            body=body,
            catch_var=catch_var,
            catch_body=catch_body,
            finally_body=finally_body,
            line=line
        )

    def _parse_del(self) -> "DelNode":
        line = self.current.line
        self.advance()  # @del
        args = self.parse_args()
        return DelNode(targets=args, line=line)

    def _parse_raise(self) -> "RaiseNode":
        line = self.current.line
        self.advance()  # @raise
        args = self.parse_args()
        if not args:
            return RaiseNode(exception="", message=None, line=line)  # bare re-raise
        exception = args[0]
        message = args[1] if len(args) > 1 else None
        return RaiseNode(exception=exception, message=message, line=line)

    def _parse_with(self) -> "WithNode":
        line = self.current.line
        self.advance()  # @with
        args = self.parse_args()
        raw = args[0] if args else ""

        # Split "expr as var" pattern
        var = None
        if " as " in raw:
            expr_part, var_part = raw.split(" as ", 1)
            expr = expr_part.strip()
            var = var_part.strip()
        else:
            expr = raw.strip()

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return WithNode(expr=expr, var=var, body=body, line=line)

    def _parse_match(self) -> "MatchNode":
        line = self.current.line
        self.advance()  # @match
        args = self.parse_args()
        value = args[0] if args else ""

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        cases = []
        default_body = []

        while self.current.type != "EOF":
            self.skip_newlines()

            if self.current.type in ("DEDENT",):
                self.advance()
                continue

            if self.current.type == "AT_CMD" and self.current.value == "end":
                self.advance()
                break

            if self.current.type == "AT_CMD" and self.current.value == "case":
                self.advance()  # @case
                case_args = self.parse_args()
                pattern = case_args[0] if case_args else "_"

                self.skip_newlines()
                if self.current.type == "INDENT":
                    self.advance()

                case_body = self._parse_block()
                cases.append((pattern, case_body))

            elif self.current.type == "AT_CMD" and self.current.value == "default":
                self.advance()  # @default
                self.skip_newlines()
                if self.current.type == "INDENT":
                    self.advance()

                default_body = self._parse_block()

            else:
                break

        return MatchNode(value=value, cases=cases, default_body=default_body, line=line)

    def _parse_raw(self):
        """
        @raw
            # Python code
        @end

        Reads lines from the original source between the @raw line and @end,
        preserving indentation exactly. Uses stored _source_lines so that
        Python-style indented code (class bodies, nested defs, etc.) passes
        through correctly.
        """
        from .ast_nodes import RawNode
        raw_line_num = self.current.line  # 1-based line of @raw token
        self.advance()  # consume @raw token

        # _source_lines is 0-based; @raw is at index (raw_line_num - 1),
        # so content starts at index raw_line_num (= the line after @raw).
        content_start = raw_line_num

        # Advance the token stream to @end, recording the line number.
        # We must handle INDENT/DEDENT tokens that precede @end — they appear
        # before the @end AT_CMD on the same logical line and must be skipped.
        end_line_num = len(self._source_lines) + 1
        while self.current.type != "EOF":
            tok = self.current
            if tok.type in ("NEWLINE", "COMMENT", "INDENT", "DEDENT"):
                self.advance()
                continue
            if tok.type == "AT_CMD" and tok.value == "end":
                end_line_num = tok.line  # 1-based
                self.advance()  # consume @end
                break
            # Advance past all other tokens on this line
            while self.current.type not in ("NEWLINE", "EOF"):
                if self.current.type == "AT_CMD" and self.current.value == "end":
                    end_line_num = self.current.line
                    self.advance()
                    break
                self.advance()
            else:
                continue
            break

        # Extract original source lines between @raw and @end (exclusive)
        # Lines are 1-based; _source_lines is 0-based
        raw_lines = self._source_lines[content_start:end_line_num - 1]

        # Strip the common leading indentation introduced by the @raw block indent
        # (e.g. if @raw is inside @func, the content has 4 extra spaces we should remove)
        if raw_lines:
            # Find minimum non-empty indentation
            non_empty = [ln for ln in raw_lines if ln.strip()]
            if non_empty:
                min_indent = min(len(ln) - len(ln.lstrip()) for ln in non_empty)
            else:
                min_indent = 0
            raw_lines = [ln[min_indent:] if len(ln) >= min_indent else ln
                         for ln in raw_lines]

        # Drop leading/trailing blank lines
        while raw_lines and not raw_lines[0].strip():
            raw_lines.pop(0)
        while raw_lines and not raw_lines[-1].strip():
            raw_lines.pop()

        code = "\n".join(raw_lines)
        return RawNode(code=code, line=raw_line_num)

    def _parse_namespace_call(self) -> Node:
        """
        Route namespace calls to the correct node type:
          @math.sqrt[16]     → LibCallNode (stdlib — stateless)
          @discord.send["hi"] → NamespaceCallNode (mod — stateful runtime)
        """
        line = self.current.line
        namespace = self.advance().value  # NAMESPACE token
        self.advance()                    # DOT
        method = self.advance().value     # AT_CMD token (method name)
        args = self.parse_args()

        # Stdlib namespaces have a registered lib module → LibCallNode
        from .registry import is_lib_namespace
        if is_lib_namespace(namespace):
            return LibCallNode(namespace=namespace, method=method, args=args, line=line)

        # Everything else is a mod namespace → NamespaceCallNode
        from .ast_nodes import NamespaceCallNode
        return NamespaceCallNode(namespace=namespace, method=method, args=args, line=line)


# ─────────────────────────────────────────────────────────────
# SINGLETON
# ─────────────────────────────────────────────────────────────

_parser_instance = Parser()


def get_parser() -> Parser:
    return _parser_instance


def parse(source: str) -> ProgramNode:
    return _parser_instance.parse(source)
