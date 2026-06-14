"""
cruhon/core/libs/dis_.py
========================
Bytecode disassembler for Cruhon — @dis.*

Peek inside compiled Python functions and code objects.

━━━ DISASSEMBLE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @dis.disasm[fn]                 → disassembly string for a function/code
  @dis.instructions[fn]           → list of Instruction namedtuples
  @dis.opnames[fn]                → list of opcode name strings

━━━ INFO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @dis.stack_size[fn]             → max stack size needed
  @dis.consts[fn]                 → tuple of constants used
  @dis.names[fn]                  → tuple of global names referenced
  @dis.code[fn]                   → the underlying code object
"""
from ..registry import register_lib, register_lib_call

_DI = "__import__('dis')"
_IO = "__import__('io')"


def register():
    register_lib("dis", None)

    # ── Disassemble ───────────────────────────────────────────
    register_lib_call("dis", "disasm",
        lambda a: (
            f"(lambda _f: (lambda _s: ({_DI}.dis(_f, file=_s), _s.getvalue())[1])"
            f"({_IO}.StringIO()))({a[0]})"
        ))
    register_lib_call("dis", "instructions",
        lambda a: f"list({_DI}.get_instructions({a[0]}))")
    register_lib_call("dis", "opnames",
        lambda a: f"[_i.opname for _i in {_DI}.get_instructions({a[0]})]")

    # ── Info ──────────────────────────────────────────────────
    register_lib_call("dis", "stack_size",
        lambda a: f"{a[0].__code__ if hasattr(a[0], '__code__') else a[0]}.co_stacksize"
        if False else
        lambda a: f"(getattr({a[0]}, '__code__', {a[0]})).co_stacksize")
    register_lib_call("dis", "consts",
        lambda a: f"(getattr({a[0]}, '__code__', {a[0]})).co_consts")
    register_lib_call("dis", "names",
        lambda a: f"(getattr({a[0]}, '__code__', {a[0]})).co_names")
    register_lib_call("dis", "code",
        lambda a: f"(getattr({a[0]}, '__code__', {a[0]}))")
