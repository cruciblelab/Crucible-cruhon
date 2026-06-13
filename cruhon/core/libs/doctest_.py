"""
cruhon/core/libs/doctest_.py
============================
Run examples embedded in docstrings for Cruhon — @doctest.*

Verify ">>> " examples found in text or in a module.

━━━ TEXT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @doctest.run[text]              → (failures, attempts) for examples in text
  @doctest.passed[text]           → bool: did every example pass
  @doctest.examples[text]         → list of (source, expected) pairs

━━━ MODULE / OBJECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @doctest.module[mod]            → TestResults(failed, attempted) for a module
  @doctest.object[obj; globals]   → run the docstring examples of obj
"""
from ..registry import register_lib, register_lib_call

_DT = "__import__('doctest')"

# parse text into a DocTest, run it silently, return (failures, tries)
_RUN = (
    "(lambda _t, _g: (lambda _r: (lambda _dt: (_r.run(_dt), (_r.failures, _r.tries))[1])"
    "(__import__('doctest').DocTestParser().get_doctest(_t, _g, 'cruhon', None, 0)))"
    "(__import__('doctest').DocTestRunner(verbose=False)))"
)


def register():
    register_lib("doctest", None)

    # ── Text ──────────────────────────────────────────────────
    register_lib_call("doctest", "run",
        lambda a: f"{_RUN}({a[0]}, {{}})")
    register_lib_call("doctest", "passed",
        lambda a: f"({_RUN}({a[0]}, {{}})[0] == 0)")
    register_lib_call("doctest", "examples",
        lambda a: (
            f"[(_e.source, _e.want) for _e in {_DT}.DocTestParser().get_examples({a[0]})]"
        ))

    # ── Module / Object ───────────────────────────────────────
    register_lib_call("doctest", "module",
        lambda a: f"{_DT}.testmod({a[0]})")
    register_lib_call("doctest", "object",
        lambda a: (
            f"{_DT}.run_docstring_examples({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_DT}.run_docstring_examples({a[0]}, {{}})"
        ))
