"""
cruhon/core/transpiler.py
=========================
AST → Python source code

Each Node type has a visit_* method.
Mods can add new visit methods via register_visitor().

v0.5: _interpolate() and _as_string() replaced by a single
      _eval_value(value, context) method.
"""

from __future__ import annotations
import re
from typing import List, Callable
from .ast_nodes import *


class TranspileError(Exception):
    def __init__(self, msg: str, line: int = 0):
        super().__init__(f"[TranspileError] Line {line} — {msg}")
        self.line = line


class Transpiler:
    """
    Converts an AST to Python code.

    Mod system:
      - register_visitor(node_class, fn) for new node support
      - pre_hooks: AST manipulation before code generation
      - post_hooks: manipulation of generated Python code

    Line mapping:
      _line_map maps generated Python line numbers → Cruhon source lines.
      Used by runner.py to produce helpful error messages.
    """

    def __init__(self):
        self._indent = 0
        self._custom_visitors: dict = {}
        self._visitor_owners: dict = {}        # node_name → plugin_name
        self._block_visitors: dict = {}        # plugin_name → visitor_fn
        self._scoped_blocks: set = set()       # plugin names with auto ctx save/restore
        self._node_transforms: dict = {}       # plugin_name → [transform_fn, ...]
        self._block_hooks: dict = {}           # "enter"|"exit" → [fn, ...]
        self._ast_hooks: dict = {}             # node_type_name → [fn(node) → node, ...]
        self._eval_hooks: list = []            # fn(value, context) → str | None
        self._pre_hooks: list = []
        self._post_hooks: list = []
        self._known_modules: set = set()       # module names for namespace call routing
        # Line map: python_line (1-based) → cruhon_line
        self._line_map: dict[int, int] = {}
        self._python_line: int = 1

    # ── Mod API ───────────────────────────────────────────────

    def register_visitor(self, node_class: type, fn: Callable):
        """
        Register a visitor for a new node type.

        Example:
            def visit_db_get(transpiler, node):
                return transpiler._line(f"db.get({node.table!r}, {node.key!r})")

            transpiler.register_visitor(DbGetNode, visit_db_get)
        """
        self._custom_visitors[node_class.__name__] = fn

    def add_pre_hook(self, fn: Callable):
        self._pre_hooks.append(fn)

    def add_post_hook(self, fn: Callable):
        self._post_hooks.append(fn)

    # ── Main transpile ────────────────────────────────────────

    def _apply_ast_hooks(self, ast: ProgramNode) -> ProgramNode:
        """Walk the AST and apply registered ast_hooks to matching nodes."""

        def transform_node(node):
            node_type = node.__class__.__name__
            for fn in self._ast_hooks.get(node_type, []):
                node = fn(node)
            return node

        def transform_body(nodes):
            if not nodes:
                return nodes
            result = []
            for node in nodes:
                node = transform_node(node)
                for attr in ("body", "else_body", "catch_body", "finally_body", "default_body"):
                    children = getattr(node, attr, None)
                    if children and isinstance(children, list):
                        setattr(node, attr, transform_body(children))
                if hasattr(node, "elif_branches") and node.elif_branches:
                    node.elif_branches = [
                        (cond, transform_body(body))
                        for cond, body in node.elif_branches
                    ]
                if hasattr(node, "cases") and node.cases:
                    node.cases = [
                        (pattern, transform_body(body))
                        for pattern, body in node.cases
                    ]
                result.append(node)
            return result

        ast.body = transform_body(ast.body)
        return ast

    def transpile(self, ast: ProgramNode) -> str:
        self._indent = 0
        self._line_map = {}
        self._python_line = 1
        self._known_modules = set()  # Populated by _collect_imports after hooks

        # AST hooks — parse-time transforms registered by plugins
        if self._ast_hooks:
            ast = self._apply_ast_hooks(ast)

        # Pre-hooks
        for hook in self._pre_hooks:
            ast = hook(ast)

        lines = []

        # Collect lib imports at top
        import_lines = self._collect_imports(ast)
        if import_lines:
            lines.extend(import_lines)
            # Count the import lines to keep _python_line in sync
            self._python_line += len(import_lines) + 1  # +1 for blank line
            lines.append("")

        # Main code
        for node in ast.body:
            if not isinstance(node, (ImportNode, IncludeNode, UseNode)):
                result = node.accept(self)
                if result:
                    lines.append(result)

        code = "\n".join(lines)

        # Post-hooks
        for hook in self._post_hooks:
            code = hook(code)

        return code

    def _collect_imports(self, ast: ProgramNode) -> List[str]:
        """
        Collect ImportNodes, detect auto-required imports, and populate
        self._known_modules — all in a single AST walk.

        Running after ast_hooks and pre-hooks means _known_modules correctly
        reflects any node renames those hooks may have applied.
        """
        from .registry import get_lib, is_lib_namespace, _BUILTIN
        from .parser import get_parser as _gp
        lines = []
        seen = set()

        # Explicit @import statements
        for node in ast.body:
            if isinstance(node, ImportNode):
                lib_module = get_lib(node.lib)
                if lib_module is None:
                    if is_lib_namespace(node.lib):
                        raise TranspileError(
                            f"@{node.lib} is a builtin namespace — no @import needed. "
                            f"Use @{node.lib}.command[...] directly.",
                            node.line
                        )
                    # Unknown library: emit a plain Python import and let the
                    # runtime decide whether the package is installed.
                    alias = f" as {node.alias}" if node.alias else ""
                    stmt = f"import {node.lib}{alias}"
                    if stmt not in seen:
                        seen.add(stmt)
                        lines.append(stmt)
                    continue
                # Builtin Cruhon namespace — no import statement needed
                if lib_module == _BUILTIN:
                    raise TranspileError(
                        f"@{node.lib} is a builtin namespace — no @import needed. "
                        f"Use @{node.lib}.command[...] directly.",
                        node.line
                    )
                alias = f" as {node.alias}" if node.alias else ""
                stmt = f"import {lib_module}{alias}"
                if stmt not in seen:
                    seen.add(stmt)
                    lines.append(stmt)

        # Single unified scan: populate _known_modules + all auto-import flags
        # (Note: _known_modules is already initialized in transpile() at start)
        _p = _gp()
        needs_os = _p._needs_os
        needs_requests = _p._needs_requests
        needs_store = False
        needs_types = False
        for _n in _walk_ast(ast):
            if not needs_os and isinstance(_n, EnvNode):
                needs_os = True
            if not needs_requests and isinstance(_n, FetchNode):
                needs_requests = True
            if not needs_store and isinstance(_n, LibCallNode) and _n.namespace == "store":
                needs_store = True
            if isinstance(_n, ModuleNode):
                needs_types = True
                self._known_modules.add(_n.name)

        if needs_os:
            stmt = "import os"
            if stmt not in seen:
                seen.add(stmt)
                lines.insert(0, stmt)

        if needs_requests:
            stmt = "import requests"
            if stmt not in seen:
                seen.add(stmt)
                lines.append(stmt)

        if needs_store:
            for hl in _STORE_HELPERS.splitlines():
                lines.append(hl)

        if needs_types:
            stmt = "import types as _cruhon_types"
            if stmt not in seen:
                seen.add(stmt)
                lines.append(stmt)

        return lines

    # ── Line emit ─────────────────────────────────────────────

    def _line(self, code: str, cruhon_line: int = 0) -> str:
        """Emit one indented line of Python, recording its source map entry."""
        if cruhon_line > 0:
            self._line_map[self._python_line] = cruhon_line
        self._python_line += 1
        return "    " * self._indent + code

    def _block(self, nodes: List[Node]) -> str:
        self._indent += 1
        lines = []
        for node in nodes:
            result = node.accept(self)
            if result:
                lines.append(result)
        if not lines:
            lines.append(self._line("pass"))
        self._indent -= 1
        return "\n".join(lines)

    # ── Single evaluation rule ────────────────────────────────

    def _eval_value(self, value: str, context: str = "expr") -> str:
        """
        Single evaluation rule for all values in Cruhon.

        context:
          "expr"    — right-hand side of @var, @return, @const, @fetch url
                      identifiers remain as Python identifiers (variable references)
          "display" — @print value, @assert message
                      bare identifiers become string literals

        Plugin eval hooks run first — if any returns non-None, that value is used
        and the default rules below are skipped entirely.

        Priority order (strict):

          0. Plugin eval hooks (api.eval_hook)
          1. Quoted string without {} → string literal as-is
          2. Quoted string with {}    → f-string
          3. Numeric literal          → as-is
          4. True / False / None      → as-is
          5. Collection literal       → as-is (starts with [ { ( )
          6. Python expression        → as-is (contains operator/call/dot/subscript)
          7a. [expr]    Single identifier → Python identifier (variable reference)
          7b. [display] Single identifier → string literal "ident"
          8. Bare text (anything else) → string literal "text"
        """
        v = value.strip()

        # ── Rule 0: plugin eval hooks ─────────────────────────
        for _hook in self._eval_hooks:
            _result = _hook(v, context)
            if _result is not None:
                return _result

        # ── Rule 0.5: Python string literal with prefix (f"", r"", b"", etc.) ──
        # Pass through as-is — wrapping would double-apply the prefix.
        if len(v) >= 3 and re.match(r'^[fFrRbBuU]{1,3}["\']', v):
            return v

        # ── Rule 1: quoted string, no interpolation ───────────
        if (v.startswith('"') and v.endswith('"') and len(v) >= 2) or \
           (v.startswith("'") and v.endswith("'") and len(v) >= 2):
            inner = v[1:-1]
            if "{" in inner and "}" in inner:
                # Rule 2: quoted + {} → f-string
                return f"f{v}"
            return v

        # ── Rule 2 (unquoted): bare {var} interpolation ───────
        # Fires when value contains {} BUT is NOT a Python expression
        # with dict literals. Two helpers below make the distinction.
        if "{" in v and "}" in v:
            if self._is_python_expression(v):
                return v          # pass through as Python expression (Rule 6 territory)
            if self._is_fstring_template(v):
                # Use single-quoted f-string when content contains double quotes
                if '"' in v:
                    return f"f'{v}'"
                return f'f"{v}"'
            # Fallthrough: only wrap as f-string in display context if { is followed
            # by an identifier start — this handles {A + B} templates while leaving
            # set literals like {1, 2} and CSS-like {!value} as raw expressions.
            if context == "display" and re.search(r'\{[a-zA-Z_]', v):
                if '"' in v:
                    return f"f'{v}'"
                return f'f"{v}"'
            return v

        # ── Rule 3: numeric literal ───────────────────────────
        try:
            float(v)
            return v
        except ValueError:
            pass

        # ── Rule 3b: hex / octal / binary integer literals ────
        _nv = v.lstrip("-").lstrip("+")
        if _nv.startswith(("0x", "0X", "0o", "0O", "0b", "0B")) and len(_nv) > 2:
            try:
                int(v, 0)
                return v
            except ValueError:
                pass

        # ── Rule 4: True / False / None ───────────────────────
        if v in ("True", "False", "None"):
            return v

        # ── Rule 5: collection literal ────────────────────────
        if (v.startswith("{") and v.endswith("}")) or \
           (v.startswith("[") and v.endswith("]")) or \
           (v.startswith("(") and v.endswith(")")):
            return v

        # ── Rule 6: Python expression ─────────────────────────
        # In display context, only treat as expression if it has call/subscript/dot
        # (things that unambiguously look like Python). Operators alone are not
        # enough — "x is great" contains " is " but is not a Python expression.
        operators = [
            "+", "-", "*", "/", "%", "**", "//",
            "==", "!=", ">=", "<=", ">", "<",
            " and ", " or ", " not ", " in ", " is ",
            " not in ", " is not ",
            " if ", " else ",   # ternary: a if cond else b
            " for ", " yield ", " await ",  # comprehension / coroutine
            ":=",               # walrus
            " lambda ",         # lambda expr
        ]
        has_operator = any(op in v for op in operators)
        has_call = "(" in v and ")" in v
        has_subscript = "[" in v and "]" in v
        # Require an identifier char on BOTH sides of the dot (obj.attr-shaped),
        # not just any "." — otherwise bare prose ending in a period (e.g.
        # "@print[Done.]", extremely common with the bare-text → string rule)
        # is misdetected as Python attribute access and fails to compile.
        has_dot = bool(re.search(r'[a-zA-Z0-9_]\.[a-zA-Z_]', v))

        if context == "expr":
            if has_operator or has_call or has_subscript or has_dot:
                return v
        else:
            # display: only pass through if it has structural expression markers
            # (call, subscript, dot) — operators alone could be inside plain text
            if has_call or has_subscript or has_dot:
                return v

        # ── Rule 7: single identifier ─────────────────────────
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            if context == "expr":
                return v           # 7a: variable reference
            else:
                return f'"{v}"'    # 7b: display — treat as string

        # ── Rule 8: bare text → string literal ────────────────
        return f'"{v}"'

    def _is_fstring_template(self, value: str) -> bool:
        """
        True if value is a genuine f-string interpolation template —
        i.e. contains {identifier} or {expression} meant for substitution.

        Returns False for Python expressions that happen to contain braces
        (dict literals, sets, format specs inside function calls).
        """
        import re
        if "{" not in value or "}" not in value:
            return False
        # Python expressions are never f-string templates
        if self._is_python_expression(value):
            return False
        # Match {identifier}, {attr.path}, or {func_call(…)} patterns
        return bool(
            re.search(r'\{[a-zA-Z_][a-zA-Z0-9_.]*\}', value) or   # {var} or {obj.attr}
            re.search(r'\{[a-zA-Z_][a-zA-Z0-9_.]*\(', value)       # {func( or {obj.method(
        )

    def _is_python_expression(self, value: str) -> bool:
        """
        True if value is a Python expression containing braces as dict
        literals or function arguments — NOT f-string interpolation templates.

        Cases handled:
          func({"key": val})   — function call with dict arg
          __import__('x')(…)   — stdlib inline call with dict
          {"key": val}         — plain dict literal
          {key: val}           — dict with variable key
          await expr           — async expression
        """
        import re
        brace_pos = value.find("{")
        if brace_pos == -1:
            return False

        # Rule 1: function call ( appears before first {  → dict inside a call
        paren_pos = value.find("(")
        if paren_pos != -1 and paren_pos < brace_pos:
            return True

        # Rule 2: { immediately followed by quote → {"key": ...} dict literal
        if re.search(r'\{["\']', value):
            return True

        # Rule 3: starts with { and contains : AND the leading { is the ONLY
        # top-level brace group spanning the whole value → plain dict literal
        # {key: val}. Guards against f-string templates with multiple groups
        # that happen to have a literal ":" after them, e.g.
        # "{u['id']}: {u['name']}" (NOT a dict — two interpolations plus text).
        if value.startswith("{") and ":" in value and self._is_single_brace_group(value):
            return True

        # Rule 4: assignment (=) before the first { → var = {"key": val}
        eq_pos = value.find("=")
        if eq_pos != -1 and eq_pos < brace_pos:
            return True

        return False

    def _is_single_brace_group(self, value: str) -> bool:
        """
        True if value is exactly one balanced {...} span with nothing before
        the opening brace or after its matching closing brace — i.e. a real
        standalone dict/set literal, not an f-string template with multiple
        {..} interpolation groups plus literal text (which merely starts
        with { and happens to contain a ":" later on).
        """
        v = value.strip()
        if not v.startswith("{"):
            return False
        depth = 0
        in_str = None
        i, n = 0, len(v)
        while i < n:
            ch = v[i]
            if in_str:
                if ch == "\\":
                    i += 2
                    continue
                if ch == in_str:
                    in_str = None
            elif ch in ("'", '"'):
                in_str = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i == n - 1
            i += 1
        return False

    def visit_unknown(self, node: Node) -> str:
        """Unknown node — check mod visitors."""
        node_name = node.__class__.__name__
        if node_name in self._custom_visitors:
            owner = self._visitor_owners.get(node_name, "unknown plugin")
            try:
                return self._custom_visitors[node_name](self, node)
            except Exception as e:
                raise TranspileError(
                    f"Plugin '{owner}' visitor for '{node_name}' raised {type(e).__name__}: {e}",
                    node.line
                ) from e
        return self._line(f"# Unknown node: {node_name}")

    # ── Core visitors ─────────────────────────────────────────

    def visit_ProgramNode(self, node: ProgramNode) -> str:
        lines = []
        for child in node.body:
            result = child.accept(self)
            if result:
                lines.append(result)
        return "\n".join(lines)

    def visit_PrintNode(self, node: PrintNode) -> str:
        values = [self._eval_value(str(node.value), "display")]
        for extra in (node.extra or []):
            values.append(self._eval_value(str(extra), "display"))
        kwargs = []
        if node.sep is not None:
            kwargs.append(f"sep={node.sep}")
        if node.end is not None:
            kwargs.append(f"end={node.end}")
        all_args = ", ".join(values + kwargs)
        return self._line(f"print({all_args})", node.line)

    def visit_InputNode(self, node: InputNode) -> str:
        prompt = self._eval_value(str(node.prompt), "display") if node.prompt else '""'
        return self._line(f"input({prompt})", node.line)

    def visit_VarNode(self, node: VarNode) -> str:
        if "," in node.name:
            return self._line(f"{node.name} = {node.value}", node.line)
        if node.type_hint is not None:
            if node.value is None:
                return self._line(f"{node.name}: {node.type_hint}", node.line)
            value = self._eval_value(str(node.value), "expr")
            return self._line(f"{node.name}: {node.type_hint} = {value}", node.line)
        value = self._eval_value(str(node.value), "expr")
        return self._line(f"{node.name} = {value}", node.line)

    def visit_ConstNode(self, node: ConstNode) -> str:
        if node.type_hint is not None:
            if node.value is None:
                return self._line(f"{node.name}: {node.type_hint}", node.line)
            value = self._eval_value(str(node.value), "expr")
            return self._line(f"{node.name}: {node.type_hint} = {value}  # const", node.line)
        value = self._eval_value(str(node.value), "expr")
        return self._line(f"{node.name} = {value}  # const", node.line)

    def visit_AssertNode(self, node: AssertNode) -> str:
        if node.message:
            msg = self._eval_value(str(node.message), "display")
            return self._line(f"assert {node.condition}, {msg}", node.line)
        return self._line(f"assert {node.condition}", node.line)

    def visit_EnvNode(self, node: EnvNode) -> str:
        """
        @env as a statement. When nested inside @var the parser inlines it.
        """
        if node.default is not None:
            return self._line(f'os.environ.get("{node.key}", {node.default})', node.line)
        return self._line(f'os.environ.get("{node.key}")', node.line)

    def visit_IncludeNode(self, node: IncludeNode) -> str:
        """IncludeNode should have been resolved by runner.py before transpilation."""
        return self._line(f"# @include[{node.path}] — not resolved", node.line)

    def visit_RawNode(self, node) -> str:
        """
        @raw blocks pass through unchanged.
        Each line is indented to current block level.
        """
        if not node.code.strip():
            return ""
        lines = node.code.splitlines()
        indented = []
        for line in lines:
            if line.strip():
                indented.append(self._line(line, node.line))
            else:
                indented.append("")
        return "\n".join(indented)

    def visit_ListNode(self, node: ListNode) -> str:
        """@list as a statement."""
        items = ", ".join(node.items)
        return self._line(f"[{items}]", node.line)

    def visit_DictNode(self, node: DictNode) -> str:
        """@dict as a statement."""
        pairs = ", ".join(f"{k}: {v}" for k, v in node.pairs)
        return self._line("{" + pairs + "}", node.line)

    def visit_FetchNode(self, node: FetchNode) -> str:
        """@fetch as a statement."""
        url = self._eval_value(str(node.url), "expr")
        return self._line(f"requests.get({url})", node.line)

    def visit_ReturnNode(self, node: ReturnNode) -> str:
        value = self._eval_value(str(node.value), "expr")
        return self._line(f"return {value}", node.line)

    def visit_BreakNode(self, node: BreakNode) -> str:
        return self._line("break", node.line)

    def visit_ContinueNode(self, node: ContinueNode) -> str:
        return self._line("continue", node.line)

    def visit_PassNode(self, node) -> str:
        return self._line("pass", node.line)

    def visit_GlobalNode(self, node) -> str:
        return self._line(f"global {', '.join(node.names)}", node.line)

    def visit_NonlocalNode(self, node) -> str:
        return self._line(f"nonlocal {', '.join(node.names)}", node.line)

    def visit_YieldNode(self, node) -> str:
        if node.is_from:
            return self._line(f"yield from {node.value}", node.line)
        if node.value:
            val = self._eval_value(str(node.value), "expr")
            return self._line(f"yield {val}", node.line)
        return self._line("yield", node.line)

    def visit_DecorateNode(self, node) -> str:
        return self._line(f"@{node.expr}", node.line)

    def visit_ForeachNode(self, node) -> str:
        if node.start != "0":
            enum_call = f"enumerate({node.iterable}, {node.start})"
        else:
            enum_call = f"enumerate({node.iterable})"
        lines = [self._line(f"for {node.index}, {node.var} in {enum_call}:", node.line)]
        lines.append(self._block(node.body))
        return "\n".join(lines)

    def visit_IncNode(self, node) -> str:
        amount = self._eval_value(str(node.amount), "expr")
        return self._line(f"{node.target} += {amount}", node.line)

    def visit_DecNode(self, node) -> str:
        amount = self._eval_value(str(node.amount), "expr")
        return self._line(f"{node.target} -= {amount}", node.line)

    def visit_SwapNode(self, node) -> str:
        return self._line(f"{node.left}, {node.right} = {node.right}, {node.left}", node.line)

    def visit_RetryNode(self, node) -> str:
        idx = f"__retry_i_{node.line}"
        mx = f"__retry_n_{node.line}"
        exc = node.exc_type or "Exception"
        lines = [
            self._line(f"{mx} = int({node.times})", node.line),
            self._line(f"for {idx} in range({mx}):"),
        ]
        self._indent += 1
        lines.append(self._line("try:"))
        lines.append(self._block(node.body))
        self._indent += 1
        lines.append(self._line("break"))
        self._indent -= 1
        lines.append(self._line(f"except {exc}:"))
        self._indent += 1
        lines.append(self._line(f"if {idx} >= {mx} - 1:"))
        self._indent += 1
        lines.append(self._line("raise"))
        self._indent -= 2
        self._indent -= 1
        return "\n".join(lines)

    def visit_TimeoutNode(self, node) -> str:
        fn = f"__timeout_fn_{node.line}"
        cf = f"__cf_{node.line}"
        pool = f"__pool_{node.line}"
        ft = f"__ft_{node.line}"
        s = node.seconds
        lines = [self._line(f"def {fn}():", node.line)]
        lines.append(self._block(node.body))
        lines.append(self._line(f"import concurrent.futures as {cf}"))
        lines.append(self._line(f"with {cf}.ThreadPoolExecutor(max_workers=1) as {pool}:"))
        self._indent += 1
        lines.append(self._line(f"{ft} = {pool}.submit({fn})"))
        lines.append(self._line("try:"))
        self._indent += 1
        lines.append(self._line(f"{ft}.result(timeout={s})"))
        self._indent -= 1
        lines.append(self._line(f"except {cf}.TimeoutError:"))
        self._indent += 1
        lines.append(self._line(
            f"raise TimeoutError('operation timed out after ' + str({s}) + 's')"
        ))
        self._indent -= 2
        return "\n".join(lines)

    def visit_MacroDefNode(self, node) -> str:
        params_str = ", ".join(node.params) if node.params else ""
        lines = [self._line(f"def __macro_{node.name}({params_str}):", node.line)]
        lines.append(self._block(node.body))
        return "\n".join(lines)

    def visit_MacroCallNode(self, node) -> str:
        args_str = ", ".join(node.args)
        return self._line(f"__macro_{node.name}({args_str})", node.line)

    def visit_TemplateDefNode(self, node) -> str:
        body_repr = repr(node.body)
        return self._line(f"__tmpl_{node.name} = {body_repr}", node.line)

    def visit_LetNode(self, node) -> str:
        lines = [self._line(f"{name} = {value}", node.line) for name, value in node.pairs]
        return "\n".join(lines)

    def visit_PipelineNode(self, node) -> str:
        if not node.funcs:
            return self._line(f"__pipeline_{node.name} = lambda __v: __v", node.line)
        composed = "__v"
        for fn in node.funcs:
            composed = f"({fn})({composed})"
        return self._line(f"__pipeline_{node.name} = lambda __v: {composed}", node.line)

    def visit_ExprNode(self, node: ExprNode) -> str:
        return self._line(node.expr, node.line)

    def visit_AwaitNode(self, node: AwaitNode) -> str:
        return self._line(f"await {node.expr}", node.line)

    def visit_ImportNode(self, node: ImportNode) -> str:
        return ""  # handled in _collect_imports

    def visit_IfNode(self, node: IfNode) -> str:
        lines = [self._line(f"if {node.condition}:", node.line)]
        lines.append(self._block(node.body))

        for cond, body in node.elif_branches:
            lines.append(self._line(f"elif {cond}:"))
            lines.append(self._block(body))

        if node.else_body:
            lines.append(self._line("else:"))
            lines.append(self._block(node.else_body))

        return "\n".join(lines)

    def visit_ForNode(self, node: ForNode) -> str:
        lines = [self._line(f"for {node.var} in {node.iterable}:", node.line)]
        lines.append(self._block(node.body))
        if node.else_body:
            lines.append(self._line("else:", node.line))
            lines.append(self._block(node.else_body))
        return "\n".join(lines)

    def visit_WhileNode(self, node: WhileNode) -> str:
        lines = [self._line(f"while {node.condition}:", node.line)]
        lines.append(self._block(node.body))
        if node.else_body:
            lines.append(self._line("else:", node.line))
            lines.append(self._block(node.else_body))
        return "\n".join(lines)

    def visit_RepeatNode(self, node: RepeatNode) -> str:
        lines = [self._line(f"for _ in range({node.count}):", node.line)]
        lines.append(self._block(node.body))
        return "\n".join(lines)

    def visit_FuncNode(self, node: FuncNode) -> str:
        params = list(node.params)
        # Legacy: last param starting with "->" is the return type
        return_type = ""
        if params and params[-1].strip().startswith("->"):
            return_type = " " + params[-1].strip()
            params = params[:-1]
        # New: explicit return_type field (set via return=type named arg)
        if node.return_type:
            return_type = f" -> {node.return_type}"
        params_str = ", ".join(params)
        prefix = "async " if node.is_async else ""
        lines = [self._line(f"@{d}", node.line) for d in (node.decorators or [])]
        lines.append(self._line(f"{prefix}def {node.name}({params_str}){return_type}:", node.line))
        lines.append(self._block(node.body))
        return "\n".join(lines)

    def visit_TypeAliasNode(self, node) -> str:
        return self._line(f"{node.name} = {node.alias}  # type alias", node.line)

    def visit_DataclassNode(self, node) -> str:
        parent = f"({node.parent})" if node.parent else ""
        lines = [
            self._line("from dataclasses import dataclass", node.line),
            self._line("@dataclass", node.line),
            self._line(f"class {node.name}{parent}:", node.line),
            self._block(node.body),
        ]
        return "\n".join(lines)

    def visit_ClassNode(self, node: ClassNode) -> str:
        parent = f"({node.parent})" if node.parent else ""
        lines = [self._line(f"@{d}", node.line) for d in (node.decorators or [])]
        lines.append(self._line(f"class {node.name}{parent}:", node.line))
        lines.append(self._block(node.body))
        return "\n".join(lines)

    def visit_WithNode(self, node) -> str:
        managers = node.managers if node.managers else [(node.expr, node.var)]
        parts = [f"{e} as {v}" if v else e for e, v in managers]
        header = self._line(f"with {', '.join(parts)}:", node.line)
        return "\n".join([header, self._block(node.body)])

    def visit_AsyncForNode(self, node) -> str:
        lines = [self._line(f"async for {node.var} in {node.iterable}:", node.line)]
        lines.append(self._block(node.body))
        return "\n".join(lines)

    def visit_AsyncWithNode(self, node) -> str:
        if node.var:
            header = self._line(f"async with {node.expr} as {node.var}:", node.line)
        else:
            header = self._line(f"async with {node.expr}:", node.line)
        return "\n".join([header, self._block(node.body)])

    def visit_MatchNode(self, node) -> str:
        lines = [self._line(f"match {node.value}:", node.line)]
        self._indent += 1
        for pattern, body in node.cases:
            lines.append(self._line(f"case {pattern}:"))
            lines.append(self._block(body))
        if node.default_body:
            lines.append(self._line("case _:"))
            lines.append(self._block(node.default_body))
        self._indent -= 1
        return "\n".join(lines)

    def visit_DelNode(self, node) -> str:
        targets = ", ".join(node.targets)
        return self._line(f"del {targets}", node.line)

    def visit_RaiseNode(self, node) -> str:
        if not node.exception:
            return self._line("raise", node.line)
        exc = self._eval_value(str(node.exception), "expr")
        if node.message:
            msg = self._eval_value(str(node.message), "expr")
            base = f"raise {exc}({msg})"
        else:
            base = f"raise {exc}"
        if getattr(node, "cause", None):
            base += f" from {node.cause}"
        return self._line(base, node.line)

    def visit_TryNode(self, node: TryNode) -> str:
        lines = [self._line("try:", node.line)]
        lines.append(self._block(node.body))
        # Build clause list: prefer explicit multi-catch; fall back to legacy only if
        # the legacy catch_body is non-empty. If no clauses at all (e.g. try/finally
        # without any catch) we skip the except block entirely.
        clauses = node.catch_clauses or []
        if not clauses and node.catch_body:
            clauses = [(node.catch_type, node.catch_var, node.catch_body)]
        for exc_type, var, cbody in clauses:
            if exc_type and var:
                except_line = f"except {exc_type} as {var}:"
            elif exc_type:
                except_line = f"except {exc_type}:"
            elif var:
                except_line = f"except Exception as {var}:"
            else:
                except_line = "except:"
            lines.append(self._line(except_line))
            lines.append(self._block(cbody))
        if getattr(node, "else_body", None):
            lines.append(self._line("else:"))
            lines.append(self._block(node.else_body))
        if node.finally_body:
            lines.append(self._line("finally:"))
            lines.append(self._block(node.finally_body))
        return "\n".join(lines)

    def visit_LibCallNode(self, node: LibCallNode) -> str:
        from .registry import get_lib_call
        handler = get_lib_call(node.namespace, node.method)
        if handler:
            return self._line(handler(node.args), node.line)
        # Fallback: direct Python call
        # Args are already parsed Python expressions; don't quote them
        args = ", ".join(node.args)
        return self._line(f"{node.namespace}.{node.method}({args})", node.line)

    def visit_PluginBlockNode(self, node) -> str:
        """
        Dispatch to the plugin's registered visitor with optional:
          - ctx scope isolation (scoped=True saves/restores __ctx__)
          - node transforms   (post-process generated Python code)
          - block lifecycle   (emit __ph__("enter"/"exit", name) calls)
        """
        visitor = self._block_visitors.get(node.plugin_name)
        if not visitor:
            return self._line(f"# @{node.plugin_name} block (no visitor registered)", node.line)

        try:
            parts = []

            # Block enter hook
            if self._block_hooks.get("enter"):
                parts.append(self._line(
                    f'__ph__("enter", {node.plugin_name!r}, {node.args!r})',
                    node.line
                ))

            # Ctx scope: save before body
            scoped = node.plugin_name in self._scoped_blocks
            if scoped:
                parts.append(self._line("__ctx_stack__.append(dict(__ctx__))", node.line))

            # Primary visitor
            result = visitor(self, node)

            # Apply registered transforms (other plugins can wrap this output)
            for transform_fn in self._node_transforms.get(node.plugin_name, []):
                result = transform_fn(self, node, result)

            parts.append(result)

            # Ctx scope: restore after body
            if scoped:
                parts.append(self._line(
                    "__ctx__.clear(); __ctx__.update(__ctx_stack__.pop() if __ctx_stack__ else {})"
                ))

            # Block exit hook
            if self._block_hooks.get("exit"):
                parts.append(self._line(f'__ph__("exit", {node.plugin_name!r})'))

            return "\n".join(p for p in parts if p)

        except TranspileError:
            raise
        except Exception as e:
            raise TranspileError(
                f"Block plugin '@{node.plugin_name}' raised {type(e).__name__}: {e}",
                node.line
            ) from e

    def visit_NamespaceCallNode(self, node) -> str:
        """
        Route namespace calls:
          @utils.greet[...] → utils.greet(...)       when utils is a user module
          @discord.send[...] → __ns__["discord"]...  when it is a runtime mod
        """
        args_str = ", ".join(
            self._eval_value(a, "expr") for a in node.args
        )
        if node.namespace in self._known_modules:
            if args_str:
                return self._line(f"{node.namespace}.{node.method}({args_str})", node.line)
            return self._line(f"{node.namespace}.{node.method}()", node.line)
        if args_str:
            return self._line(
                f'__ns__["{node.namespace}"].call("{node.method}", {args_str})',
                node.line
            )
        return self._line(
            f'__ns__["{node.namespace}"].call("{node.method}")',
            node.line
        )

    def visit_ModuleNode(self, node) -> str:
        """
        @module[name] ... @end

        Compiles to a Python init function that returns a SimpleNamespace
        of exported symbols. Private names (starts with _) or names not
        listed in @export stay inside the function scope and never leak.
        """
        export_names = []
        export_star = False
        body_nodes = []

        for n in node.body:
            if isinstance(n, ExportNode):
                if "*" in n.names:
                    export_star = True
                else:
                    export_names.extend(n.names)
            else:
                body_nodes.append(n)

        # No @export directive → export all non-private top-level names
        if not export_names and not export_star:
            export_star = True

        # Auto-derive only when no explicit names given; explicit list takes priority
        if export_star and not export_names:
            for n in body_nodes:
                if isinstance(n, (FuncNode, ClassNode, VarNode, ConstNode)):
                    if isinstance(n.name, str) and not n.name.startswith("_"):
                        export_names.append(n.name)

        fn_name = f"_cruhon_mod_{node.name}"
        lines = [self._line(f"def {fn_name}():", node.line)]

        # Init export dict — must precede the body
        self._indent += 1
        lines.append(self._line("_cruhon_ex = {}"))
        self._indent -= 1

        # Module body (handles its own indentation via _block)
        lines.append(self._block(body_nodes))

        # Export assignments + return at body depth
        self._indent += 1
        for name in export_names:
            lines.append(self._line(f'_cruhon_ex["{name}"] = {name}'))
        lines.append(self._line("return _cruhon_types.SimpleNamespace(**_cruhon_ex)"))
        self._indent -= 1

        # Instantiate the module
        lines.append(self._line(f"{node.name} = {fn_name}()"))

        return "\n".join(filter(None, lines))

    def visit_ExportNode(self, node) -> str:
        """@export outside a module body is a no-op (handled by visit_ModuleNode)."""
        return ""

    def visit_UseNode(self, node) -> str:
        raise TranspileError(
            f"Unresolved @use[{node.path}] — ensure resolve_modules() ran before transpile",
            node.line,
        )

    def visit_FromNode(self, node) -> str:
        """@from[module; name1; name2 as alias] → name1 = module.name1 ..."""
        if not node.imports:
            return ""
        lines = []
        for name, alias in node.imports:
            lines.append(self._line(f"{alias} = {node.module}.{name}", node.line))
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# AST WALK HELPERS (used for auto-imports)
# ─────────────────────────────────────────────────────────────

