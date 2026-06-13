"""
cruhon/core/libs/sysconfig_.py
==============================
Python installation paths & config for Cruhon — @sysconfig.*

Query where Python keeps its files and how it was built.

━━━ PATHS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sysconfig.paths[]              → dict of all installation paths
  @sysconfig.path[name]           → one path ("purelib", "scripts", …)
  @sysconfig.path_names[]         → list of valid path names

━━━ CONFIG ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @sysconfig.vars[]               → dict of all configuration variables
  @sysconfig.var[name]            → a single config variable
  @sysconfig.platform[]           → platform identifier ("linux-x86_64")
  @sysconfig.version[]            → "3.11" style Python version string
"""
from ..registry import register_lib, register_lib_call

_SC = "__import__('sysconfig')"


def register():
    register_lib("sysconfig", None)

    # ── Paths ─────────────────────────────────────────────────
    register_lib_call("sysconfig", "paths",
        lambda a: f"{_SC}.get_paths()")
    register_lib_call("sysconfig", "path",
        lambda a: f"{_SC}.get_path({a[0]})")
    register_lib_call("sysconfig", "path_names",
        lambda a: f"list({_SC}.get_path_names())")

    # ── Config ────────────────────────────────────────────────
    register_lib_call("sysconfig", "vars",
        lambda a: f"{_SC}.get_config_vars()")
    register_lib_call("sysconfig", "var",
        lambda a: f"{_SC}.get_config_var({a[0]})")
    register_lib_call("sysconfig", "platform",
        lambda a: f"{_SC}.get_platform()")
    register_lib_call("sysconfig", "version",
        lambda a: f"{_SC}.get_python_version()")
