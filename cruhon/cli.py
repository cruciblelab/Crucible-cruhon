"""
cruhon/cli.py
=============
cruhon run main.clpy [--show-python] [--watch]
cruhon build main.clpy
cruhon check main.clpy
cruhon repl
cruhon docs [plugin]
cruhon fmt main.clpy [--check | --stdout]
cruhon mods
cruhon libs
cruhon new <name>
cruhon new --plugin <name>
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path


CRUHON_VERSION = "2.3.0"

BANNER = f"""
  \033[36m╔═══════════════════════════╗
  ║   C R U H O N  v{CRUHON_VERSION}   ║
  ║   by CrucibleLab           ║
  ╚═══════════════════════════╝\033[0m
"""


def _print_error(e, fallback_file=None):
    """Render an exception richly when it carries source context, else plainly."""
    from cruhon.core import diagnostics as _diag
    source = getattr(e, "source", None)
    filename = getattr(e, "filename", None) or fallback_file or "<clpy>"
    if source:
        print("\n" + _diag.render_exception(e, source=source, filename=filename))
    else:
        print(f"\n  \033[31m✗ {e}\033[0m")


def cmd_run(args):
    from cruhon.core import run_file
    from cruhon.core.diagnostics import get_diagnostic_log

    # CLI flag is the zero-env way to enable diagnostic logging.
    if getattr(args, "log", None):
        get_diagnostic_log().configure(args.log, args.log_level or "INFO")

    def _run_once():
        try:
            run_file(
                args.file,
                debug=args.debug,
                show_python=args.show_python,
            )
            return True
        except Exception as e:
            _print_error(e, fallback_file=args.file)
            return False

    if getattr(args, "watch", False):
        _watch_loop(args.file, _run_once)
    else:
        if not _run_once():
            sys.exit(1)


def _watch_loop(file, run_once):
    """Re-run `file` every time it (or any .clpy in its folder) changes."""
    path = Path(file)
    watch_dir = path.parent if path.parent != Path("") else Path(".")

    def _snapshot():
        snap = {}
        for p in watch_dir.rglob("*.clpy"):
            try:
                snap[p] = p.stat().st_mtime
            except OSError:
                pass
        return snap

    print(f"  \033[36m◉ watch\033[0m  {file}  \033[90m(Ctrl+C to stop)\033[0m\n")
    run_once()
    last = _snapshot()
    try:
        while True:
            time.sleep(0.4)
            current = _snapshot()
            if current != last:
                last = current
                ts = time.strftime("%H:%M:%S")
                print(f"\n  \033[90m── change detected {ts} ──\033[0m")
                run_once()
    except KeyboardInterrupt:
        print("\n  \033[90m⏹ watch stopped\033[0m")


def cmd_build(args):
    from cruhon.core import build_file
    try:
        out = build_file(args.file, output=args.output)
        print(f"  \033[32m✓ Built: {out}\033[0m")
    except Exception as e:
        _print_error(e, fallback_file=args.file)
        sys.exit(1)


def cmd_check(args):
    from cruhon.core import check_file
    errors = check_file(args.file, rich=True)
    if not errors:
        print(f"  \033[32m✓ {args.file} — No errors\033[0m")
    else:
        for err in errors:
            print(f"\n{err}")
        sys.exit(1)


def cmd_mods(args):
    from cruhon.core.mod_loader import (
        load_all_mods,
        get_load_order,
        get_override_chains,
        get_warnings,
        list_exposed_apis,
        list_block_commands,
    )
    load_all_mods()
    order = get_load_order()
    chains = get_override_chains()
    warnings = get_warnings()

    # ── Loaded mods (load order) ──────────────────────────────
    print("\n  \033[36mLoaded mods (load order):\033[0m")
    for i, entry in enumerate(order, 1):
        name = entry["name"]
        version = entry["version"]
        source = entry["source"]
        path = entry["source_path"]

        if source == "built-in":
            label = "\033[90mbuilt-in\033[0m"
        elif source == "pip":
            label = f"\033[32mv{version}\033[0m   \033[90m[pip]\033[0m"
        else:
            rel = path if path else f"mods/{name}"
            label = f"\033[32mv{version}\033[0m   \033[90m[local: {rel}]\033[0m"

        print(f"    {i:>2}. {name:<20} {label}")

    # ── Plugin block commands ─────────────────────────────────
    block_cmds = list_block_commands()
    if block_cmds:
        print("\n  \033[36mPlugin block commands:\033[0m")
        for plugin, cmds in sorted(block_cmds.items()):
            cmds_str = "  ".join(f"@{c}" for c in cmds)
            print(f"    {plugin:<20} {cmds_str}")

    # ── Exposed APIs ─────────────────────────────────────────
    exposed = list_exposed_apis()
    if exposed:
        print("\n  \033[36mExposed APIs:\033[0m")
        for plugin, keys in sorted(exposed.items()):
            keys_str = "  ".join(keys)
            print(f"    {plugin:<20} {keys_str}")

    # ── Active overrides ─────────────────────────────────────
    if chains:
        print("\n  \033[36mActive overrides:\033[0m")
        for node_name, chain in sorted(chains.items()):
            cmd = node_name.replace("Node", "").lower()
            chain_str = " → ".join(chain)
            print(f"    @{cmd:<12} →  {chain_str}")
    else:
        print("\n  \033[90mNo active overrides.\033[0m")

    # ── Warnings ─────────────────────────────────────────────
    if warnings:
        print(f"\n  \033[33mWarnings ({len(warnings)}):\033[0m")
        for w in warnings:
            print(f"    {w}")

    print("\n  To create a plugin: cruhon new --plugin <name>")
    print("  \033[90mCommunity: https://discord.gg/SPf5VZ6QPG  ·  cruciblelab@hotmail.com\033[0m\n")


def cmd_libs(args):
    from cruhon.core.registry import list_libs
    libs = list_libs()
    print("  \033[36mSupported libraries:\033[0m")
    for lib in libs:
        print(f"    • @import[{lib}]")
    print("\n  More coming soon — see library.md")


# ─────────────────────────────────────────────────────────────
# REPL — interactive Cruhon session
# ─────────────────────────────────────────────────────────────

def cmd_repl(args):
    from cruhon.core.parser import parse, get_parser
    from cruhon.core.lexer import get_lexer
    from cruhon.core.transpiler import transpile
    from cruhon.core.mod_loader import load_all_mods, list_block_commands, get_inject_globals
    from cruhon.core.namespace_runtime import get_namespace_registry

    load_all_mods(Path.cwd())

    # Block-opening commands all close with @end. @decorator is registered as a
    # block command but attaches to the next def/class (no @end of its own).
    parser = get_parser()
    lexer = get_lexer()
    block_openers = set(parser._block_commands.keys()) - {"decorator"}
    for cmds in list_block_commands().values():
        block_openers.update(cmds)

    # Persistent exec namespace — definitions and variables survive across lines.
    ns_registry = get_namespace_registry()
    ns_registry.init_all()
    exec_globals = {
        "__name__": "__main__",
        "__ns__": ns_registry,
        "__ctx__": {},
        "__ctx_stack__": [],
        "__ph__": lambda *a, **k: None,
    }
    reserved = {"__name__", "__ns__", "__ctx__", "__ctx_stack__", "__ph__"}
    for k, v in get_inject_globals().items():
        if k not in reserved:
            exec_globals[k] = v

    print(BANNER)
    print("  \033[90mInteractive REPL — :help for commands, :quit to exit\033[0m\n")

    buffer = []
    depth = 0
    while True:
        prompt = "\033[36mcruhon>\033[0m " if depth == 0 else "\033[36m......\033[0m "
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\n  \033[90mbye\033[0m")
            break

        stripped = line.strip()

        # REPL meta-commands (only at top level)
        if depth == 0 and stripped in (":quit", ":q", ":exit"):
            print("  \033[90mbye\033[0m")
            break
        if depth == 0 and stripped in (":help", ":h"):
            print("  \033[36m:quit/:q\033[0m   exit    "
                  "\033[36m:clear\033[0m   reset namespace    "
                  "\033[36m:vars\033[0m   show defined names")
            print("  Type Cruhon normally. Blocks (@for, @func, ...) buffer until @end.\n")
            continue
        if depth == 0 and stripped == ":clear":
            for k in [k for k in exec_globals if not k.startswith("__") and k not in reserved]:
                del exec_globals[k]
            print("  \033[90mnamespace cleared\033[0m")
            continue
        if depth == 0 and stripped == ":vars":
            names = [k for k in exec_globals if not k.startswith("__") and k not in reserved]
            print("  " + ("  ".join(sorted(names)) if names else "\033[90m(none)\033[0m"))
            continue

        # Track block depth
        cmd = _effective_leading_cmd(stripped, lexer)
        if cmd in block_openers:
            depth += 1
        elif stripped == "@end" or stripped.startswith("@end"):
            depth = max(0, depth - 1)

        buffer.append(line)
        if depth > 0:
            continue

        src = "\n".join(buffer)
        buffer = []
        if not src.strip():
            continue

        _repl_eval(src, exec_globals, parse, transpile)

    ns_registry.destroy_all()


def _repl_eval(src, exec_globals, parse, transpile):
    """Transpile a complete Cruhon snippet; eval-and-echo if it's an expression."""
    try:
        code = transpile(parse(src)).strip()
    except Exception as e:
        print(f"  \033[31m✗ {type(e).__name__}: {e}\033[0m")
        return

    if not code:
        return

    # Single-line output with no assignment/keyword → try to echo its value,
    # mirroring how Python's own REPL prints bare expressions.
    if "\n" not in code:
        try:
            value = eval(compile(code, "<repl>", "eval"), exec_globals)
            if value is not None:
                print(f"  \033[90m=>\033[0m {value!r}")
            return
        except SyntaxError:
            pass  # not an expression — fall through to exec
        except Exception as e:
            print(f"  \033[31m✗ {type(e).__name__}: {e}\033[0m")
            return

    try:
        exec(compile(code, "<repl>", "exec"), exec_globals)
    except Exception as e:
        print(f"  \033[31m✗ {type(e).__name__}: {e}\033[0m")


# ─────────────────────────────────────────────────────────────
# DOCS — show a plugin's command reference
# ─────────────────────────────────────────────────────────────

def cmd_docs(args):
    import importlib.util
    from cruhon.core.mod_loader import (
        load_all_mods, get_load_order, list_block_commands,
    )

    load_all_mods(Path.cwd())
    order = get_load_order()
    block_cmds = list_block_commands()

    # No plugin named → list everything available
    if not getattr(args, "plugin", None):
        print("\n  \033[36mPlugins with docs:\033[0m")
        documented = []
        for entry in order:
            name = entry["name"]
            if entry["source"] == "built-in":
                continue
            documented.append(name)
            cmds = block_cmds.get(name, [])
            tag = f"\033[90m{len(cmds)} block cmds\033[0m" if cmds else ""
            print(f"    • {name:<22} {tag}")
        if not documented:
            print("    \033[90m(no plugins loaded)\033[0m")
        print("\n  \033[90mcruhon docs <plugin>  →  full command reference\033[0m\n")
        return

    target = args.plugin
    entry = next((e for e in order if e["name"] == target), None)
    if entry is None:
        # tolerate "discord" vs "cruhon-discord"
        entry = next((e for e in order if e["name"].endswith(target)
                      or e["name"].replace("cruhon-", "") == target), None)
    if entry is None:
        print(f"  \033[31m✗ Plugin not loaded: {target}\033[0m")
        print(f"  \033[90mcruhon docs   →  list available plugins\033[0m")
        sys.exit(1)

    name = entry["name"]
    print(f"\n  \033[36m{name}\033[0m  \033[90mv{entry['version']}\033[0m")

    # Print the plugin module's docstring — the human-readable command reference
    doc = None
    src_path = entry.get("source_path") or ""
    init_file = Path(src_path) / "__init__.py" if src_path else None
    if init_file and init_file.exists():
        try:
            spec = importlib.util.spec_from_file_location(f"_docs_{name}", init_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            doc = (mod.__doc__ or "").strip()
        except Exception:
            doc = None

    if doc:
        print()
        for line in doc.splitlines():
            print(f"  {line}")
    else:
        print("  \033[90m(no module docstring)\033[0m")

    cmds = block_cmds.get(name, [])
    if cmds:
        print(f"\n  \033[36mBlock commands:\033[0m  " + "  ".join(f"@{c}" for c in cmds))
    print()


# ─────────────────────────────────────────────────────────────
# FMT — normalize .clpy indentation
# ─────────────────────────────────────────────────────────────

# Keywords that dedent their own line but stay inside the current block
_FMT_MID_KEYWORDS = {"else", "elif", "catch", "finally", "case", "default"}


def cmd_fmt(args):
    from cruhon.core.parser import get_parser
    from cruhon.core.lexer import get_lexer
    from cruhon.core.mod_loader import load_all_mods, list_block_commands

    load_all_mods(Path.cwd())
    parser = get_parser()
    lexer = get_lexer()
    openers = set(parser._block_commands.keys()) - {"decorator"}
    for cmds in list_block_commands().values():
        openers.update(cmds)

    path = Path(args.file)
    if not path.exists():
        print(f"  \033[31m✗ File not found: {args.file}\033[0m")
        sys.exit(1)

    original = path.read_text(encoding="utf-8")
    formatted = _format_clpy(original, openers, indent=args.indent, lexer=lexer)

    if getattr(args, "stdout", False):
        sys.stdout.write(formatted)
        return

    if getattr(args, "check", False):
        if formatted != original:
            print(f"  \033[33m✗ {args.file} is not formatted\033[0m")
            sys.exit(1)
        print(f"  \033[32m✓ {args.file} is formatted\033[0m")
        return

    if formatted == original:
        print(f"  \033[90m✓ {args.file} unchanged\033[0m")
    else:
        path.write_text(formatted, encoding="utf-8")
        print(f"  \033[32m✓ Formatted {args.file}\033[0m")


def _effective_leading_cmd(stripped, lexer=None):
    """
    The block-command name a line resolves to *after* lexer pre-hooks run.

    Plugin block commands are written namespaced in source (@discord.on[...])
    but rewritten by a lexer pre-hook to an internal name (@_dc_on[...]) before
    tokenizing. Applying those same hooks here lets fmt/repl recognize plugin
    blocks by the exact names registered in list_block_commands().
    """
    if not stripped.startswith("@"):
        return None
    text = stripped
    if lexer is not None:
        for hook in getattr(lexer, "_pre_hooks", []):
            try:
                text = hook(text)
            except Exception:
                text = stripped  # a hook that dislikes a partial line — ignore it
    text = text.strip()
    if not text.startswith("@") or len(text) < 2:
        return None
    # token = chars after @ up to the first '[' or whitespace (keep dots)
    tok = text[1:]
    for sep in ("[", " ", "\t"):
        tok = tok.split(sep)[0]
    return tok


def _leading_at_cmd(stripped):
    # Back-compat shim used where a lexer isn't threaded through.
    return _effective_leading_cmd(stripped)


def _format_clpy(source, openers, indent=4, lexer=None):
    out = []
    depth = 0
    unit = " " * indent
    in_raw = False  # inside @raw — body is verbatim, don't touch it
    for raw in source.splitlines():
        stripped = raw.strip()

        # Preserve blank lines verbatim
        if not stripped:
            out.append("")
            continue

        cmd = _effective_leading_cmd(stripped, lexer)

        # @raw body is emitted untouched (it is literal Python)
        if in_raw:
            if stripped == "@end" or stripped.startswith("@end"):
                depth = max(0, depth - 1)
                out.append(unit * depth + stripped)
                in_raw = False
            else:
                out.append(raw)
            continue

        # @end and mid-keywords dedent the line they sit on
        if stripped == "@end" or stripped.startswith("@end"):
            depth = max(0, depth - 1)
            out.append(unit * depth + stripped)
            continue
        if cmd in _FMT_MID_KEYWORDS:
            line_depth = max(0, depth - 1)
            out.append(unit * line_depth + stripped)
            continue

        out.append(unit * depth + stripped)

        # Block openers increase depth for following lines (@decorator excluded)
        if cmd in openers and cmd != "decorator":
            depth += 1
            if cmd == "raw":
                in_raw = True

    text = "\n".join(out)
    if source.endswith("\n") and not text.endswith("\n"):
        text += "\n"
    return text


def cmd_new(args):
    """Create a new Cruhon project or plugin scaffold."""
    if getattr(args, "plugin", False):
        _cmd_new_plugin(args.name)
    else:
        _cmd_new_project(args.name)


def _cmd_new_project(name: str):
    path = Path(name)
    if path.exists():
        print(f"  \033[31m✗ Directory already exists: {name}\033[0m")
        sys.exit(1)

    (path / "mods").mkdir(parents=True)
    (path / "src").mkdir()

    (path / "src" / "main.clpy").write_text(
        "# Welcome to Cruhon!\n@print[Hello, World!]\n",
        encoding="utf-8"
    )

    (path / "mods" / "README.md").write_text(
        "# Mods\nPlace your mods here. Each mod is a folder with mod.json and __init__.py\n",
        encoding="utf-8"
    )

    print(f"  \033[32m✓ Created project: {name}\033[0m")
    print(f"  \033[90mcd {name} && cruhon run src/main.clpy\033[0m")


def _cmd_new_plugin(name: str):
    path = Path("mods") / name
    if path.exists():
        print(f"  \033[31m✗ Plugin already exists: mods/{name}/\033[0m")
        sys.exit(1)

    path.mkdir(parents=True)

    manifest = {
        "name": name,
        "version": "0.1.0",
        "description": f"Cruhon plugin: {name}",
        "cruhon": f">={CRUHON_VERSION}",
    }
    (path / "mod.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    (path / "__init__.py").write_text(
        f'"""\n{name} — Cruhon plugin\n"""\n\n\ndef register(api):\n'
        '    """Plugin entry point. Called by Cruhon\'s mod loader."""\n\n'
        '    # Register a block command:\n'
        '    # api.block_command("my_block", visit_my_block)\n\n'
        '    # Expose a utility for other plugins:\n'
        '    # api.expose("my_util", lambda x: x)\n\n'
        '    pass\n',
        encoding="utf-8"
    )

    print(f"  \033[32m✓ Plugin scaffold created: mods/{name}/\033[0m")
    print(f"  \033[90m  mod.json + __init__.py ready\033[0m")
    print(f"  \033[90m  Edit mods/{name}/__init__.py to add commands\033[0m")


def main():
    parser = argparse.ArgumentParser(
        prog="cruhon",
        description="Cruhon language CLI — by CrucibleLab"
    )
    parser.add_argument("--version", action="version", version=f"cruhon {CRUHON_VERSION}")

    sub = parser.add_subparsers(dest="command")

    # run
    p_run = sub.add_parser("run", help="Run a .clpy file")
    p_run.add_argument("file", help=".clpy file to run")
    p_run.add_argument("--debug", action="store_true", help="Show generated Python code (legacy alias for --show-python)")
    p_run.add_argument("--show-python", action="store_true", dest="show_python",
                       help="Show generated Python before running")
    p_run.add_argument("--watch", action="store_true",
                       help="Re-run automatically when .clpy files change")
    p_run.add_argument("--log", metavar="FILE", default=None,
                       help="Write Cruhon's diagnostics to a log file "
                            "(same as setting CRUHON_LOG)")
    p_run.add_argument("--log-level", default=None,
                       choices=["ERROR", "WARNING", "INFO", "DEBUG"],
                       help="Diagnostic log verbosity (default INFO)")
    p_run.set_defaults(fn=cmd_run)

    # repl
    p_repl = sub.add_parser("repl", help="Start an interactive Cruhon session")
    p_repl.set_defaults(fn=cmd_repl)

    # docs
    p_docs = sub.add_parser("docs", help="Show a plugin's command reference")
    p_docs.add_argument("plugin", nargs="?", help="Plugin name (e.g. discord). Omit to list all.")
    p_docs.set_defaults(fn=cmd_docs)

    # fmt
    p_fmt = sub.add_parser("fmt", help="Normalize .clpy indentation")
    p_fmt.add_argument("file", help=".clpy file to format")
    p_fmt.add_argument("--check", action="store_true", help="Exit non-zero if not formatted (don't write)")
    p_fmt.add_argument("--stdout", action="store_true", help="Write result to stdout instead of the file")
    p_fmt.add_argument("--indent", type=int, default=4, help="Spaces per indent level (default 4)")
    p_fmt.set_defaults(fn=cmd_fmt)

    # build
    p_build = sub.add_parser("build", help="Compile .clpy to .py")
    p_build.add_argument("file", help=".clpy file to build")
    p_build.add_argument("-o", "--output", help="Output .py file path")
    p_build.set_defaults(fn=cmd_build)

    # check
    p_check = sub.add_parser("check", help="Check .clpy for syntax errors")
    p_check.add_argument("file", help=".clpy file to check")
    p_check.set_defaults(fn=cmd_check)

    # mods
    p_mods = sub.add_parser("mods", help="List loaded mods with load order and override chains")
    p_mods.set_defaults(fn=cmd_mods)

    # libs
    p_libs = sub.add_parser("libs", help="List supported libraries")
    p_libs.set_defaults(fn=cmd_libs)

    # new
    p_new = sub.add_parser("new", help="Create a new Cruhon project or plugin scaffold")
    p_new.add_argument("name", help="Project or plugin name")
    p_new.add_argument("--plugin", action="store_true", help="Create a plugin skeleton in mods/<name>/")
    p_new.set_defaults(fn=cmd_new)

    args = parser.parse_args()

    if not args.command:
        print(BANNER)
        parser.print_help()
        return

    if hasattr(args, "fn"):
        args.fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
