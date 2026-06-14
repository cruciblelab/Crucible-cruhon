"""
cruhon/core/libs/shutil_.py
===========================
High-level file operations for Cruhon — @shutil.*

Copy, move and remove files and directory trees; query and use disk space.

━━━ COPY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shutil.copy[src; dst]          → copy file (data + permissions)
  @shutil.copy_data[src; dst]     → copy file data only (no metadata)
  @shutil.copy_tree[src; dst]     → copy entire directory tree
  @shutil.copy2[src; dst]         → copy with all metadata

━━━ MOVE / REMOVE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shutil.move[src; dst]          → move/rename file or directory
  @shutil.rm[path]                → delete a file
  @shutil.rmtree[path]            → delete a directory tree (recursive)

━━━ DISK ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shutil.disk_usage[path]        → (total, used, free) in bytes
  @shutil.free[path]              → free bytes on the partition

━━━ METADATA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shutil.copy_mode[src; dst]     → copy permission bits only
  @shutil.copy_stat[src; dst]     → copy permissions, times and flags
  @shutil.chown[path; user]       → change file owner (Unix)

━━━ FIND ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @shutil.which[name]             → full path of a CLI tool, or None
  @shutil.unpack[archive; dest]   → unpack any shutil-recognised archive
  @shutil.make_archive[base; fmt; root] → create an archive file
  @shutil.archive_formats[]       → supported archive formats
  @shutil.terminal_size[]         → (columns, lines) of the terminal
"""
from ..registry import register_lib, register_lib_call

_SH = "__import__('shutil')"
_OS = "__import__('os')"


def register():
    register_lib("shutil", None)

    # ── Copy ──────────────────────────────────────────────────
    register_lib_call("shutil", "copy",
        lambda a: f"{_SH}.copy({a[0]}, {a[1]})")
    register_lib_call("shutil", "copy_data",
        lambda a: f"{_SH}.copyfile({a[0]}, {a[1]})")
    register_lib_call("shutil", "copy_tree",
        lambda a: f"{_SH}.copytree({a[0]}, {a[1]})")
    register_lib_call("shutil", "copy2",
        lambda a: f"{_SH}.copy2({a[0]}, {a[1]})")

    # ── Move / Remove ──────────────────────────────────────────
    register_lib_call("shutil", "move",
        lambda a: f"{_SH}.move({a[0]}, {a[1]})")
    register_lib_call("shutil", "rm",
        lambda a: f"{_OS}.remove({a[0]})")
    register_lib_call("shutil", "rmtree",
        lambda a: f"{_SH}.rmtree({a[0]})")

    # ── Disk ──────────────────────────────────────────────────
    register_lib_call("shutil", "disk_usage",
        lambda a: f"{_SH}.disk_usage({a[0]})")
    register_lib_call("shutil", "free",
        lambda a: f"{_SH}.disk_usage({a[0]}).free")

    # ── Find ──────────────────────────────────────────────────
    register_lib_call("shutil", "which",
        lambda a: f"{_SH}.which({a[0]})")
    register_lib_call("shutil", "unpack",
        lambda a: f"{_SH}.unpack_archive({a[0]}, {a[1]})")
    register_lib_call("shutil", "make_archive",
        lambda a: f"{_SH}.make_archive({a[0]}, {a[1]}, {a[2]})")
    register_lib_call("shutil", "archive_formats",
        lambda a: f"{_SH}.get_archive_formats()")
    register_lib_call("shutil", "terminal_size",
        lambda a: f"tuple({_SH}.get_terminal_size())")

    # ── Metadata ──────────────────────────────────────────────
    register_lib_call("shutil", "copy_mode",
        lambda a: f"{_SH}.copymode({a[0]}, {a[1]})")
    register_lib_call("shutil", "copy_stat",
        lambda a: f"{_SH}.copystat({a[0]}, {a[1]})")
    register_lib_call("shutil", "chown",
        lambda a: f"{_SH}.chown({a[0]}, {a[1]})")
