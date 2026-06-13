"""
cruhon/core/libs/glob_.py
=========================
Glob wrappers for Cruhon — @glob.*

Deeper than @file.glob: recursive search, sorting, filtering by type,
size, date — all without @raw.

━━━ BASIC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @glob.glob[pattern]             → list of matching paths
  @glob.rglob[dir; pattern]       → recursive glob (** added automatically)
  @glob.escape[path]              → escape special glob characters

━━━ FILES & DIRS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @glob.files[dir]                → all files in dir (non-recursive)
  @glob.files[dir; pattern]       → files matching shell pattern
  @glob.files_r[dir]              → all files recursively
  @glob.files_r[dir; pattern]     → recursive + pattern
  @glob.dirs[dir]                 → immediate subdirectories
  @glob.dirs_r[dir]               → all subdirectories recursively
  @glob.by_ext[dir; ext]          → files with extension (e.g. "py" or ".py")
  @glob.by_ext_r[dir; ext]        → same, recursive

━━━ PREDICATES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @glob.count[pattern]            → int: number of matches
  @glob.any[pattern]              → bool: at least one match
  @glob.first[pattern]            → first match or None

━━━ SORT / SELECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @glob.newest[pattern]           → most recently modified path
  @glob.oldest[pattern]           → oldest path
  @glob.largest[pattern]          → largest file by byte size
  @glob.sort_by_name[pattern]     → sorted alphabetically
  @glob.sort_by_date[pattern]     → sorted by modification time (oldest first)
  @glob.sort_by_size[pattern]     → sorted by size (smallest first)
"""
from ..registry import register_lib, register_lib_call


def register():
    register_lib("glob", None)

    # ── Basic ──────────────────────────────────────────────────
    register_lib_call("glob", "glob",
        lambda a: f"__import__('glob').glob({a[0]})")

    register_lib_call("glob", "rglob",
        lambda a: (
            f"__import__('glob').glob(__import__('os').path.join({a[0]}, '**', {a[1]}), recursive=True)"
        ))

    register_lib_call("glob", "escape",
        lambda a: f"__import__('glob').escape({a[0]})")

    # ── Files & Dirs ──────────────────────────────────────────
    register_lib_call("glob", "files",
        lambda a: (
            f"[_p for _p in __import__('glob').glob(__import__('os').path.join({a[0]}, {a[1]})) if __import__('os').path.isfile(_p)]"
            if len(a) > 1 else
            f"[_p for _p in __import__('glob').glob(__import__('os').path.join({a[0]}, '*')) if __import__('os').path.isfile(_p)]"
        ))

    register_lib_call("glob", "files_r",
        lambda a: (
            f"[_p for _p in __import__('glob').glob(__import__('os').path.join({a[0]}, '**', {a[1]}), recursive=True) if __import__('os').path.isfile(_p)]"
            if len(a) > 1 else
            f"[_p for _p in __import__('glob').glob(__import__('os').path.join({a[0]}, '**'), recursive=True) if __import__('os').path.isfile(_p)]"
        ))

    register_lib_call("glob", "dirs",
        lambda a: (
            f"[_p for _p in __import__('glob').glob(__import__('os').path.join({a[0]}, '*')) if __import__('os').path.isdir(_p)]"
        ))

    register_lib_call("glob", "dirs_r",
        lambda a: (
            f"(lambda _d: [_p for _p in __import__('glob').glob(__import__('os').path.join(_d, '**'), recursive=True) if __import__('os').path.isdir(_p) and __import__('os').path.normpath(_p) != __import__('os').path.normpath(_d)])({a[0]})"
        ))

    register_lib_call("glob", "by_ext",
        lambda a: (
            f"(lambda _d, _e: [_p for _p in __import__('glob').glob(__import__('os').path.join(_d, '*.' + _e.lstrip('.'))) if __import__('os').path.isfile(_p)])({a[0]}, {a[1]})"
        ))

    register_lib_call("glob", "by_ext_r",
        lambda a: (
            f"(lambda _d, _e: [_p for _p in __import__('glob').glob(__import__('os').path.join(_d, '**', '*.' + _e.lstrip('.')), recursive=True) if __import__('os').path.isfile(_p)])({a[0]}, {a[1]})"
        ))

    # ── Predicates ────────────────────────────────────────────
    register_lib_call("glob", "count",
        lambda a: f"len(__import__('glob').glob({a[0]}))")

    register_lib_call("glob", "any",
        lambda a: f"bool(__import__('glob').glob({a[0]}))")

    register_lib_call("glob", "first",
        lambda a: f"(lambda _m: _m[0] if _m else None)(__import__('glob').glob({a[0]}))")

    # ── Sort / Select ─────────────────────────────────────────
    register_lib_call("glob", "newest",
        lambda a: (
            f"(lambda _m: max(_m, key=__import__('os').path.getmtime) if _m else None)(__import__('glob').glob({a[0]}))"
        ))

    register_lib_call("glob", "oldest",
        lambda a: (
            f"(lambda _m: min(_m, key=__import__('os').path.getmtime) if _m else None)(__import__('glob').glob({a[0]}))"
        ))

    register_lib_call("glob", "largest",
        lambda a: (
            f"(lambda _m: max((_p for _p in _m if __import__('os').path.isfile(_p)), key=__import__('os').path.getsize, default=None))(__import__('glob').glob({a[0]}))"
        ))

    register_lib_call("glob", "sort_by_name",
        lambda a: f"sorted(__import__('glob').glob({a[0]}))")

    register_lib_call("glob", "sort_by_date",
        lambda a: f"sorted(__import__('glob').glob({a[0]}), key=__import__('os').path.getmtime)")

    register_lib_call("glob", "sort_by_size",
        lambda a: (
            f"sorted((_p for _p in __import__('glob').glob({a[0]}) if __import__('os').path.isfile(_p)), key=__import__('os').path.getsize)"
        ))
