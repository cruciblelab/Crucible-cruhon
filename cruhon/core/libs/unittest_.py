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

━━━ ASSERTIONS (raise on failure) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @unittest.assert_equal[a; b]    → fail unless a == b
  @unittest.assert_true[x]        → fail unless x is truthy
  @unittest.assert_in[x; coll]    → fail unless x in coll
  @unittest.assert_raises[exc; fn; args] → fail unless fn(*args) raises exc

━━━ MOCKING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @unittest.mock[]                → a MagicMock
  @unittest.mock[return_value]    → a MagicMock with a fixed return value
  @unittest.patch[target]         → a patch() context manager / decorator
"""
from ..registry import register_lib, register_lib_call

_UT = "__import__('unittest')"
_MK = "__import__('unittest.mock', fromlist=['mock'])"

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

    # ── Assertions ────────────────────────────────────────────
    register_lib_call("unittest", "assert_equal",
        lambda a: f"{_UT}.TestCase().assertEqual({a[0]}, {a[1]})")
    register_lib_call("unittest", "assert_true",
        lambda a: f"{_UT}.TestCase().assertTrue({a[0]})")
    register_lib_call("unittest", "assert_in",
        lambda a: f"{_UT}.TestCase().assertIn({a[0]}, {a[1]})")
    register_lib_call("unittest", "assert_raises",
        lambda a: (
            f"{_UT}.TestCase().assertRaises({a[0]}, {a[1]}, *{a[2]})" if len(a) > 2 else
            f"{_UT}.TestCase().assertRaises({a[0]}, {a[1]})"
        ))

    # ── Mocking ───────────────────────────────────────────────
    register_lib_call("unittest", "mock",
        lambda a: f"{_MK}.MagicMock(return_value={a[0]})" if a else f"{_MK}.MagicMock()")
    register_lib_call("unittest", "patch",
        lambda a: f"{_MK}.patch({a[0]})")
