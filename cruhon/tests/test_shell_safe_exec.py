"""
Tests for @shell.exec[argv]/exec_output/exec_code/exec_ok/exec_bg — the
safe (no shell=True) counterparts to @shell.run/output/code/ok/bg.

Found while auditing the engine for security gaps: every existing
@shell.* command ran through subprocess with shell=True (a string
command), which interprets shell metacharacters (;, &&, |, $(...), ...)
— the same injection surface as os.system()/subprocess.run(cmd,
shell=True) in plain Python. There was no argv-list, no-shell
alternative, meaning a Cruhon script author who wanted to safely run a
command built from partially-untrusted data (a filename from @input, a
value from an HTTP response) had no way to do so without falling back to
@raw + import subprocess — contradicting the project's own stated goal
that nothing should require @raw to escape into "real" Python.
"""
import io
import contextlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core.runner import run_source
from cruhon.core.transpiler import transpile
from cruhon.core.parser import parse


def run(src):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_source(src)
    return buf.getvalue()


class TestShellExecSafety:
    def test_shell_metacharacters_stay_literal(self):
        """The whole point: ';', '&&', etc. inside an argv element must
        NOT be interpreted as shell syntax — they're just characters in
        a string argument passed straight to the program via execve."""
        out = run(
            '@var[argv; ["echo", "safe; rm -rf /nonexistent && echo pwned"]]\n'
            '@var[o; @shell.exec_output[argv]]\n'
            '@print[{o}]'
        )
        assert out.strip() == "safe; rm -rf /nonexistent && echo pwned"
        assert "pwned" not in out.replace("&& echo pwned", "")  # not a separate line

    def test_contrasts_with_unsafe_run(self):
        """Same metacharacters DO get interpreted by the shell=True path
        — demonstrates exec[] is solving a real, reproducible gap."""
        out = run(
            '@var[cmd; "echo first && echo second"]\n'
            '@var[o; @shell.output[cmd]]\n'
            '@print[{o}]'
        )
        assert "first" in out and "second" in out
        assert out.count("\n") >= 2  # two separate output lines = shell DID interpret &&

    def test_exec_returns_completed_process(self):
        out = run(
            '@var[argv; ["echo", "hi"]]\n'
            '@var[r; @shell.exec[argv]]\n'
            '@print[{r.returncode}]'
        )
        assert out.strip() == "0"

    def test_exec_code(self):
        out = run('@var[argv; ["true"]]\n@var[c; @shell.exec_code[argv]]\n@print[{c}]')
        assert out.strip() == "0"

    def test_exec_ok_true_and_false(self):
        out_true = run('@var[argv; ["true"]]\n@var[ok; @shell.exec_ok[argv]]\n@print[{ok}]')
        assert out_true.strip() == "True"
        out_false = run('@var[argv; ["false"]]\n@var[ok; @shell.exec_ok[argv]]\n@print[{ok}]')
        assert out_false.strip() == "False"

    def test_exec_bg_runs_and_can_be_waited_on(self):
        out = run(
            '@var[argv; ["echo", "background"]]\n'
            '@var[p; @shell.exec_bg[argv]]\n'
            '@var[rc; @shell.wait[p]]\n'
            '@print[{rc}]'
        )
        assert out.strip() == "0"


class TestShellExecCompiles:
    def test_all_variants_compile(self):
        for src in [
            '@var[r; @shell.exec[["ls"]]]',
            '@var[o; @shell.exec_output[["ls"]]]',
            '@var[c; @shell.exec_code[["ls"]]]',
            '@var[ok; @shell.exec_ok[["ls"]]]',
            '@var[p; @shell.exec_bg[["ls"]]]',
        ]:
            compile(transpile(parse(src)), "<t>", "exec")
