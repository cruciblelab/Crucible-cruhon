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
        self._inline_commands: dict[str, Callable] = {}
        self._pre_hooks: list = []
        self._post_hooks: list = []
        # Track inline expressions that require auto-imports
        self._needs_os: bool = False
        self._needs_requests: bool = False
        # Source lines preserved for @raw block reconstruction
        self._source_lines: list = []
        # Module aliases declared in the current parse — cleared each parse()
        self._module_aliases: set = set()
        # Pending decorators accumulated before @func / @class
        self._pending_decorators: list = []
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

    def register_inline_command(self, name: str, fn: Callable):
        """
        Register an inline expression command.

        fn(parser) -> str
          Called when @name appears inside an argument context.
          fn must call parser.advance() to consume the command token,
          then optionally parser.parse_args() for arguments.
          Must return a Python expression string.
        """
        self._inline_commands[name] = fn

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
            "pass":     self._parse_pass,
            "global":   self._parse_global,
            "nonlocal": self._parse_nonlocal,
            "yield":    self._parse_yield,
            "decorate": self._parse_decorate,
            "inc":      self._parse_inc,
            "dec":      self._parse_dec,
            "swap":     self._parse_swap,
        }
        self._block_commands = {
            "if":        self._parse_if,
            "for":       self._parse_for,
            "while":     self._parse_while,
            "func":      self._parse_func,
            "class":     self._parse_class,
            "try":       self._parse_try,
            "async":     self._parse_async_func,
            "repeat":    self._parse_repeat,
            "raw":       self._parse_raw,
            "with":      self._parse_with,
            "match":     self._parse_match,
            "module":    self._parse_module,
            "foreach":   self._parse_foreach,
            "decorator": self._parse_decorator,
            "retry":     self._parse_retry,
            "timeout":   self._parse_timeout,
            "macro":     self._parse_macro,
            "template":  self._parse_template,
            "dataclass": self._parse_dataclass,
        }
        self._commands.update({
            "export":   self._parse_export,
            "use":      self._parse_use,
            "from":     self._parse_from,
            "call":     self._parse_call,
            "let":      self._parse_let,
            "pipeline": self._parse_pipeline,
            "spread":   self._parse_spread,
            "unpack":   self._parse_unpack,
            "apply":    self._parse_apply,
            "render":   self._parse_render,
            "type":     self._parse_type,
        })

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

        self._module_aliases = set()
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
            # @yield.from[expr]
            if self.current.value == "yield" and self.peek(2).type == "AT_CMD" and self.peek(2).value == "from":
                return self._parse_yield_from()
            # @async.for / @async.with are block commands
            if self.current.value == "async" and self.peek(2).type == "AT_CMD":
                method = self.peek(2).value
                if method in ("for", "with"):
                    return self._parse_async_block()

            # Custom plugin commands registered with a "." in their name
            # (api.command("ns.method", ...) / api.block_command("ns.method",
            # ...)) must be checked before falling through to generic
            # namespace-call routing below. The lexer always splits "a.b"
            # into NAMESPACE + DOT + AT_CMD tokens regardless of whether
            # "a.b" was registered as one dotted command name — without this
            # check, a dotted plugin command is silently unreachable and
            # gets misparsed as a stdlib/mod namespace method call instead,
            # producing wrong code with no error.
            if self.peek(2).type == "AT_CMD":
                dotted = f"{self.current.value}.{self.peek(2).value}"
                if dotted in self._block_commands:
                    line = self.current.line
                    self.advance()  # NAMESPACE
                    self.advance()  # DOT
                    self.advance()  # AT_CMD (method)
                    return self._finish_plugin_block(dotted, line)
                if dotted in self._commands:
                    self.advance()  # NAMESPACE
                    self.advance()  # DOT
                    # AT_CMD (method) is left as self.current — the
                    # registered parser_fn consumes it itself via its own
                    # parser.advance() call, per the api.command() contract.
                    return self._commands[dotted]()

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

        # User module alias → direct attribute call
        if namespace in self._module_aliases:
            args_str = ", ".join(args)
            return f"{namespace}.{method}({args_str})"

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
        inline_expr_cmds = {
            "env", "list", "dict", "fetch", "ctx", "lambda", "comp", "pipe",
            "dictcomp", "setcomp", "gencomp", "set", "tuple", "when", "default",
            "input", "call", "spread", "unpack", "apply", "render",
        }

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

            elif cmd == "lambda":
                # @lambda[params; body]  or  @lambda[body]  (no params)
                self.advance()  # @lambda
                args = self.parse_args()
                if len(args) >= 2:
                    params = args[0]
                    body = args[1]
                    return f"(lambda {params}: {body})"
                elif args:
                    return f"(lambda: {args[0]})"
                raise ParseError("@lambda requires [body] or [params; body]", line)

            elif cmd == "comp":
                # @comp[expr; var; iterable]
                # @comp[expr; var; iterable; condition]
                # @comp[expr; var; iterable; type=dict|set|gen]
                # @comp[expr; var; iterable; condition; type=dict|set|gen]
                self.advance()  # @comp
                args = self.parse_args()
                if len(args) < 3:
                    raise ParseError("@comp requires [expr; var; iterable]", line)
                expr, var, iterable = args[0], args[1], args[2]
                # Extract type= kwarg and optional condition from remaining args
                comp_type = "list"
                cond = None
                for a in args[3:]:
                    stripped = a.strip()
                    if stripped.startswith("type="):
                        comp_type = stripped[5:].strip().strip("\"'")
                    else:
                        cond = stripped
                core = f"{expr} for {var} in {iterable}" + (f" if {cond}" if cond else "")
                if comp_type == "dict":
                    return "{" + core + "}"
                elif comp_type == "set":
                    return "{" + core + "}"
                elif comp_type in ("gen", "generator"):
                    return f"({core})"
                return f"[{core}]"

            elif cmd == "pipe":
                # @pipe[value; fn1; fn2; fn3] → fn3(fn2(fn1(value)))
                self.advance()  # @pipe
                args = self.parse_args()
                if len(args) < 2:
                    raise ParseError("@pipe requires [value; fn1; fn2; ...]", line)
                result = args[0]
                for fn in args[1:]:
                    result = f"{fn}({result})"
                return result

            elif cmd == "dictcomp":
                # @dictcomp[key; value; var; iterable]  (+ optional condition)
                self.advance()  # @dictcomp
                args = self.parse_args()
                if len(args) < 4:
                    raise ParseError(
                        "@dictcomp requires [key; value; var; iterable] or [...; cond]", line)
                key, value, var, iterable = args[0], args[1], args[2], args[3]
                if len(args) >= 5:
                    return "{" + f"{key}: {value} for {var} in {iterable} if {args[4]}" + "}"
                return "{" + f"{key}: {value} for {var} in {iterable}" + "}"

            elif cmd == "setcomp":
                # @setcomp[expr; var; iterable]  (+ optional condition)
                self.advance()  # @setcomp
                args = self.parse_args()
                if len(args) < 3:
                    raise ParseError(
                        "@setcomp requires [expr; var; iterable] or [...; cond]", line)
                expr, var, iterable = args[0], args[1], args[2]
                if len(args) >= 4:
                    return "{" + f"{expr} for {var} in {iterable} if {args[3]}" + "}"
                return "{" + f"{expr} for {var} in {iterable}" + "}"

            elif cmd == "gencomp":
                # @gencomp[expr; var; iterable]  (+ optional condition)
                self.advance()  # @gencomp
                args = self.parse_args()
                if len(args) < 3:
                    raise ParseError(
                        "@gencomp requires [expr; var; iterable] or [...; cond]", line)
                expr, var, iterable = args[0], args[1], args[2]
                if len(args) >= 4:
                    return f"({expr} for {var} in {iterable} if {args[3]})"
                return f"({expr} for {var} in {iterable})"

            elif cmd == "set":
                # @set[a; b; c] → {a, b, c}   ;   @set[] → set()
                self.advance()  # @set
                args = self.parse_args()
                if not args:
                    return "set()"
                return "{" + ", ".join(args) + "}"

            elif cmd == "tuple":
                # @tuple[a; b] → (a, b)  ;  @tuple[a] → (a,)  ;  @tuple[] → ()
                self.advance()  # @tuple
                args = self.parse_args()
                if not args:
                    return "()"
                if len(args) == 1:
                    return f"({args[0]},)"
                return "(" + ", ".join(args) + ")"

            elif cmd == "when":
                # @when[cond; yes; no] → (yes if cond else no)
                self.advance()  # @when
                args = self.parse_args()
                if len(args) < 3:
                    raise ParseError("@when requires [condition; if_true; if_false]", line)
                return f"({args[1]} if {args[0]} else {args[2]})"

            elif cmd == "default":
                # @default[value; fallback] → (value if value is not None else fallback)
                self.advance()  # @default
                args = self.parse_args()
                if len(args) < 2:
                    raise ParseError("@default requires [value; fallback]", line)
                return f"({args[0]} if {args[0]} is not None else {args[1]})"

            elif cmd == "input":
                # @input[prompt] as inline expression → input("prompt")
                self.advance()  # @input
                args = self.parse_args()
                if not args:
                    return "input()"
                p = args[0]
                # Wrap bare text in quotes (mirrors visit_InputNode display context)
                if p and not (p.startswith('"') or p.startswith("'")):
                    p = f'"{p}"'
                return f"input({p})"

            elif cmd == "call":
                # @call[name; arg1; arg2] as inline expression → __macro_name(arg1, arg2)
                self.advance()  # @call
                args = self.parse_args()
                if not args:
                    raise ParseError("@call requires a macro name", line)
                macro_name = args[0].strip()
                call_args = ", ".join(args[1:])
                return f"__macro_{macro_name}({call_args})"

            elif cmd == "spread":
                # @spread[fn; iterable] → fn(*iterable)
                self.advance()  # @spread
                args = self.parse_args()
                if len(args) < 2:
                    raise ParseError("@spread requires [fn; iterable]", line)
                return f"{args[0]}(*{args[1]})"

            elif cmd == "unpack":
                # @unpack[fn; mapping] → fn(**mapping)
                self.advance()  # @unpack
                args = self.parse_args()
                if len(args) < 2:
                    raise ParseError("@unpack requires [fn; mapping]", line)
                return f"{args[0]}(**{args[1]})"

            elif cmd == "apply":
                # @apply[pipeline_name; value] → __pipeline_name(value)
                self.advance()  # @apply
                args = self.parse_args()
                if len(args) < 2:
                    raise ParseError("@apply requires [pipeline_name; value]", line)
                pipeline_name = args[0].strip()
                return f"__pipeline_{pipeline_name}({args[1]})"

            elif cmd == "render":
                # @render[name; k=v; ...] → __tmpl_name.format_map({...})
                self.advance()  # @render
                args = self.parse_args()
                if not args:
                    raise ParseError("@render requires a template name", line)
                tmpl_name = args[0].strip()
                pairs = []
                for a in args[1:]:
                    a = a.strip()
                    eq = a.find("=")
                    if eq > 0:
                        k = a[:eq].strip()
                        v = a[eq + 1:].strip()
                        pairs.append(f'"{k}": {v}')
                mapping = "{" + ", ".join(pairs) + "}" if pairs else "{}"
                return f"__tmpl_{tmpl_name}.format_map({mapping})"

        # Plugin-registered inline commands
        if cmd in self._inline_commands:
            return self._inline_commands[cmd](self)

        # Unknown inline command — raise error with line info
        builtin = ("@env, @list, @dict, @fetch, @ctx, @lambda, @comp, @pipe, "
                   "@dictcomp, @setcomp, @gencomp, @set, @tuple, @when, @default, @input")
        plugin_names = ", ".join(f"@{k}" for k in self._inline_commands) if self._inline_commands else ""
        available = f"{builtin}{', ' + plugin_names if plugin_names else ''}"
        raise ParseError(
            f"@{cmd} cannot be used as an inline expression. "
            f"Supported inline commands: {available}",
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

            # STRING token — reconstruct with quotes so split_args sees it quoted.
            # Use single quotes when the value contains double quotes to avoid
            # producing malformed Python literals like "say "hello"".
            if tok.type == "STRING":
                val = tok.value
                if '"' in val:
                    if "'" not in val:
                        raw_parts.append(f"'{val}'")
                    else:
                        escaped = val.replace('"', '\\"')
                        raw_parts.append(f'"{escaped}"')
                else:
                    raw_parts.append(f'"{val}"')
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
        return self._finish_plugin_block(plugin_name, line)

    def _finish_plugin_block(self, plugin_name: str, line: int) -> "PluginBlockNode":
        """
        Shared tail of plugin-block parsing: args + body + @end.

        Split out from parse_plugin_block() so callers that consume the
        leading command token(s) themselves — e.g. dotted block-command
        names spread across NAMESPACE + DOT + AT_CMD tokens, see
        _parse_statement() — can reuse this without a redundant advance().
        """
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
        import re as _re
        line = self.current.line
        self.advance()  # @print
        args = self.parse_args()
        # Separate sep= and end= kwargs from positional args
        positional = []
        sep = None
        end_ = None
        for arg in args:
            m = _re.match(r'^(sep|end)\s*=\s*(.+)$', arg.strip())
            if m:
                if m.group(1) == "sep":
                    sep = m.group(2)
                else:
                    end_ = m.group(2)
            else:
                positional.append(arg)
        value = positional[0] if positional else ""
        extra = positional[1:]
        return PrintNode(value=value, extra=extra, sep=sep, end=end_, line=line)

    def _parse_var(self) -> VarNode:
        line = self.current.line
        self.advance()  # @var
        args = self.parse_args()
        if not args:
            raise ParseError("@var requires [name; value] or [name: type; value]", line)
        raw_name = args[0]
        type_hint = None
        if ": " in raw_name:
            name_part, type_part = raw_name.split(": ", 1)
            name = name_part.strip()
            type_hint = type_part.strip()
        else:
            name = raw_name
        value = args[1] if len(args) > 1 else None
        if value is None and type_hint is None:
            raise ParseError("@var requires [name; value]", line)
        return VarNode(name=name, value=value, type_hint=type_hint, line=line)

    def _parse_const(self) -> ConstNode:
        line = self.current.line
        self.advance()  # @const
        args = self.parse_args()
        if not args:
            raise ParseError("@const requires [NAME; value] or [NAME: type; value]", line)
        raw_name = args[0]
        type_hint = None
        if ": " in raw_name:
            name_part, type_part = raw_name.split(": ", 1)
            name = name_part.strip()
            type_hint = type_part.strip()
        else:
            name = raw_name
        value = args[1] if len(args) > 1 else None
        if value is None and type_hint is None:
            raise ParseError("@const requires [NAME; value]", line)
        return ConstNode(name=name, value=value, type_hint=type_hint, line=line)

    def _parse_assert(self) -> AssertNode:
        line = self.current.line
        self.advance()  # @assert
        args = self.parse_args()
        if not args:
            raise ParseError("@assert requires [condition] or [condition; message]", line)
        condition = args[0]
        message = args[1] if len(args) > 1 else None
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

    def _parse_module(self) -> ModuleNode:
        line = self.current.line
        self.advance()  # @module
        args = self.parse_args()
        name = args[0].strip("\"'") if args else ""
        self._module_aliases.add(name)
        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()
        body = self._parse_block()
        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()
        return ModuleNode(name=name, body=body, line=line)

    def _parse_export(self) -> ExportNode:
        line = self.current.line
        self.advance()  # @export
        args = self.parse_args()
        names = [a.strip("\"'") for a in args]
        return ExportNode(names=names, line=line)

    def _parse_use(self) -> UseNode:
        line = self.current.line
        self.advance()  # @use
        args = self.parse_args()
        raw = args[0].strip("\"'") if args else ""
        if " as " in raw:
            path, alias = raw.split(" as ", 1)
            path = path.strip()
            alias = alias.strip()
        else:
            path = raw
            # Derive alias from the last path segment, strip extension
            seg = path.rstrip("/").rsplit("/", 1)[-1]
            if "." in seg:
                seg = seg.rsplit(".", 1)[0]
            alias = seg.replace("-", "_").replace(".", "_")
        self._module_aliases.add(alias)
        return UseNode(path=path, alias=alias, line=line)

    def _parse_from(self) -> FromNode:
        line = self.current.line
        self.advance()  # @from
        args = self.parse_args()
        module = args[0].strip("\"'") if args else ""
        imports = []
        for spec in args[1:]:
            spec = spec.strip().strip("\"'")
            if " as " in spec:
                name, alias = spec.split(" as ", 1)
                imports.append((name.strip(), alias.strip()))
            else:
                imports.append((spec.strip(), spec.strip()))
        return FromNode(module=module, imports=imports, line=line)

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
        raw = args[0] if args else ""
        # Support "numpy as np" inline alias syntax
        if " as " in raw:
            lib_part, alias_part = raw.split(" as ", 1)
            lib = lib_part.strip()
            alias = alias_part.strip()
        else:
            lib = raw.strip()
            alias = args[1].strip() if len(args) > 1 else None
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

        body = self._parse_block(stop_at=("end", "else"))
        else_body: list = []

        if self.current.type == "AT_CMD" and self.current.value == "else":
            self.advance()
            self.skip_newlines()
            if self.current.type == "INDENT":
                self.advance()
            else_body = self._parse_block(stop_at=("end",))

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return ForNode(var=args[0], iterable=args[1], body=body, else_body=else_body, line=line)

    def _parse_while(self) -> WhileNode:
        line = self.current.line
        self.advance()  # @while
        condition = self._parse_single_arg()

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block(stop_at=("end", "else"))
        else_body: list = []

        if self.current.type == "AT_CMD" and self.current.value == "else":
            self.advance()
            self.skip_newlines()
            if self.current.type == "INDENT":
                self.advance()
            else_body = self._parse_block(stop_at=("end",))

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return WhileNode(condition=condition, body=body, else_body=else_body, line=line)

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

    def _parse_decorator(self):
        # @decorator[fn]  or  @decorator[fn1; fn2; ...]
        # Accumulates into _pending_decorators; consumed by the next @func/@class.
        line = self.current.line
        self.advance()  # @decorator
        args = self.parse_args()
        for a in args:
            self._pending_decorators.append(a.strip())
        return None   # no AST node emitted — decorators attach to the next def/class

    def _parse_func(self) -> FuncNode:
        line = self.current.line
        self.advance()  # @func
        args = self.parse_args()
        if not args:
            raise ParseError("@func requires at least a name", line)

        name = args[0]
        return_type = None
        params = []
        for p in args[1:]:
            stripped = p.strip()
            if stripped.startswith("return="):
                return_type = stripped[len("return="):].strip()
            else:
                params.append(p)
        decs = self._pending_decorators[:]
        self._pending_decorators.clear()

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return FuncNode(name=name, params=params, body=body, line=line,
                        decorators=decs, return_type=return_type)

    def _parse_async_func(self) -> FuncNode:
        line = self.current.line
        self.advance()  # @async
        args = self.parse_args()
        if not args:
            raise ParseError("@async requires at least a name", line)

        name = args[0]
        return_type = None
        params = []
        for p in args[1:]:
            stripped = p.strip()
            if stripped.startswith("return="):
                return_type = stripped[len("return="):].strip()
            else:
                params.append(p)
        decs = self._pending_decorators[:]
        self._pending_decorators.clear()

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return FuncNode(name=name, params=params, body=body, is_async=True, line=line,
                        decorators=decs, return_type=return_type)

    def _parse_class(self) -> ClassNode:
        line = self.current.line
        self.advance()  # @class
        args = self.parse_args()
        if not args:
            raise ParseError("@class requires a name", line)

        name = args[0]
        parent = ", ".join(a.strip() for a in args[1:]) if len(args) > 1 else None
        decs = self._pending_decorators[:]
        self._pending_decorators.clear()

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return ClassNode(name=name, parent=parent, body=body, line=line, decorators=decs)

    def _parse_type(self) -> TypeAliasNode:
        line = self.current.line
        self.advance()  # @type
        args = self.parse_args()
        if len(args) < 2:
            raise ParseError("@type requires [Name; Alias]", line)
        return TypeAliasNode(name=args[0].strip(), alias=args[1].strip(), line=line)

    def _parse_dataclass(self) -> DataclassNode:
        line = self.current.line
        self.advance()  # @dataclass
        args = self.parse_args()
        if not args:
            raise ParseError("@dataclass requires a name", line)
        name = args[0].strip()
        parent = args[1].strip() if len(args) > 1 else None
        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()
        body = self._parse_block()
        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()
        return DataclassNode(name=name, parent=parent, body=body, line=line)

    def _parse_try(self) -> TryNode:
        line = self.current.line
        self.advance()  # @try

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()
        catch_clauses = []
        finally_body = []

        while self.current.type == "AT_CMD" and self.current.value == "catch":
            self.advance()
            args = self.parse_args()
            exc_type = None
            var = "e"
            if len(args) >= 2:
                exc_type = args[0].strip()
                var = args[1].strip()
            elif len(args) == 1:
                a = args[0].strip()
                if a and (a[0].isupper() or "." in a or "," in a):
                    exc_type = a
                    var = ""
                else:
                    var = a
            self.skip_newlines()
            if self.current.type == "INDENT":
                self.advance()
            cb = self._parse_block()
            catch_clauses.append((exc_type, var, cb))

        else_body: list = []
        if self.current.type == "AT_CMD" and self.current.value == "else":
            self.advance()
            self.skip_newlines()
            if self.current.type == "INDENT":
                self.advance()
            else_body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "finally":
            self.advance()
            self.skip_newlines()
            if self.current.type == "INDENT":
                self.advance()
            finally_body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        # Populate legacy single-catch fields for backward compat
        first = catch_clauses[0] if catch_clauses else (None, "e", [])
        return TryNode(
            body=body,
            catch_clauses=catch_clauses,
            else_body=else_body,
            catch_var=first[1],
            catch_type=first[0],
            catch_body=first[2],
            finally_body=finally_body,
            line=line
        )

    def _parse_del(self) -> "DelNode":
        line = self.current.line
        self.advance()  # @del
        args = self.parse_args()
        return DelNode(targets=args, line=line)

    def _parse_raise(self) -> "RaiseNode":
        import re as _re
        line = self.current.line
        self.advance()  # @raise
        args = self.parse_args()
        if not args:
            return RaiseNode(exception="", message=None, line=line)  # bare re-raise
        positional = []
        cause = None
        for arg in args:
            m = _re.match(r'^from\s*=\s*(.+)$', arg.strip())
            if m:
                cause = m.group(1).strip()
            else:
                positional.append(arg)
        exception = positional[0] if positional else ""
        message = positional[1] if len(positional) > 1 else None
        return RaiseNode(exception=exception, message=message, cause=cause, line=line)

    def _parse_with(self) -> "WithNode":
        line = self.current.line
        self.advance()  # @with
        args = self.parse_args()

        def _split_as(raw: str):
            raw = raw.strip()
            if " as " in raw:
                e, v = raw.split(" as ", 1)
                return e.strip(), v.strip()
            return raw, None

        managers = [_split_as(a) for a in args] if args else [("", None)]

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        expr, var = managers[0]
        return WithNode(expr=expr, var=var, body=body, managers=managers, line=line)

    def _parse_async_block(self) -> Node:
        """Dispatch @async.for / @async.with to their respective parsers."""
        line = self.current.line
        self.advance()  # NAMESPACE "async"
        self.advance()  # DOT
        method = self.advance().value  # AT_CMD "for" or "with"

        if method == "for":
            return self._parse_async_for_block(line)
        elif method == "with":
            return self._parse_async_with_block(line)
        raise ParseError(f"Unknown @async.{method}", line)

    def _parse_async_for_block(self, line: int) -> "AsyncForNode":
        args = self.parse_args()
        if len(args) < 2:
            raise ParseError("@async.for requires [var; iterable]", line)
        var = args[0].strip()
        iterable = args[1].strip()

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return AsyncForNode(var=var, iterable=iterable, body=body, line=line)

    def _parse_async_with_block(self, line: int) -> "AsyncWithNode":
        args = self.parse_args()
        raw = args[0] if args else ""

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

        return AsyncWithNode(expr=expr, var=var, body=body, line=line)

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

    def _parse_pass(self) -> "PassNode":
        line = self.current.line
        self.advance()  # @pass
        return PassNode(line=line)

    def _parse_global(self) -> "GlobalNode":
        line = self.current.line
        self.advance()  # @global
        args = self.parse_args()
        names = [a.strip() for a in args]
        return GlobalNode(names=names, line=line)

    def _parse_nonlocal(self) -> "NonlocalNode":
        line = self.current.line
        self.advance()  # @nonlocal
        args = self.parse_args()
        names = [a.strip() for a in args]
        return NonlocalNode(names=names, line=line)

    def _parse_yield(self) -> "YieldNode":
        line = self.current.line
        self.advance()  # @yield
        args = self.parse_args()
        value = args[0] if args else None
        return YieldNode(value=value, is_from=False, line=line)

    def _parse_yield_from(self) -> "YieldNode":
        line = self.current.line
        self.advance()  # NAMESPACE "yield"
        self.advance()  # DOT
        self.advance()  # AT_CMD "from"
        args = self.parse_args()
        value = args[0] if args else ""
        return YieldNode(value=value, is_from=True, line=line)

    def _parse_decorate(self) -> "DecorateNode":
        line = self.current.line
        self.advance()  # @decorate
        args = self.parse_args()
        expr = args[0] if args else ""
        return DecorateNode(expr=expr, line=line)

    def _parse_foreach(self) -> "ForeachNode":
        line = self.current.line
        self.advance()  # @foreach
        args = self.parse_args()
        if len(args) < 3:
            raise ParseError("@foreach requires [index; var; iterable] or [index; var; iterable; start]", line)
        index = args[0].strip()
        var = args[1].strip()
        iterable = args[2].strip()
        start = args[3].strip() if len(args) >= 4 else "0"

        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()

        body = self._parse_block()

        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()

        return ForeachNode(index=index, var=var, iterable=iterable, start=start, body=body, line=line)

    def _parse_inc(self) -> "IncNode":
        line = self.current.line
        self.advance()  # @inc
        args = self.parse_args()
        if not args:
            raise ParseError("@inc requires [target] or [target; amount]", line)
        target = args[0].strip()
        amount = args[1].strip() if len(args) > 1 else "1"
        return IncNode(target=target, amount=amount, line=line)

    def _parse_dec(self) -> "DecNode":
        line = self.current.line
        self.advance()  # @dec
        args = self.parse_args()
        if not args:
            raise ParseError("@dec requires [target] or [target; amount]", line)
        target = args[0].strip()
        amount = args[1].strip() if len(args) > 1 else "1"
        return DecNode(target=target, amount=amount, line=line)

    def _parse_swap(self) -> "SwapNode":
        line = self.current.line
        self.advance()  # @swap
        args = self.parse_args()
        if len(args) < 2:
            raise ParseError("@swap requires [a; b]", line)
        return SwapNode(left=args[0].strip(), right=args[1].strip(), line=line)

    def _parse_retry(self) -> "RetryNode":
        from .ast_nodes import RetryNode
        line = self.current.line
        self.advance()  # @retry
        args = self.parse_args()
        times = args[0].strip() if args else "3"
        exc_type = args[1].strip() if len(args) > 1 else None
        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()
        body = self._parse_block()
        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()
        return RetryNode(times=times, exc_type=exc_type, body=body, line=line)

    def _parse_timeout(self) -> "TimeoutNode":
        from .ast_nodes import TimeoutNode
        line = self.current.line
        self.advance()  # @timeout
        args = self.parse_args()
        seconds = args[0].strip() if args else "30"
        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()
        body = self._parse_block()
        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()
        return TimeoutNode(seconds=seconds, body=body, line=line)

    def _parse_macro(self) -> "MacroDefNode":
        from .ast_nodes import MacroDefNode
        line = self.current.line
        self.advance()  # @macro
        args = self.parse_args()
        if not args:
            raise ParseError("@macro requires at least a name", line)
        name = args[0].strip()
        params = [a.strip() for a in args[1:]]
        self.skip_newlines()
        if self.current.type == "INDENT":
            self.advance()
        body = self._parse_block()
        if self.current.type == "AT_CMD" and self.current.value == "end":
            self.advance()
        return MacroDefNode(name=name, params=params, body=body, line=line)

    def _parse_call(self) -> "MacroCallNode":
        from .ast_nodes import MacroCallNode
        line = self.current.line
        self.advance()  # @call
        args = self.parse_args()
        if not args:
            raise ParseError("@call requires a macro name", line)
        name = args[0].strip()
        call_args = list(args[1:])
        return MacroCallNode(name=name, args=call_args, line=line)

    def _parse_template(self) -> "TemplateDefNode":
        from .ast_nodes import TemplateDefNode
        tmpl_line = self.current.line
        self.advance()  # @template
        args = self.parse_args()
        if not args:
            raise ParseError("@template requires a name", tmpl_line)
        name = args[0].strip()

        # Body capture — same pattern as _parse_raw
        content_start = tmpl_line  # 0-based index of line after @template
        end_line_num = len(self._source_lines) + 1
        while self.current.type != "EOF":
            tok = self.current
            if tok.type in ("NEWLINE", "COMMENT", "INDENT", "DEDENT"):
                self.advance()
                continue
            if tok.type == "AT_CMD" and tok.value == "end":
                end_line_num = tok.line
                self.advance()
                break
            while self.current.type not in ("NEWLINE", "EOF"):
                if self.current.type == "AT_CMD" and self.current.value == "end":
                    end_line_num = self.current.line
                    self.advance()
                    break
                self.advance()
            else:
                continue
            break

        raw_lines = self._source_lines[content_start:end_line_num - 1]
        if raw_lines:
            non_empty = [ln for ln in raw_lines if ln.strip()]
            if non_empty:
                min_indent = min(len(ln) - len(ln.lstrip()) for ln in non_empty)
            else:
                min_indent = 0
            raw_lines = [ln[min_indent:] if len(ln) >= min_indent else ln
                         for ln in raw_lines]
        while raw_lines and not raw_lines[0].strip():
            raw_lines.pop(0)
        while raw_lines and not raw_lines[-1].strip():
            raw_lines.pop()

        body = "\n".join(raw_lines)
        return TemplateDefNode(name=name, body=body, line=tmpl_line)

    def _parse_let(self) -> "LetNode":
        from .ast_nodes import LetNode
        line = self.current.line
        self.advance()  # @let
        args = self.parse_args()
        if len(args) % 2 != 0:
            raise ParseError(
                "@let requires an even number of arguments (name; value pairs)", line)
        pairs = [(args[i].strip(), args[i + 1]) for i in range(0, len(args), 2)]
        return LetNode(pairs=pairs, line=line)

    def _parse_pipeline(self) -> "PipelineNode":
        from .ast_nodes import PipelineNode
        line = self.current.line
        self.advance()  # @pipeline
        args = self.parse_args()
        if not args:
            raise ParseError("@pipeline requires at least a name", line)
        name = args[0].strip()
        funcs = [a.strip() for a in args[1:]]
        return PipelineNode(name=name, funcs=funcs, line=line)

    def _parse_spread(self) -> "ExprNode":
        from .ast_nodes import ExprNode
        line = self.current.line
        self.advance()  # @spread
        args = self.parse_args()
        if len(args) < 2:
            raise ParseError("@spread requires [fn; iterable]", line)
        return ExprNode(expr=f"{args[0]}(*{args[1]})", line=line)

    def _parse_unpack(self) -> "ExprNode":
        from .ast_nodes import ExprNode
        line = self.current.line
        self.advance()  # @unpack
        args = self.parse_args()
        if len(args) < 2:
            raise ParseError("@unpack requires [fn; mapping]", line)
        return ExprNode(expr=f"{args[0]}(**{args[1]})", line=line)

    def _parse_apply(self) -> "ExprNode":
        from .ast_nodes import ExprNode
        line = self.current.line
        self.advance()  # @apply
        args = self.parse_args()
        if len(args) < 2:
            raise ParseError("@apply requires [pipeline_name; value]", line)
        pipeline_name = args[0].strip()
        return ExprNode(expr=f"__pipeline_{pipeline_name}({args[1]})", line=line)

    def _parse_render(self) -> "ExprNode":
        from .ast_nodes import ExprNode
        line = self.current.line
        self.advance()  # @render
        args = self.parse_args()
        if not args:
            raise ParseError("@render requires a template name", line)
        tmpl_name = args[0].strip()
        pairs = []
        for a in args[1:]:
            a = a.strip()
            eq = a.find("=")
            if eq > 0:
                k = a[:eq].strip()
                v = a[eq + 1:].strip()
                pairs.append(f'"{k}": {v}')
        mapping = "{" + ", ".join(pairs) + "}" if pairs else "{}"
        return ExprNode(expr=f"__tmpl_{tmpl_name}.format_map({mapping})", line=line)

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