def _walk_ast(node):
    """Yield all nodes in the AST recursively."""
    yield node
    for attr in ("body", "else_body", "catch_body", "finally_body", "default_body"):
        children = getattr(node, attr, None)
        if children:
            for child in children:
                yield from _walk_ast(child)
    if hasattr(node, "elif_branches"):
        for _cond, branch_body in (node.elif_branches or []):
            for child in branch_body:
                yield from _walk_ast(child)
    if hasattr(node, "cases"):
        for _pat, case_body in (node.cases or []):
            for child in case_body:
                yield from _walk_ast(child)


def _needs_os_import(ast) -> bool:
    """Return True if the AST contains any EnvNode, or parser saw inline @env."""
    from .parser import get_parser
    if get_parser()._needs_os:
        return True
    return any(isinstance(n, EnvNode) for n in _walk_ast(ast))


def _needs_requests_import(ast) -> bool:
    """Return True if the AST contains any FetchNode, or parser saw inline @fetch."""
    from .parser import get_parser
    if get_parser()._needs_requests:
        return True
    return any(isinstance(n, FetchNode) for n in _walk_ast(ast))


def _needs_store_helpers(ast) -> str:
    """
    Return store helper code string if any @store.* LibCallNode is found,
    empty string otherwise.
    """
    for node in _walk_ast(ast):
        if isinstance(node, LibCallNode) and node.namespace == "store":
            return _STORE_HELPERS
    return ""


_STORE_HELPERS = """\
import json as __json
import os as __os

def __cruhon_store_path():
    return __os.path.join(__os.getcwd(), ".cruhon_store.json")

def __cruhon_store_load():
    p = __cruhon_store_path()
    if __os.path.exists(p):
        with open(p) as f:
            return __json.load(f)
    return {}

def __cruhon_store_set(key, value):
    d = __cruhon_store_load()
    d[key] = value
    with open(__cruhon_store_path(), "w") as f:
        __json.dump(d, f)

def __cruhon_store_get(key, default=None):
    return __cruhon_store_load().get(key, default)

def __cruhon_store_delete(key):
    d = __cruhon_store_load()
    d.pop(key, None)
    with open(__cruhon_store_path(), "w") as f:
        __json.dump(d, f)
"""


# ─────────────────────────────────────────────────────────────
# SINGLETON
# ─────────────────────────────────────────────────────────────

_transpiler_instance = Transpiler()


def get_transpiler() -> Transpiler:
    return _transpiler_instance


def transpile(ast) -> str:
    return _transpiler_instance.transpile(ast)
