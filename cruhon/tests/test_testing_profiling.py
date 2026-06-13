"""
Tests for Testing & Profiling namespaces:
@timeit, @profile, @doctest, @unittest
"""
import unittest as _unittest

import pytest

from cruhon.core.transpiler import Transpiler
from cruhon.core.parser import Parser


def transpile(src):
    return Transpiler().transpile(Parser().parse(src))


def run(src, globs=None):
    g = globs or {}
    exec(compile(transpile(src), "<test>", "exec"), g)
    return g


def _work():
    return sum(range(1000))


# ─────────────────────────────────────────────────────────────
# @timeit
# ─────────────────────────────────────────────────────────────

class TestTimeit:
    def test_run(self):
        g = run('@var[t; @timeit.run[fn; 1000]]', {"fn": lambda: 1 + 1})
        assert isinstance(g["t"], float) and g["t"] >= 0

    def test_each(self):
        g = run('@var[t; @timeit.each[fn; 1000]]', {"fn": lambda: 1 + 1})
        assert isinstance(g["t"], float) and g["t"] >= 0

    def test_repeat(self):
        g = run('@var[r; @timeit.repeat[fn; 3; 1000]]', {"fn": lambda: 1 + 1})
        assert isinstance(g["r"], list) and len(g["r"]) == 3

    def test_auto(self):
        g = run('@var[a; @timeit.auto[fn]]', {"fn": lambda: 1 + 1})
        loops, secs = g["a"]
        assert loops > 0 and secs >= 0


# ─────────────────────────────────────────────────────────────
# @profile
# ─────────────────────────────────────────────────────────────

class TestProfile:
    def test_run(self):
        import pstats
        g = run('@var[s; @profile.run[fn]]', {"fn": _work})
        assert isinstance(g["s"], pstats.Stats)

    def test_calls(self):
        g = run('@var[c; @profile.calls[fn]]', {"fn": _work})
        assert isinstance(g["c"], int) and g["c"] >= 1

    def test_time(self):
        g = run('@var[t; @profile.time[fn]]', {"fn": _work})
        assert isinstance(g["t"], float) and g["t"] >= 0

    def test_dump(self, tmp_path):
        p = tmp_path / "stats.prof"
        run(f'@profile.dump[fn; "{p}"]', {"fn": _work})
        assert p.exists() and p.stat().st_size > 0


# ─────────────────────────────────────────────────────────────
# @doctest
# ─────────────────────────────────────────────────────────────

class TestDoctest:
    def test_run_pass(self):
        text = ">>> 1 + 1\n2\n"
        g = run('@var[r; @doctest.run[t]]', {"t": text})
        assert g["r"] == (0, 1)  # 0 failures, 1 attempt

    def test_run_fail(self):
        text = ">>> 1 + 1\n3\n"
        g = run('@var[r; @doctest.run[t]]', {"t": text})
        assert g["r"][0] == 1  # 1 failure

    def test_passed_true(self):
        text = ">>> 2 * 3\n6\n"
        g = run('@var[b; @doctest.passed[t]]', {"t": text})
        assert g["b"] is True

    def test_passed_false(self):
        text = ">>> 2 * 3\n7\n"
        g = run('@var[b; @doctest.passed[t]]', {"t": text})
        assert g["b"] is False

    def test_examples(self):
        text = ">>> x = 5\n>>> x\n5\n"
        g = run('@var[e; @doctest.examples[t]]', {"t": text})
        assert len(g["e"]) == 2


# ─────────────────────────────────────────────────────────────
# @unittest
# ─────────────────────────────────────────────────────────────

class _PassingCase(_unittest.TestCase):
    __test__ = False  # fixture for @unittest tests — not collected by pytest

    def test_a(self):
        self.assertEqual(1 + 1, 2)

    def test_b(self):
        self.assertTrue(True)


class _FailingCase(_unittest.TestCase):
    __test__ = False  # fixture for @unittest tests — not collected by pytest

    def test_x(self):
        self.assertEqual(1, 2)


class TestUnittest:
    def test_passed_true(self):
        g = run('@var[b; @unittest.passed[c]]', {"c": _PassingCase})
        assert g["b"] is True

    def test_passed_false(self):
        g = run('@var[b; @unittest.passed[c]]', {"c": _FailingCase})
        assert g["b"] is False

    def test_count(self):
        g = run('@var[n; @unittest.count[c]]', {"c": _PassingCase})
        assert g["n"] == 2

    def test_failures(self):
        g = run('@var[n; @unittest.failures[c]]', {"c": _FailingCase})
        assert g["n"] == 1

    def test_suite(self):
        g = run('@var[s; @unittest.suite[c]]', {"c": _PassingCase})
        assert g["s"].countTestCases() == 2
