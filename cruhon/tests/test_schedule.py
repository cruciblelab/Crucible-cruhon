"""
Test suite for the cruhon-schedule plugin (@schedule.*).

Runtime: exercise _CruhonScheduler registration/parsing helpers.
Transpile: load the plugin and check generated job functions + control calls.
"""
import sys
import importlib.util
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core import mod_loader
from cruhon.core.parser import parse
from cruhon.core.transpiler import transpile


_spec = importlib.util.spec_from_file_location(
    "_cruhon_schedule_mod",
    Path(__file__).parent.parent.parent / "mods" / "cruhon-schedule" / "__init__.py",
)
_sch_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sch_mod)
Scheduler = _sch_mod._CruhonScheduler


@pytest.fixture(scope="module", autouse=True)
def _load_schedule_mod():
    mod_path = Path(__file__).parent.parent.parent / "mods" / "cruhon-schedule"
    mod_loader.load_mod_from_path(mod_path)


def _compile(source: str) -> str:
    code = transpile(parse(source))
    indented = "\n".join("    " + line for line in code.splitlines())
    wrapper = "async def __c__():\n" + (indented if indented.strip() else "    pass")
    compile(wrapper, "<test>", "exec")
    return code


# ─────────────────────────────────────────────────────────────
# RUNTIME
# ─────────────────────────────────────────────────────────────

class TestSchedulerRuntime:
    def test_every_registers_seconds(self):
        s = Scheduler()
        @s.every(minutes=2)
        async def job():
            pass
        assert s.count() == 1
        kind, spec, fn = s._jobs[0]
        assert kind == "every" and spec == 120

    def test_daily_and_weekly(self):
        s = Scheduler()
        @s.daily("09:30")
        async def a(): pass
        @s.weekly("monday", "10:00")
        async def b(): pass
        assert s.count() == 2
        assert s._jobs[0][0] == "daily"
        assert s._jobs[1][0] == "weekly"

    def test_parse_hm(self):
        assert Scheduler._parse_hm("09:30") == (9, 30)
        assert Scheduler._parse_hm("7") == (7, 0)

    def test_weekday_num(self):
        assert Scheduler._weekday_num("monday") == 0
        assert Scheduler._weekday_num("sun") == 6
        assert Scheduler._weekday_num(3) == 3


# ─────────────────────────────────────────────────────────────
# TRANSPILE
# ─────────────────────────────────────────────────────────────

class TestScheduleTranspile:
    def test_every_block(self):
        src = (
            "@schedule.every[minutes=5]\n"
            '    @print["tick"]\n'
            "@end"
        )
        code = _compile(src)
        assert "@__scheduler__.every(minutes=5)" in code
        assert "async def _sched_job_" in code

    def test_every_positional_seconds(self):
        src = (
            "@schedule.every[30]\n"
            '    @print["tick"]\n'
            "@end"
        )
        code = _compile(src)
        assert "@__scheduler__.every(seconds=30)" in code

    def test_daily(self):
        src = (
            '@schedule.daily["09:00"]\n'
            '    @print["good morning"]\n'
            "@end"
        )
        code = _compile(src)
        assert '@__scheduler__.daily("09:00")' in code

    def test_weekly(self):
        src = (
            '@schedule.weekly[monday; "10:00"]\n'
            '    @print["week start"]\n'
            "@end"
        )
        code = _compile(src)
        assert "@__scheduler__.weekly('monday', \"10:00\")" in code

    def test_at_oneshot(self):
        src = (
            '@schedule.at["2025-12-31 23:59"]\n'
            '    @print["happy new year"]\n'
            "@end"
        )
        code = _compile(src)
        assert '@__scheduler__.at("2025-12-31 23:59")' in code

    def test_cron(self):
        src = (
            '@schedule.cron["0 9 * * *"]\n'
            '    @print["cron tick"]\n'
            "@end"
        )
        code = _compile(src)
        assert '@__scheduler__.cron("0 9 * * *")' in code

    def test_control(self):
        assert "__scheduler__.start()" in _compile("@schedule.start[]")
        assert "__scheduler__.stop()" in _compile("@schedule.stop[]")
        assert "__scheduler__.count()" in _compile("@var[n; @schedule.count[]]")
