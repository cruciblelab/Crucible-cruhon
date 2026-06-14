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
  @ast.functions[code]            → names of functions defined
  @ast.classes[code]              → names of classes defined
  @ast.imports[code]              → names of modules imported
  @ast.constants[code]            → literal constant values used
  @ast.docstring[code]            → module docstring, or None
  @ast.is_valid[code]             → bool: does the source parse?

━━━ NODES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ast.parse_eval[expr]           → AST in expression mode (eval)
  @ast.fields[node]               → list of (field, value) pairs
  @ast.children[node]             → direct child nodes
  @ast.fix[node]                  → fill in missing line/column info
  @ast.increment[node; n]         → shift all line numbers by n
"""
from ..registry import register_lib, register_lib_call

_AS = "__import__('ast')"


def _is_valid(code):
    import ast
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


_SELF = "__import__('cruhon.core.libs.ast_', fromlist=['_is_valid'])"


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
    register_lib_call("ast", "functions",
        lambda a: (
            f"[_n.name for _n in {_AS}.walk({_AS}.parse({a[0]})) "
            f"if isinstance(_n, ({_AS}.FunctionDef, {_AS}.AsyncFunctionDef))]"
        ))
    register_lib_call("ast", "classes",
        lambda a: f"[_n.name for _n in {_AS}.walk({_AS}.parse({a[0]})) if isinstance(_n, {_AS}.ClassDef)]")
    register_lib_call("ast", "imports",
        lambda a: (
            f"[_x.name for _n in {_AS}.walk({_AS}.parse({a[0]})) "
            f"if isinstance(_n, ({_AS}.Import, {_AS}.ImportFrom)) for _x in _n.names]"
        ))
    register_lib_call("ast", "constants",
        lambda a: f"[_n.value for _n in {_AS}.walk({_AS}.parse({a[0]})) if isinstance(_n, {_AS}.Constant)]")
    register_lib_call("ast", "docstring",
        lambda a: f"{_AS}.get_docstring({_AS}.parse({a[0]}))")
    register_lib_call("ast", "is_valid",
        lambda a: f"{_SELF}._is_valid({a[0]})")

    # ── Nodes ─────────────────────────────────────────────────
    register_lib_call("ast", "parse_eval",
        lambda a: f"{_AS}.parse({a[0]}, mode='eval')")
    register_lib_call("ast", "fields",
        lambda a: f"list({_AS}.iter_fields({a[0]}))")
    register_lib_call("ast", "children",
        lambda a: f"list({_AS}.iter_child_nodes({a[0]}))")
    register_lib_call("ast", "fix",
        lambda a: f"{_AS}.fix_missing_locations({a[0]})")
    register_lib_call("ast", "increment",
        lambda a: f"{_AS}.increment_lineno({a[0]}, {a[1]})")
