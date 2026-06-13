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
import time
import traceback
from pathlib import Path
from typing import Optional

from .parser import parse, ParseError
from .lexer import LexerError
from .transpiler import transpile, get_transpiler, TranspileError
from .mod_loader import fire_hook, load_all_mods, get_inject_globals
from .ast_nodes import IncludeNode, ProgramNode, UseNode, ModuleNode
from . import diagnostics as _diag


class RunError(Exception):
    pass


# Compile-time errors carry a `.line`; runtime wraps land in RunError.
_COMPILE_ERRORS = (LexerError, ParseError, TranspileError)


def _attach_context(exc: Exception, *, source: str = None, filename: str = None,
                    error_type: str = None, clean_message: str = None,
                    line=None, col=None, hint: str = None, suggestion: str = None):
    """Attach structured fields so diagnostics.render_exception can format it.

    Never raises — best-effort enrichment of an in-flight exception.
    """
    try:
        if source is not None:
            exc.source = source
        if filename is not None:
            exc.filename = filename
        if error_type is not None:
            exc.error_type = error_type
        if clean_message is not None:
            exc.clean_message = clean_message
        if line is not None:
            exc.cruhon_line = line
        if col is not None:
            exc.col = col
        if hint:
            exc.hint = hint
        if suggestion:
            exc.suggestion = suggestion
    except Exception:
        pass


def _strip_error_prefix(msg: str) -> str:
    """Remove a leading "[XError] Line N — " prefix for cleaner display."""
    import re
    m = re.match(r"^\[\w+Error\] Line \d+(?::\d+)? — (.*)$", msg, re.S)
    return m.group(1) if m else msg


def _log_error(dlog, filename: str, exc: Exception, source: str, py_tb: str = ""):
    """Write a rich, uncolored diagnostic report to the diagnostic log file."""
    try:
        if not dlog.enabled:
            return
        report = _diag.render_exception(exc, source=source, filename=filename,
                                        colored=False)
        dlog.run_error(filename, report, py_tb)
    except Exception:
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
# SHARED AST CHILD RECURSION
# ─────────────────────────────────────────────────────────────

def _recurse_children(node, fn) -> None:
    """
    Apply fn(ProgramNode) → ProgramNode to every child-body list of node,
    mutating node in place.

    Handles: body / else_body / catch_body / finally_body / default_body,
             elif_branches (list of (cond, body)),
             cases (list of (pattern, body)).
    """
    for attr in ("body", "else_body", "catch_body", "finally_body", "default_body"):
        children = getattr(node, attr, None)
        if isinstance(children, list):
            setattr(node, attr, fn(ProgramNode(body=children)).body)
    if hasattr(node, "elif_branches"):
        node.elif_branches = [
            (cond, fn(ProgramNode(body=branch_body)).body)
            for cond, branch_body in (node.elif_branches or [])
        ]
    if hasattr(node, "cases") and node.cases:
        node.cases = [
            (pat, fn(ProgramNode(body=case_body)).body)
            for pat, case_body in node.cases
        ]


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
            _recurse_children(node, lambda sub: resolve_includes(sub, base_dir, included))
            new_body.append(node)

    ast.body = new_body
    return ast


# ─────────────────────────────────────────────────────────────
# MODULE RESOLUTION
# ─────────────────────────────────────────────────────────────

def _find_module_file(path: str, base_dir: Path) -> Path:
    """Locate a .clpy module file by name or relative path."""
    if path.startswith(".") or path.startswith("/"):
        candidate = (base_dir / path).resolve()
        if not candidate.suffix:
            candidate = candidate.with_suffix(".clpy")
        if candidate.exists():
            return candidate
        raise RunError(f"@use: module not found: {path}")

    for search_dir in [base_dir, base_dir / "modules"]:
        candidate = search_dir / f"{path}.clpy"
        if candidate.exists():
            return candidate

    raise RunError(f"@use: module not found: {path}")


