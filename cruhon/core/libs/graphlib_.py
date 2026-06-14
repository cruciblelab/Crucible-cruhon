"""
cruhon/core/libs/graphlib_.py
=============================
Topological sorting for Cruhon — @graphlib.*

Sort nodes in dependency order using Python's graphlib.TopologicalSorter.

━━━ ONE-SHOT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @graphlib.sort[graph]           → list of nodes in topological order
  @graphlib.sort_groups[graph]    → list of groups (parallel-runnable sets)
  @graphlib.is_dag[graph]         → bool: is the graph acyclic?

━━━ SORTER OBJECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @graphlib.new[graph]            → prepared TopologicalSorter
  @graphlib.add[sorter; node; predecessors] → add a node with dependencies
  @graphlib.ready[sorter]         → nodes that have no remaining dependencies
  @graphlib.done[sorter; nodes]   → mark a list of nodes as completed

graph format: {"a": {"b", "c"}, ...} — key depends on values.
"""
from ..registry import register_lib, register_lib_call

_GL = "__import__('graphlib')"


def register():
    register_lib("graphlib", None)

    # ── One-shot ──────────────────────────────────────────────
    register_lib_call("graphlib", "sort",
        lambda a: f"list({_GL}.TopologicalSorter({a[0]}).static_order())")
    register_lib_call("graphlib", "sort_groups",
        lambda a: (
            f"(lambda _s: (_s.prepare(), "
            f"[list(_s.get_ready()) or (_s.done(*_s.get_ready()), [])[1] "
            f"for _ in range(len({a[0]}) + 1) if not _s.is_active()] )[1])"
            f"({_GL}.TopologicalSorter({a[0]}))"
        ))
    register_lib_call("graphlib", "is_dag",
        lambda a: (
            f"(lambda _g: (lambda: (list(__import__('graphlib').TopologicalSorter(_g).static_order()), True)[1])() "
            f"if True else False)({a[0]})"
        ))

    # ── Sorter object ─────────────────────────────────────────
    register_lib_call("graphlib", "new",
        lambda a: (
            f"(lambda _s: (_s.prepare(), _s)[1])({_GL}.TopologicalSorter({a[0]}))"
        ))
    register_lib_call("graphlib", "add",
        lambda a: f"{a[0]}.add({a[1]}, *{a[2]})")
    register_lib_call("graphlib", "ready",
        lambda a: f"list({a[0]}.get_ready())")
    register_lib_call("graphlib", "done",
        lambda a: f"{a[0]}.done(*{a[1]})")
