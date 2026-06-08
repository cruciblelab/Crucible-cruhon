"""
Cruhon — A modern, extensible scripting language built on Python.
By CrucibleLab | github.com/cruciblelab/cruhon
"""

__version__ = "0.9.2"
__author__ = "CrucibleLab"

from .core import (
    run_file, run_source, build_file, check_file,
    parse, transpile, tokenize,
    ModAPI, load_all_mods,
    register_lib, register_lib_call,
)

__all__ = [
    "run_file", "run_source", "build_file", "check_file",
    "parse", "transpile", "tokenize",
    "ModAPI", "load_all_mods",
    "register_lib", "register_lib_call",
]
