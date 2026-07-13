"""
Tests for @math.* methods that README/library.md always documented
(clamp, lerp, sign, hypot, dist, gcd, lcm, factorial, comb, perm, prod,
degrees, radians, log2, log10, exp, sin/cos/tan/asin/acos/atan/atan2,
isclose/isfinite/isinf/isnan, e/tau/inf/nan, min/max/sum) but were never
actually registered — @math.clamp[...] raised NameError: name 'math' is
not defined (silently falling through to the generic "namespace.method(args)"
fallback in visit_LibCallNode, since get_lib_call returned None).
"""
import math as _pymath
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core.runner import run_source


def run(src):
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_source(src)
    return buf.getvalue().strip()


class TestMathExtended:
    def test_clamp_within_range(self):
        assert run('@var[x; @math.clamp[25; 0; 50]]\n@print[{x}]') == "25"

    def test_clamp_above_max(self):
        assert run('@var[x; @math.clamp[57; 0; 50]]\n@print[{x}]') == "50"

    def test_clamp_below_min(self):
        assert run('@var[x; @math.clamp[-5; 0; 50]]\n@print[{x}]') == "0"

    def test_lerp(self):
        assert run('@var[x; @math.lerp[0; 10; 0.5]]\n@print[{x}]') == "5.0"

    def test_sign_positive(self):
        assert run('@var[x; @math.sign[7]]\n@print[{x}]') == "1"

    def test_sign_negative(self):
        assert run('@var[x; @math.sign[-7]]\n@print[{x}]') == "-1"

    def test_sign_zero(self):
        assert run('@var[x; @math.sign[0]]\n@print[{x}]') == "0"

    def test_hypot(self):
        assert run('@var[x; @math.hypot[3; 4]]\n@print[{x}]') == "5.0"

    def test_dist(self):
        out = run('@var[a; (0, 0)]\n@var[b; (3, 4)]\n@var[x; @math.dist[a; b]]\n@print[{x}]')
        assert out == "5.0"

    def test_gcd(self):
        assert run('@var[x; @math.gcd[12; 18]]\n@print[{x}]') == "6"

    def test_lcm(self):
        assert run('@var[x; @math.lcm[4; 6]]\n@print[{x}]') == "12"

    def test_factorial(self):
        assert run('@var[x; @math.factorial[5]]\n@print[{x}]') == "120"

    def test_comb(self):
        assert run('@var[x; @math.comb[5; 2]]\n@print[{x}]') == "10"

    def test_perm(self):
        assert run('@var[x; @math.perm[5; 2]]\n@print[{x}]') == "20"

    def test_prod(self):
        assert run('@var[nums; [1, 2, 3, 4]]\n@var[x; @math.prod[nums]]\n@print[{x}]') == "24"

    def test_degrees(self):
        out = float(run(f'@var[x; @math.degrees[{_pymath.pi}]]\n@print[{{x}}]'))
        assert abs(out - 180.0) < 1e-6

    def test_radians(self):
        out = float(run('@var[x; @math.radians[180]]\n@print[{x}]'))
        assert abs(out - _pymath.pi) < 1e-6

    def test_log2(self):
        assert run('@var[x; @math.log2[8]]\n@print[{x}]') == "3.0"

    def test_log10(self):
        assert run('@var[x; @math.log10[1000]]\n@print[{x}]') == "3.0"

    def test_exp(self):
        out = float(run('@var[x; @math.exp[1]]\n@print[{x}]'))
        assert abs(out - _pymath.e) < 1e-9

    def test_sin_cos_tan(self):
        assert run('@var[x; @math.sin[0]]\n@print[{x}]') == "0.0"
        assert run('@var[x; @math.cos[0]]\n@print[{x}]') == "1.0"

    def test_atan2(self):
        out = float(run('@var[x; @math.atan2[1; 1]]\n@print[{x}]'))
        assert abs(out - _pymath.pi / 4) < 1e-9

    def test_isclose(self):
        assert run('@var[x; @math.isclose[1.0; 1.0000000001]]\n@print[{x}]') == "True"

    def test_isnan(self):
        assert run("@var[x; @math.isnan[float('nan')]]\n@print[{x}]") == "True"

    def test_e_tau_inf_nan_constants(self):
        assert abs(float(run('@var[x; @math.e[]]\n@print[{x}]')) - _pymath.e) < 1e-12
        assert abs(float(run('@var[x; @math.tau[]]\n@print[{x}]')) - _pymath.tau) < 1e-12
        assert run('@var[x; @math.inf[]]\n@print[{x}]') == "inf"

    def test_min_max_sum(self):
        assert run('@var[n; [3, 1, 4, 1, 5]]\n@var[x; @math.min[n]]\n@print[{x}]') == "1"
        assert run('@var[n; [3, 1, 4, 1, 5]]\n@var[x; @math.max[n]]\n@print[{x}]') == "5"
        assert run('@var[n; [3, 1, 4, 1, 5]]\n@var[x; @math.sum[n]]\n@print[{x}]') == "14"