def resolve_modules(
    ast: ProgramNode,
    base_dir: Path,
    loading: Optional[set] = None,
) -> ProgramNode:
    """
    Walk the AST, find UseNode instances, replace them with resolved ModuleNode.

    base_dir: directory for resolving relative module paths.
    loading: set of absolute paths currently being resolved (circular detection).
    """
    if loading is None:
        loading = set()

    new_body = []
    for node in ast.body:
        if isinstance(node, UseNode):
            module_path = _find_module_file(node.path, base_dir)
            abs_path = module_path.resolve()

            if abs_path in loading:
                raise RunError(f"Circular module dependency: {node.path}")

            source = module_path.read_text(encoding="utf-8")
            mod_ast = parse(source)
            new_loading = loading | {abs_path}
            mod_ast = resolve_includes(mod_ast, module_path.parent)
            mod_ast = resolve_modules(mod_ast, module_path.parent, new_loading)

            if mod_ast.body and isinstance(mod_ast.body[0], ModuleNode):
                mod_node = mod_ast.body[0]
                mod_node.name = node.alias
            else:
                mod_node = ModuleNode(
                    name=node.alias,
                    body=mod_ast.body,
                    line=node.line,
                )

            new_body.append(mod_node)
        else:
            _recurse_children(node, lambda sub: resolve_modules(sub, base_dir, loading))
            new_body.append(node)

    ast.body = new_body
    return ast


# ─────────────────────────────────────────────────────────────
# HINT ENGINE — friendly error messages
# ─────────────────────────────────────────────────────────────

def _build_hint(exc: Exception, python_code: str, python_line: int) -> str:
    """
    Return a human-friendly hint for common runtime errors.
    Returns empty string if no hint applies. Kept as a thin wrapper over
    _diagnose() so existing callers/tests see the same hint text.
    """
    hint, _suggestion = _diagnose(exc, python_code, python_line, source=None)
    return hint


def _diagnose(exc: Exception, python_code: str, python_line: int,
              source: Optional[str] = None) -> tuple[str, Optional[str]]:
    """
    Inspect a runtime exception and return (hint, suggestion).

    hint       — a plain-language explanation, "" if none applies
    suggestion — a "did you mean 'x'?" candidate, or None

    `source` (the original .clpy text) is used to mine candidate names for
    spelling suggestions; passing None disables suggestions.
    """
    import re

    if isinstance(exc, NameError):
        m = re.search(r"name '([^']+)' is not defined", str(exc))
        if m:
            name = m.group(1)
            # Spelling suggestion from names that appear in the source.
            suggestion = None
            if source:
                suggestion = _diag.suggest(name, _diag.collect_identifiers(source))
            hint = (
                f"'{name}' is not defined as a variable. "
                f"If you meant text, wrap it in quotes: \"{name}\"."
            )
            return hint, suggestion

    if isinstance(exc, TypeError):
        low = str(exc).lower()
        if "argument" in low or "positional" in low:
            return ("The function got the wrong number of arguments — "
                    "check how many values you passed."), None
        if "not callable" in low:
            return ("You tried to call something that is not a function. "
                    "Remove the parentheses or check the name."), None
        if ("unsupported operand" in low or "not supported between" in low
                or "concatenate" in low or "can't multiply" in low):
            return ("You mixed incompatible types (e.g. text + number). "
                    "Convert one side first, e.g. str(...) or int(...)."), None
        return "Check that the value types on this line match.", None

    if isinstance(exc, AttributeError):
        m = re.search(r"'([^']+)' object has no attribute '([^']+)'", str(exc))
        if m:
            obj_type, attr = m.group(1), m.group(2)
            suggestion = None
            if source:
                suggestion = _diag.suggest(attr, _diag.collect_identifiers(source))
            return (f"A value of type '{obj_type}' has no method or property "
                    f"'{attr}'."), suggestion

    if isinstance(exc, KeyError):
        return (f"Key {exc} was not found in the dictionary. Check the key "
                f"name, or read it safely with a default value."), None

    if isinstance(exc, IndexError):
        return ("List index out of range — the position you asked for is past "
                "the end of the list. Check the list has enough items."), None

    if isinstance(exc, ZeroDivisionError):
        return ("Division by zero is not allowed. Add a check that the "
                "divisor is not zero before dividing."), None

    if isinstance(exc, ValueError):
        return ("The value has the right type but an unacceptable content — "
                "e.g. int(\"abc\"). Check the value before converting."), None

    if isinstance(exc, (FileNotFoundError,)):
        return ("The file could not be found. Check the path and that the "
                "file exists relative to where you run the script."), None

    if isinstance(exc, PermissionError):
        return "Permission denied — the OS blocked access to that file or resource.", None

    if isinstance(exc, ModuleNotFoundError):
        m = re.search(r"No module named '([^']+)'", str(exc))
        if m:
            return (f"The module '{m.group(1)}' is not installed. Install it "
                    f"with pip, or check the @import name."), None

    if isinstance(exc, RecursionError):
        return ("Maximum recursion depth exceeded — a function is calling "
                "itself without a stopping condition (base case)."), None

    if isinstance(exc, AssertionError):
        return "An @assert check failed — the condition was not true.", None

    return "", None


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

