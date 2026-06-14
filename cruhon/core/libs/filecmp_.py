"""
cruhon/core/libs/filecmp_.py
============================
File and directory comparison for Cruhon — @filecmp.*

Check whether files are identical and diff entire directory trees.

━━━ FILES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @filecmp.equal[a; b]            → bool: are two files byte-for-byte equal?
  @filecmp.shallow[a; b]          → bool: quick stat-based comparison

━━━ DIRS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @filecmp.dircmp[a; b]           → dircmp object for two directories
  @filecmp.same_files[a; b]       → files present in both dirs that match
  @filecmp.diff_files[a; b]       → files present in both dirs that differ
  @filecmp.left_only[a; b]        → files only in directory a
  @filecmp.right_only[a; b]       → files only in directory b
  @filecmp.common[a; b]           → names present in both directories
  @filecmp.compare[a; b; names]   → (match, mismatch, errors) for given names
  @filecmp.clear_cache[]          → clear the comparison cache
"""
from ..registry import register_lib, register_lib_call

_FC = "__import__('filecmp')"


def register():
    register_lib("filecmp", None)

    # ── Files ─────────────────────────────────────────────────
    register_lib_call("filecmp", "equal",
        lambda a: f"{_FC}.cmp({a[0]}, {a[1]}, shallow=False)")
    register_lib_call("filecmp", "shallow",
        lambda a: f"{_FC}.cmp({a[0]}, {a[1]}, shallow=True)")

    # ── Dirs ──────────────────────────────────────────────────
    register_lib_call("filecmp", "dircmp",
        lambda a: f"{_FC}.dircmp({a[0]}, {a[1]})")
    register_lib_call("filecmp", "same_files",
        lambda a: f"{_FC}.dircmp({a[0]}, {a[1]}).same_files")
    register_lib_call("filecmp", "diff_files",
        lambda a: f"{_FC}.dircmp({a[0]}, {a[1]}).diff_files")
    register_lib_call("filecmp", "left_only",
        lambda a: f"{_FC}.dircmp({a[0]}, {a[1]}).left_only")
    register_lib_call("filecmp", "right_only",
        lambda a: f"{_FC}.dircmp({a[0]}, {a[1]}).right_only")
    register_lib_call("filecmp", "common",
        lambda a: f"{_FC}.dircmp({a[0]}, {a[1]}).common")
    register_lib_call("filecmp", "compare",
        lambda a: f"{_FC}.cmpfiles({a[0]}, {a[1]}, {a[2]})")
    register_lib_call("filecmp", "clear_cache",
        lambda a: f"{_FC}.clear_cache()")
