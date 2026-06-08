"""
cruhon/core/runner.py
=====================
.clpy file runner.
Lexer → Parser → Transpiler → exec()

Handles:
  - @include resolution (before transpilation)
  - Auto-import injection (os, requests, store helpers)
  - --show-python output formatting
  - Friendly error messages with Cruhon line numbers
"""

from __future__ import annotations
import traceback
from pathlib import Path
from typing import Optional

from .parser import parse, ParseError
from .transpiler import transpile, get_transpiler
from .mod_loader import fire_hook, load_all_mods, get_inject_globals
from .ast_nodes import IncludeNode, ProgramNode


class RunError(Exception):
    pass


# ─────────────────────────────────────────────────────────────
# ASYNC DETECTION
# ─────────────────────────────────────────────────────────────

def _is_async_code(python_code: str) -> bool:
    """
    Detect if generated Python code requires async execution.
    Returns True only if code defines 'async def main' — conservative
    check to avoid false positives with user-defined async helpers.
    """
    for line in python_code.splitlines():
        if line.strip().startswith("async def main"):
            return True
    return False


def _make_async_runner(python_code: str) -> str:
    """
    Append asyncio.run(main()) to code that defines async def main.
    The import is injected inline so it works inside exec() without
    relying on globals.
    """
    return python_code + "\nimport asyncio\nasyncio.run(main())"


# ─────────────────────────────────────────────────────────────
# INCLUDE RESOLUTION
# ─────────────────────────────────────────────────────────────

def resolve_includes(ast: ProgramNode, base_dir: Path, included: Optional[set] = None) -> ProgramNode:
    """
    Walk the AST, find IncludeNode instances, replace them with the
    parsed content of the referenced file.

    base_dir: directory used to resolve relative paths.
    included: set of already-included absolute paths (circular detection).
    """
    if included is None:
        included = set()

    new_body = []
    for node in ast.body:
        if isinstance(node, IncludeNode):
            include_path = Path(node.path)
            if not include_path.is_absolute():
                include_path = base_dir / include_path
            include_path = include_path.resolve()

            if include_path in included:
                raise RunError(f"Circular include detected: {node.path}")

            if not include_path.exists():
                raise RunError(f"@include: file not found: {node.path}")

            sub_source = include_path.read_text(encoding="utf-8")
            sub_ast = parse(sub_source)
            # Recursively resolve includes in the included file
            sub_ast = resolve_includes(sub_ast, include_path.parent, included | {include_path})
            new_body.extend(sub_ast.body)
        else:
            # Recurse into block nodes
            for attr in ("body", "else_body", "catch_body", "finally_body"):
                children = getattr(node, attr, None)
                if isinstance(children, list):
                    sub_prog = ProgramNode(body=children)
                    resolved = resolve_includes(sub_prog, base_dir, included)
                    setattr(node, attr, resolved.body)
            # elif_branches: list of (condition, body)
            if hasattr(node, "elif_branches"):
                new_branches = []
                for cond, branch_body in node.elif_branches:
                    sub_prog = ProgramNode(body=branch_body)
                    resolved = resolve_includes(sub_prog, base_dir, included)
                    new_branches.append((cond, resolved.body))
                node.elif_branches = new_branches
            new_body.append(node)

    ast.body = new_body
    return ast


# ─────────────────────────────────────────────────────────────
# HINT ENGINE — friendly error messages
# ─────────────────────────────────────────────────────────────

def _build_hint(exc: Exception, python_code: str, python_line: int) -> str:
    """
    Return a human-friendly hint for common runtime errors.
    Returns empty string if no hint applies.
    """
    import re

    if isinstance(exc, NameError):
        # Extract the undefined name from the error message
        m = re.search(r"name '([^']+)' is not defined", str(exc))
        if m:
            name = m.group(1)
            # Find the source line in generated Python
            lines = python_code.splitlines()
            src_line = lines[python_line - 1] if 0 < python_line <= len(lines) else ""

            # If the name appears unquoted as a value (right of = or in a call)
            # and looks like the user forgot quotes, suggest quoting.
            if re.search(rf'\b{re.escape(name)}\b', src_line):
                # Looks like a plain word value — suggest quoting
                return (
                    f"'{name}' is not defined as a variable. "
                    f"If you meant a string, add quotes: \"{name}\""
                )

    if isinstance(exc, TypeError):
        if "argument" in str(exc).lower() or "positional" in str(exc).lower():
            return "Check the number of arguments passed to the function."

    if isinstance(exc, AttributeError):
        m = re.search(r"'([^']+)' object has no attribute '([^']+)'", str(exc))
        if m:
            return f"'{m.group(1)}' has no method or property '{m.group(2)}'."

    if isinstance(exc, KeyError):
        return f"Key {exc} not found. Check the key name or use a default value."

    if isinstance(exc, IndexError):
        return "List index out of range. Check that the list has enough items."

    if isinstance(exc, ZeroDivisionError):
        return "Division by zero. Add a check before dividing."

    return ""


# ─────────────────────────────────────────────────────────────
# SHOW-PYTHON FORMATTING
# ─────────────────────────────────────────────────────────────