def _exec_globals(ns_registry) -> dict:
    """Build the standard exec globals dict."""
    _block_hooks = get_transpiler()._block_hooks

    def _ph(event: str, plugin_name: str, args=None):
        for fn in _block_hooks.get(event, []):
            fn(plugin_name, args or [])

    _RESERVED = {"__name__", "__ns__", "__ctx__", "__ctx_stack__", "__ph__"}
    g = {
        "__name__": "__main__",
        "__ns__": ns_registry,
        "__ctx__": {},
        "__ctx_stack__": [],
        "__ph__": _ph,
    }
    for _k, _v in get_inject_globals().items():
        if _k not in _RESERVED:
            g[_k] = _v
    return g


def run_source(
    source: str,
    filename: str = "<clpy>",
    debug: bool = False,
    show_python: bool = False,
    base_dir: Optional[Path] = None,
    _root_path: Optional[Path] = None,
    _no_cache: bool = False,
) -> str:
    """
    Run Cruhon source code. Returns the generated Python code.

    show_python: print formatted generated Python before output.
    debug: legacy alias for show_python.
    base_dir: directory for resolving @include paths.
    _root_path: absolute path of the root file (for circular include detection).
    _no_cache: bypass cache even if available.
    """
    _show = show_python or debug
    if base_dir is None:
        base_dir = Path.cwd()

    transpiler = get_transpiler()
    dlog = _diag.get_diagnostic_log()
    _t0 = time.perf_counter()
    python_code = ""  # defined early so error handlers can reference it

    dlog.run_start(filename, source)

    # ── Cache fast path ───────────────────────────────────────────────────────
    # Skip cache when: show_python is on, running inline source ("<clpy>"),
    # or _no_cache is explicitly requested.
    _cache_enabled = (
        not _show
        and not _no_cache
        and not filename.startswith("<")
    )
    _cache_key: Optional[str] = None
    _cache_dir: Optional[Path] = None

    if _cache_enabled:
        try:
            from . import cache as _cache
            from .mod_loader import get_load_order
            from cruhon import __version__ as _cruhon_ver

            _src_path = Path(filename).resolve()
            _cache_dir = _src_path.parent / ".cruhon_cache"

            _mod_fp = "|".join(
                f"{e['name']}:{e.get('version', '')}"
                for e in sorted(get_load_order(), key=lambda e: e["name"])
            )
            _cache_key = _cache.build_key(source, base_dir, _cruhon_ver, _mod_fp)
            _code_obj = _cache.try_load(_src_path, _cache_key, _cache_dir)

            if _code_obj is not None:
                # Cache hit — skip parse/transpile entirely
                fire_hook("before_run", source=source)
                fire_hook("before_exec", python_code="")
                from .namespace_runtime import get_namespace_registry
                ns_registry = get_namespace_registry()
                ns_registry.init_all()
                try:
                    exec(_code_obj, _exec_globals(ns_registry))
                finally:
                    ns_registry.destroy_all()
                fire_hook("after_run", source=source, python_code="")
                dlog.run_ok(filename, "", (time.perf_counter() - _t0) * 1000.0)
                return ""
        except Exception:
            _cache_enabled = False  # graceful degradation — proceed normally
    # ─────────────────────────────────────────────────────────────────────────

    try:
        fire_hook("before_run", source=source)

        # Parse
        ast = parse(source)
        dlog.event("parse ok", level="DEBUG")

        # Snapshot inline-command flags before sub-parses reset them.
        # resolve_includes/resolve_modules call parse() on sub-files, clobbering
        # the singleton parser's _needs_os/_needs_requests flags.
        from .parser import get_parser as _get_parser
        _pp = _get_parser()
        _inline_needs_os = _pp._needs_os
        _inline_needs_requests = _pp._needs_requests

        # Resolve @include nodes before transpilation.
        # Seed the included set with the root file so indirect cycles (A→B→C→A)
        # are caught in addition to direct cycles (A→B→A).
        initial_included = {_root_path} if _root_path else set()
        ast = resolve_includes(ast, base_dir, initial_included)
        ast = resolve_modules(ast, base_dir)

        # Restore flags so _needs_os_import/_needs_requests_import read the
        # correct value for the main file's inline commands.
        _pp._needs_os = _inline_needs_os
        _pp._needs_requests = _inline_needs_requests

        # Transpile
        python_code = transpile(ast)
        dlog.event("transpile ok", level="DEBUG")

        if _show:
            _show_python_output(python_code)

        fire_hook("before_exec", python_code=python_code)

        # If generated code defines async def main, append asyncio.run(main())
        # Sync path is completely unchanged when _is_async_code() returns False
        if _is_async_code(python_code):
            python_code = _make_async_runner(python_code)

        # ── Save to cache before exec ─────────────────────────────────────
        if _cache_enabled and _cache_key and _cache_dir:
            try:
                from . import cache as _cache
                _cache.save(
                    Path(filename).resolve(),
                    _cache_key,
                    python_code,
                    filename,
                    _cache_dir,
                )
            except Exception:
                pass
        # ─────────────────────────────────────────────────────────────────

        # Execute — inject runtime globals
        from .namespace_runtime import get_namespace_registry
        ns_registry = get_namespace_registry()
        ns_registry.init_all()  # fire init hooks before exec

        try:
            exec(
                compile(python_code, f"<cruhon:{filename}>", "exec"),
                _exec_globals(ns_registry),
            )
        finally:
            ns_registry.destroy_all()  # fire destroy hooks after exec

        if _show:
            _show_python_end()

        fire_hook("after_run", source=source, python_code=python_code)
        dlog.run_ok(filename, python_code, (time.perf_counter() - _t0) * 1000.0)
        return python_code

    except _COMPILE_ERRORS as e:
        # Lexer / Parser / Transpiler errors already carry a clean message and
        # a `.line`. Enrich with source context for rich display, but DO NOT
        # change the message string (keeps the [XError] Line N prefix stable).
        _attach_context(
            e, source=source, filename=filename,
            error_type=type(e).__name__,
            clean_message=_strip_error_prefix(str(e)),
            line=getattr(e, "line", None),
            col=getattr(e, "col", None),
        )
        fire_hook("on_error", error=e)
        _log_error(dlog, filename, e, source)
        raise

    except RunError as e:
        # Internal RunError (circular include, missing file, …) — attach source
        # so the CLI can still show a friendly excerpt where a line is known.
        _attach_context(e, source=source, filename=filename,
                        error_type="RunError")
        fire_hook("on_error", error=e)
        _log_error(dlog, filename, e, source)
        raise

    except SyntaxError as e:
        fire_hook("on_error", error=e)
        cruhon_line = transpiler._line_map.get(getattr(e, "lineno", 0) or 0, None)
        err = RunError(f"Syntax error in generated code: {e}")
        _attach_context(err, source=source, filename=filename,
                        error_type="SyntaxError",
                        clean_message=f"Syntax error in generated code: {e}",
                        line=cruhon_line,
                        hint="This is usually a Cruhon transpiler edge case — "
                             "run with --show-python to inspect the output.")
        _log_error(dlog, filename, err, source)
        raise err from e

    except Exception as e:
        fire_hook("on_error", error=e)

        try:
            tb = traceback.extract_tb(e.__traceback__)
            python_line = tb[-1].lineno if tb else 0
            cruhon_line = transpiler._line_map.get(python_line, "?")
            hint, suggestion = _diagnose(e, python_code, python_line, source=source)

            msg = f"{type(e).__name__}: {e}\n  → at line {cruhon_line} in {filename}"
            if suggestion:
                msg += f"\n  Did you mean '{suggestion}'?"
            if hint:
                msg += f"\n  Hint: {hint}"

            err = RunError(msg)
            _attach_context(
                err, source=source, filename=filename,
                error_type=type(e).__name__,
                clean_message=str(e),
                line=cruhon_line if isinstance(cruhon_line, int) else None,
                hint=hint, suggestion=suggestion,
            )
            _log_error(dlog, filename, err, source,
                       py_tb="".join(traceback.format_exception(type(e), e, e.__traceback__)))
            raise err from e
        except RunError:
            raise
        except Exception:
            raise RunError(f"{type(e).__name__}: {e}") from e


