"""Statistics stdlib wrappers for Cruhon — @statistics.*"""
from ..registry import register_lib, register_lib_call

_ST = "__import__('statistics')"


def register():
    register_lib("statistics", "statistics")

    register_lib_call("statistics", "mean",
        lambda a: f"{_ST}.mean({a[0]})")

    register_lib_call("statistics", "fmean",
        lambda a: f"{_ST}.fmean({a[0]})")

    register_lib_call("statistics", "geometric_mean",
        lambda a: f"{_ST}.geometric_mean({a[0]})")

    register_lib_call("statistics", "harmonic_mean",
        lambda a: f"{_ST}.harmonic_mean({a[0]})")

    register_lib_call("statistics", "median",
        lambda a: f"{_ST}.median({a[0]})")

    register_lib_call("statistics", "median_low",
        lambda a: f"{_ST}.median_low({a[0]})")

    register_lib_call("statistics", "median_high",
        lambda a: f"{_ST}.median_high({a[0]})")

    register_lib_call("statistics", "median_grouped",
        lambda a: f"{_ST}.median_grouped({a[0]}{', interval=' + a[1] if len(a)>1 else ''})")

    register_lib_call("statistics", "mode",
        lambda a: f"{_ST}.mode({a[0]})")

    register_lib_call("statistics", "multimode",
        lambda a: f"{_ST}.multimode({a[0]})")

    register_lib_call("statistics", "quantiles",
        lambda a: f"{_ST}.quantiles({a[0]}, n={a[1] if len(a)>1 else 4})")

    register_lib_call("statistics", "stdev",
        lambda a: f"{_ST}.stdev({a[0]})")

    register_lib_call("statistics", "pstdev",
        lambda a: f"{_ST}.pstdev({a[0]})")

    register_lib_call("statistics", "variance",
        lambda a: f"{_ST}.variance({a[0]})")

    register_lib_call("statistics", "pvariance",
        lambda a: f"{_ST}.pvariance({a[0]})")

    register_lib_call("statistics", "correlation",
        lambda a: f"{_ST}.correlation({a[0]}, {a[1]})" if len(a) > 1 else f"{_ST}.correlation({a[0]}, {a[0]})")

    register_lib_call("statistics", "covariance",
        lambda a: f"{_ST}.covariance({a[0]}, {a[1]})" if len(a) > 1 else f"{_ST}.covariance({a[0]}, {a[0]})")

    register_lib_call("statistics", "linear_regression",
        lambda a: f"{_ST}.linear_regression({a[0]}, {a[1]})" if len(a) > 1 else f"{_ST}.linear_regression({a[0]}, {a[0]})")
