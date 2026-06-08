"""
cruhon/cli.py
=============
cruhon run main.clpy [--show-python]
cruhon build main.clpy
cruhon check main.clpy
cruhon mods
cruhon libs
cruhon new <name>
"""

import sys
import os
import argparse
from pathlib import Path


CRUHON_VERSION = "0.9.2"

BANNER = f"""
  \033[36m╔═══════════════════════════╗
  ║   C R U H O N  v{CRUHON_VERSION}   ║
  ║   by CrucibleLab           ║
  ╚═══════════════════════════╝\033[0m
"""


def cmd_run(args):
    from cruhon.core import run_file
    try:
        run_file(
            args.file,
            debug=args.debug,
            show_python=args.show_python,
        )
    except Exception as e:
        print(f"\n  \033[31m✗ {e}\033[0m")
        sys.exit(1)


def cmd_build(args):
    from cruhon.core import build_file
    try:
        out = build_file(args.file, output=args.output)
        print(f"  \033[32m✓ Built: {out}\033[0m")
    except Exception as e:
        print(f"\n  \033[31m✗ {e}\033[0m")
        sys.exit(1)


def cmd_check(args):
    from cruhon.core import check_file
    errors = check_file(args.file)
    if not errors:
        print(f"  \033[32m✓ {args.file} — No errors\033[0m")
    else:
        for err in errors:
            print(f"  \033[31m✗ {err}\033[0m")
        sys.exit(1)


def cmd_mods(args):
    from cruhon.core.mod_loader import (
        load_all_mods,
        get_load_order,
        get_override_chains,
        get_warnings,
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

    # ── Active overrides ─────────────────────────────────────
    if chains:
        print("\n  \033[36mActive overrides:\033[0m")
        for node_name, chain in sorted(chains.items()):
            # Convert PrintNode → @print etc.
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

    print("\n  To create a mod: see mods/README.md\n")


def cmd_libs(args):
    from cruhon.core.registry import list_libs
    libs = list_libs()
    print("  \033[36mSupported libraries:\033[0m")
    for lib in libs:
        print(f"    • @import[{lib}]")
    print("\n  More coming soon — see library.md")


def cmd_new(args):
    """Create a new Cruhon project."""
    name = args.name
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
    p_run.set_defaults(fn=cmd_run)

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
    p_new = sub.add_parser("new", help="Create a new Cruhon project")
    p_new.add_argument("name", help="Project name")
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