def _show_python_output(python_code: str):
    """Print the formatted --show-python block."""
    width = 46
    bar = "─" * width
    print(f"\n\033[90m── Generated Python {bar[:width - 19]}\033[0m")
    print(python_code)
    print(f"\033[90m{bar}\033[0m")
    print(f"\033[90m── Output {bar[:width - 9]}\033[0m")


def _show_python_end():
    width = 46
    print(f"\033[90m{'─' * width}\033[0m")


# ─────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────

def run_source(
    source: str,
    filename: str = "<clpy>",
    debug: bool = False,
    show_python: bool = False,
    base_dir: Optional[Path] = None,
    _root_path: Optional[Path] = None,
) -> str:
    """
    Run Cruhon source code. Returns the generated Python code.

    show_python: print formatted generated Python before output.
    debug: legacy alias for show_python.
    base_dir: directory for resolving @include paths.
    _root_path: absolute path of the root file (for circular include detection).
    """
    _show = show_python or debug
    if base_dir is None:
        base_dir = Path.cwd()

    transpiler = get_transpiler()

    try:
        fire_hook("before_run", source=source)

        # Parse
        ast = parse(source)

        # Resolve @include nodes before transpilation.
        # Seed the included set with the root file so indirect cycles (A→B→C→A)
        # are caught in addition to direct cycles (A→B→A).
        initial_included = {_root_path} if _root_path else set()
        ast = resolve_includes(ast, base_dir, initial_included)

        # Transpile
        python_code = transpile(ast)

        if _show:
            _show_python_output(python_code)

        fire_hook("before_exec", python_code=python_code)

        # If generated code defines async def main, append asyncio.run(main())
        # Sync path is completely unchanged when _is_async_code() returns False
        if _is_async_code(python_code):
            python_code = _make_async_runner(python_code)

        # Execute — inject runtime globals
        from .namespace_runtime import get_namespace_registry
        ns_registry = get_namespace_registry()
        ns_registry.init_all()  # fire init hooks before exec

        # Build __ph__ (plugin hook runner) from registered block hooks
        _block_hooks = get_transpiler()._block_hooks

        def _ph(event: str, plugin_name: str, args=None):
            for fn in _block_hooks.get(event, []):
                fn(plugin_name, args or [])

        # Build exec globals: fixed builtins + plugin injections
        exec_globals = {
            "__name__": "__main__",
            "__ns__": ns_registry,
            "__ctx__": {},
            "__ctx_stack__": [],
            "__ph__": _ph,
        }
        exec_globals.update(get_inject_globals())

        try:
            exec(
                compile(python_code, f"<cruhon:{filename}>", "exec"),
                exec_globals
            )
        finally:
            ns_registry.destroy_all()  # fire destroy hooks after exec

        if _show:
            _show_python_end()

        fire_hook("after_run")
        return python_code

    except (ParseError, RunError):
        raise

    except SyntaxError as e:
        fire_hook("on_error", error=e)
        raise RunError(f"Syntax error in generated code: {e}") from e

    except Exception as e:
        fire_hook("on_error", error=e)

        try:
            tb = traceback.extract_tb(e.__traceback__)
            python_line = tb[-1].lineno if tb else 0
            cruhon_line = transpiler._line_map.get(python_line, "?")
            hint = _build_hint(e, python_code, python_line)
            msg = f"{type(e).__name__}: {e}\n  → at line {cruhon_line} in {filename}"
            if hint:
                msg += f"\n  Hint: {hint}"
            raise RunError(msg) from e
        except RunError:
            raise
        except Exception:
            raise RunError(f"{type(e).__name__}: {e}") from e


def run_file(
    path: str | Path,
    debug: bool = False,
    show_python: bool = False,
) -> str:
    """Load and run a .clpy file."""
    path = Path(path)

    if not path.exists():
        raise RunError(f"File not found: {path}")

    if path.suffix != ".clpy":
        raise RunError(f"Expected .clpy file, got: {path.suffix}")

    source = path.read_text(encoding="utf-8")

    # Load mods from project directory
    load_all_mods(path.parent)

    return run_source(
        source,
        filename=str(path),
        debug=debug,
        show_python=show_python,
        base_dir=path.parent,
        _root_path=path.resolve(),
    )


def build_file(path: str | Path, output: Optional[str | Path] = None) -> Path:
    """Compile .clpy → .py file."""
    path = Path(path)

    if not path.exists():
        raise RunError(f"File not found: {path}")

    source = path.read_text(encoding="utf-8")
    load_all_mods(path.parent)

    ast = parse(source)
    ast = resolve_includes(ast, path.parent, {path.resolve()})
    python_code = transpile(ast)

    out_path = Path(output) if output else path.with_suffix(".py")
    out_path.write_text(python_code, encoding="utf-8")

    return out_path


def check_file(path: str | Path) -> list[str]:
    """Check a .clpy file for syntax errors. Returns [] if clean."""
    path = Path(path)

    if not path.exists():
        return [f"File not found: {path}"]

    source = path.read_text(encoding="utf-8")
    errors = []

    try:
        ast = parse(source)
        ast = resolve_includes(ast, path.parent, {path.resolve()})
        transpile(ast)
    except Exception as e:
        errors.append(str(e))

    return errors
