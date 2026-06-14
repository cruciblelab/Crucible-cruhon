"""
cruhon/core/libs/ast_.py
========================
Python source ↔ syntax tree for Cruhon — @ast.*

Parse code into an abstract syntax tree, inspect it, and safely evaluate
literals.

━━━ PARSE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ast.parse[code]                → AST module node
  @ast.dump[code]                 → readable dump of the parsed tree
  @ast.unparse[node]              → regenerate source from a node
  @ast.compile[code]              → code object ready for exec/eval

━━━ SAFE EVAL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ast.literal[s]                 → safely evaluate a literal (no code exec)

━━━ INSPECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ast.walk[code]                 → flat list of every node in the tree
  @ast.node_types[code]           → list of node class names in the tree
  @ast.names[code]                → identifiers (Name nodes) referenced
"""
from ..registry import register_lib, register_lib_call

_AS = "__import__('ast')"


def register():
    register_lib("ast", None)

    # ── Parse ─────────────────────────────────────────────────
    register_lib_call("ast", "parse",
        lambda a: f"{_AS}.parse({a[0]})")
    register_lib_call("ast", "dump",
        lambda a: f"{_AS}.dump({_AS}.parse({a[0]}))")
    register_lib_call("ast", "unparse",
        lambda a: f"{_AS}.unparse({a[0]})")
    register_lib_call("ast", "compile",
        lambda a: f"compile({_AS}.parse({a[0]}), '<ast>', 'exec')")

    # ── Safe eval ─────────────────────────────────────────────
    register_lib_call("ast", "literal",
        lambda a: f"{_AS}.literal_eval({a[0]})")

    # ── Inspect ───────────────────────────────────────────────
    register_lib_call("ast", "walk",
        lambda a: f"list({_AS}.walk({_AS}.parse({a[0]})))")
    register_lib_call("ast", "node_types",
        lambda a: f"[type(_n).__name__ for _n in {_AS}.walk({_AS}.parse({a[0]}))]")
    register_lib_call("ast", "names",
        lambda a: f"[_n.id for _n in {_AS}.walk({_AS}.parse({a[0]})) if isinstance(_n, {_AS}.Name)]")
