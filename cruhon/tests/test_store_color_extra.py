"""Tests for @store.clear[] and @color.dim[...] — small, high-value gaps
found by cross-checking documentation against the real registry."""
import io
import contextlib
import sys
import tempfile
import os
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core.runner import run_source


def run(src):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_source(src)
    return buf.getvalue()


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


class TestStoreClear:
    def test_clear_empties_the_store(self):
        out = run(
            '@store.set["x"; 1]\n'
            '@store.set["y"; 2]\n'
            '@var[before; @store.all]\n'
            '@store.clear[]\n'
            '@var[after; @store.all]\n'
            '@print[{before}|{after}]'
        )
        assert "{'x': 1, 'y': 2}" in out
        assert out.strip().endswith("|{}")

    def test_clear_then_set_works_again(self):
        out = run(
            '@store.set["x"; 1]\n'
            '@store.clear[]\n'
            '@store.set["z"; 9]\n'
            '@var[s; @store.all]\n'
            '@print[{s}]'
        )
        assert "{'z': 9}" in out


class TestColorDim:
    def test_dim_wraps_text_with_ansi_codes(self):
        out = run('@var[s; @color.dim["muted"]]\n@print[{s}]')
        assert "\x1b[2m" in out
        assert "muted" in out
        assert "\x1b[0m" in out

    def test_dim_matches_other_color_shape(self):
        # Same wrap-and-reset shape as the other, already-working colors.
        dim = run('@var[s; @color.dim["x"]]\n@print[{s}]').strip()
        bold = run('@var[s; @color.bold["x"]]\n@print[{s}]').strip()
        assert dim.endswith("\x1b[0m")
        assert bold.endswith("\x1b[0m")