def run_file(
    path: str | Path,
    debug: bool = False,
    show_python: bool = False,
    no_cache: bool = False,
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
        _no_cache=no_cache,
    )


def build_file(path: str | Path, output: Optional[str | Path] = None) -> Path:
    """Compile .clpy → .py file."""
    path = Path(path)

    if not path.exists():
        raise RunError(f"File not found: {path}")

    source = path.read_text(encoding="utf-8")
    load_all_mods(path.parent)

    try:
        ast = parse(source)
        ast = resolve_includes(ast, path.parent, {path.resolve()})
        ast = resolve_modules(ast, path.parent)
        python_code = transpile(ast)
    except _COMPILE_ERRORS as e:
        _attach_context(e, source=source, filename=str(path),
                        error_type=type(e).__name__,
                        clean_message=_strip_error_prefix(str(e)),
                        line=getattr(e, "line", None),
                        col=getattr(e, "col", None))
        raise

    out_path = Path(output) if output else path.with_suffix(".py")
    out_path.write_text(python_code, encoding="utf-8")

    return out_path


def check_file(path: str | Path, rich: bool = False) -> list[str]:
    """
    Check a .clpy file for syntax errors. Returns [] if clean.

    rich=True returns a full diagnostic excerpt per error (source line +
    caret); rich=False (default) returns the compact message — kept stable
    so existing callers/tests are unaffected.
    """
    path = Path(path)

    if not path.exists():
        return [f"File not found: {path}"]

    source = path.read_text(encoding="utf-8")
    errors = []

    try:
        ast = parse(source)
        ast = resolve_includes(ast, path.parent, {path.resolve()})
        ast = resolve_modules(ast, path.parent)
        transpile(ast)
    except Exception as e:
        if rich:
            _attach_context(e, source=source, filename=str(path),
                            error_type=type(e).__name__,
                            clean_message=_strip_error_prefix(str(e)),
                            line=getattr(e, "line", None),
                            col=getattr(e, "col", None))
            errors.append(_diag.render_exception(e, source=source,
                                                 filename=str(path)))
        else:
            errors.append(str(e))

    return errors
