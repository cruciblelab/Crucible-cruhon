"""
System & platform information for Cruhon — @platform.*

Wraps Python's `platform` module: identify the OS, hardware, and Python
runtime. No `@import` needed.

━━━ OPERATING SYSTEM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @platform.system[]         → "Linux" / "Darwin" / "Windows"
  @platform.release[]        → OS release string
  @platform.version[]        → OS version string
  @platform.platform[]       → single descriptive platform string
  @platform.node[]           → network host name

━━━ HARDWARE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @platform.machine[]        → machine type ("x86_64", "arm64", …)
  @platform.processor[]      → processor name
  @platform.architecture[]   → (bits, linkage) tuple, e.g. ("64bit", "ELF")

━━━ PYTHON RUNTIME ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @platform.python_version[]       → "3.11.5"
  @platform.python_version_tuple[] → ("3", "11", "5")
  @platform.python_impl[]          → "CPython" / "PyPy" …
  @platform.python_compiler[]      → compiler used to build Python

━━━ HELPERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @platform.uname[]          → full platform.uname() named tuple
  @platform.is_windows[]     → True on Windows
  @platform.is_linux[]       → True on Linux
  @platform.is_mac[]         → True on macOS
  @platform.is_64bit[]       → True if running a 64-bit Python
"""
from ..registry import register_lib, register_lib_call

_PF = "__import__('platform')"


def register():
    register_lib("platform", "platform")

    # ── OPERATING SYSTEM ──────────────────────────────────────
    register_lib_call("platform", "system",      lambda a: f"{_PF}.system()")
    register_lib_call("platform", "release",     lambda a: f"{_PF}.release()")
    register_lib_call("platform", "version",     lambda a: f"{_PF}.version()")
    register_lib_call("platform", "platform",    lambda a: f"{_PF}.platform()")
    register_lib_call("platform", "node",        lambda a: f"{_PF}.node()")

    # ── HARDWARE ──────────────────────────────────────────────
    register_lib_call("platform", "machine",     lambda a: f"{_PF}.machine()")
    register_lib_call("platform", "processor",   lambda a: f"{_PF}.processor()")
    register_lib_call("platform", "architecture",lambda a: f"{_PF}.architecture()")

    # ── PYTHON RUNTIME ────────────────────────────────────────
    register_lib_call("platform", "python_version",       lambda a: f"{_PF}.python_version()")
    register_lib_call("platform", "python_version_tuple", lambda a: f"{_PF}.python_version_tuple()")
    register_lib_call("platform", "python_impl",          lambda a: f"{_PF}.python_implementation()")
    register_lib_call("platform", "python_compiler",      lambda a: f"{_PF}.python_compiler()")

    # ── HELPERS ───────────────────────────────────────────────
    register_lib_call("platform", "uname",       lambda a: f"{_PF}.uname()")
    register_lib_call("platform", "is_windows",  lambda a: f"({_PF}.system() == 'Windows')")
    register_lib_call("platform", "is_linux",    lambda a: f"({_PF}.system() == 'Linux')")
    register_lib_call("platform", "is_mac",      lambda a: f"({_PF}.system() == 'Darwin')")
    register_lib_call("platform", "is_64bit",    lambda a: f"({_PF}.architecture()[0] == '64bit')")
