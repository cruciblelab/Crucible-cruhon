"""
Tests for Concurrency namespaces: @multiprocessing, @futures, @sched
"""
import pytest

from cruhon.core.transpiler import Transpiler
from cruhon.core.parser import Parser


def transpile(src):
    return Transpiler().transpile(Parser().parse(src))


def run(src, globs=None):
    g = globs or {}
    exec(compile(transpile(src), "<test>", "exec"), g)
    return g


# Module-level (picklable) helpers for process pools
def _square(x):
    return x * x


def _add(a, b):
    return a + b


# ─────────────────────────────────────────────────────────────
# @multiprocessing
# ─────────────────────────────────────────────────────────────

class TestMultiprocessing:
    def test_cpus(self):
        g = run('@var[n; @multiprocessing.cpus[]]')
        assert isinstance(g["n"], int) and g["n"] >= 1

    def test_map(self):
        g = run('@var[r; @multiprocessing.map[fn; [1, 2, 3, 4]]]', {"fn": _square})
        assert g["r"] == [1, 4, 9, 16]

    def test_starmap(self):
        g = run('@var[r; @multiprocessing.starmap[fn; [(1, 2), (3, 4)]]]', {"fn": _add})
        assert g["r"] == [3, 7]

    def test_queue(self):
        import multiprocessing
        g = run('@var[q; @multiprocessing.queue[]]')
        g["q"].put(1)
        assert g["q"].get() == 1

    def test_process(self):
        import multiprocessing
        g = run('@var[p; @multiprocessing.process[fn; (1,)]]', {"fn": _square})
        assert isinstance(g["p"], multiprocessing.Process)


# ─────────────────────────────────────────────────────────────
# @futures
# ─────────────────────────────────────────────────────────────

class TestFutures:
    def test_thread_map(self):
        g = run('@var[r; @futures.thread_map[fn; [1, 2, 3]]]', {"fn": lambda x: x + 10})
        assert g["r"] == [11, 12, 13]

    def test_process_map(self):
        g = run('@var[r; @futures.process_map[fn; [1, 2, 3]]]', {"fn": _square})
        assert g["r"] == [1, 4, 9]

    def test_submit_result(self):
        src = (
            '@var[ex; @futures.threads[2]]\n'
            '@var[f; @futures.submit[ex; fn; (5,)]]\n'
            '@var[r; @futures.result[f]]\n'
            '@futures.shutdown[ex]'
        )
        g = run(src, {"fn": _square})
        assert g["r"] == 25

    def test_done(self):
        src = (
            '@var[ex; @futures.threads[1]]\n'
            '@var[f; @futures.submit[ex; fn; (2,)]]\n'
            '@var[r; @futures.result[f]]\n'
            '@var[d; @futures.done[f]]\n'
            '@futures.shutdown[ex]'
        )
        g = run(src, {"fn": _square})
        assert g["d"] is True


# ─────────────────────────────────────────────────────────────
# @sched
# ─────────────────────────────────────────────────────────────

class TestSched:
    def test_after_runs(self):
        hits = []
        src = (
            '@var[s; @sched.new[]]\n'
            '@sched.after[s; 0; cb]\n'
            '@var[empty_before; @sched.empty[s]]\n'
            '@sched.run[s]\n'
            '@var[empty_after; @sched.empty[s]]'
        )
        g = run(src, {"cb": lambda: hits.append(1)})
        assert hits == [1]
        assert g["empty_before"] is False
        assert g["empty_after"] is True

    def test_at_absolute(self):
        # @sched.at schedules at an absolute time(); a past time fires at once.
        import time as _time
        hits = []
        when = _time.time()
        src = (
            '@var[s; @sched.new[]]\n'
            '@sched.at[s; w; cb]\n'
            '@sched.run[s]'
        )
        run(src, {"w": when, "cb": lambda: hits.append(1)})
        assert hits == [1]

    def test_cancel(self):
        hits = []
        src = (
            '@var[s; @sched.new[]]\n'
            '@var[ev; @sched.after[s; 5; cb]]\n'
            '@sched.cancel[s; ev]\n'
            '@var[empty; @sched.empty[s]]'
        )
        g = run(src, {"cb": lambda: hits.append(1)})
        assert g["empty"] is True and hits == []

    def test_queue(self):
        src = (
            '@var[s; @sched.new[]]\n'
            '@sched.after[s; 10; cb]\n'
            '@var[q; @sched.queue[s]]'
        )
        g = run(src, {"cb": lambda: None})
        assert len(g["q"]) == 1
