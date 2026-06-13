"""
cruhon/core/libs/unittest_.py
=============================
Run TestCase classes for Cruhon — @unittest.*

Discover and execute unittest.TestCase subclasses and read their results.

━━━ RUN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @unittest.run[case]             → TestResult after running a TestCase class
  @unittest.passed[case]          → bool: did all tests pass
  @unittest.count[case]           → number of tests that ran
  @unittest.failures[case]        → number of failures + errors

━━━ SUITES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @unittest.suite[case]           → a TestSuite loaded from a TestCase class
  @unittest.run_suite[suite]      → run a prepared suite, returns TestResult
  @unittest.discover[start_dir]   → discover tests under a directory → suite
"""
from ..registry import register_lib, register_lib_call

_UT = "__import__('unittest')"

# load a TestCase class into a suite and run it quietly, returning TestResult
_RUNCASE = (
    f"(lambda _c: {_UT}.TextTestRunner(verbosity=0, stream=__import__('io').StringIO())"
    f".run({_UT}.TestLoader().loadTestsFromTestCase(_c)))"
)


def register():
    register_lib("unittest", None)

    # ── Run ───────────────────────────────────────────────────
    register_lib_call("unittest", "run",
        lambda a: f"{_RUNCASE}({a[0]})")
    register_lib_call("unittest", "passed",
        lambda a: f"{_RUNCASE}({a[0]}).wasSuccessful()")
    register_lib_call("unittest", "count",
        lambda a: f"{_RUNCASE}({a[0]}).testsRun")
    register_lib_call("unittest", "failures",
        lambda a: f"(lambda _r: len(_r.failures) + len(_r.errors))({_RUNCASE}({a[0]}))")

    # ── Suites ────────────────────────────────────────────────
    register_lib_call("unittest", "suite",
        lambda a: f"{_UT}.TestLoader().loadTestsFromTestCase({a[0]})")
    register_lib_call("unittest", "run_suite",
        lambda a: (
            f"{_UT}.TextTestRunner(verbosity=0, stream=__import__('io').StringIO()).run({a[0]})"
        ))
    register_lib_call("unittest", "discover",
        lambda a: f"{_UT}.TestLoader().discover({a[0]})")
