"""
cruhon/core/libs/pdb_.py
========================
Python debugger integration for Cruhon — @pdb.*

Invoke the Python debugger (pdb) programmatically — set breakpoints, do
post-mortem analysis, or run code under the debugger.

━━━ BREAKPOINTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @pdb.bp[]                       → pdb.set_trace()  (breakpoint here)
  @pdb.breakpoint[]               → builtin breakpoint()

━━━ POST-MORTEM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @pdb.pm[]                       → pdb.pm()  (debug last traceback)
  @pdb.pm[tb]                     → pdb.post_mortem(tb)

━━━ RUN UNDER DEBUGGER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @pdb.run[stmt]                  → pdb.run(stmt)
  @pdb.runeval[expr]              → pdb.runeval(expr)
  @pdb.runcall[fn; args]          → pdb.runcall(fn, *args)

━━━ DEBUGGER OBJECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @pdb.new[]                      → pdb.Pdb()
  @pdb.new[stdout]                → pdb.Pdb(stdout=stdout)
  @pdb.set_bp[dbg; fn; line]      → dbg.set_break(fn, line)
  @pdb.clear_bp[dbg; fn; line]    → dbg.clear_break(fn, line)
  @pdb.clear_all[dbg]             → dbg.clear_all_breaks()
  @pdb.list_bps[dbg]              → dbg.get_all_breaks()
"""
from ..registry import register_lib, register_lib_call

_PDB = "__import__('pdb')"


def register():
    register_lib("pdb", None)

    # ── Breakpoints ───────────────────────────────────────────
    register_lib_call("pdb", "bp",
        lambda a: f"{_PDB}.set_trace()")
    register_lib_call("pdb", "breakpoint",
        lambda a: f"breakpoint()")

    # ── Post-mortem ───────────────────────────────────────────
    register_lib_call("pdb", "pm",
        lambda a: (
            f"{_PDB}.post_mortem({a[0]})" if a else
            f"{_PDB}.pm()"
        ))

    # ── Run under debugger ────────────────────────────────────
    register_lib_call("pdb", "run",
        lambda a: f"{_PDB}.run({a[0]})")
    register_lib_call("pdb", "runeval",
        lambda a: f"{_PDB}.runeval({a[0]})")
    register_lib_call("pdb", "runcall",
        lambda a: (
            f"{_PDB}.runcall({a[0]}, *{a[1]})" if len(a) > 1 else
            f"{_PDB}.runcall({a[0]})"
        ))

    # ── Debugger object ───────────────────────────────────────
    register_lib_call("pdb", "new",
        lambda a: (
            f"{_PDB}.Pdb(stdout={a[0]})" if a else
            f"{_PDB}.Pdb()"
        ))
    register_lib_call("pdb", "set_bp",
        lambda a: f"{a[0]}.set_break({a[1]}, {a[2]})")
    register_lib_call("pdb", "clear_bp",
        lambda a: f"{a[0]}.clear_break({a[1]}, {a[2]})")
    register_lib_call("pdb", "clear_all",
        lambda a: f"{a[0]}.clear_all_breaks()")
    register_lib_call("pdb", "list_bps",
        lambda a: f"{a[0]}.get_all_breaks()")
