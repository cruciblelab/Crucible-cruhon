"""
cruhon-shortcuts-pro — file group
====================================
Higher-level file shortcuts built on @file.* and stdlib pathlib/os.

Global aliases (source rewrites)
─────────────────────────────────
@read_file[path]            → @file.read[path]
@write_file[path; content]  → @file.write[path; content]
@append_file[path; content] → @file.append[path; content]
@file_lines[path]           → @file.lines[path]
@file_exists[path]          → @file.exists[path]
@file_size[path]            → @file.size[path]
@file_ext[path]             → @file.ext[path]
@file_name[path]            → @file.name[path]
@file_dir[path]             → @file.dir[path]
@glob_files[pattern]        → @file.glob[pattern]
@list_dir[path]             → @file.list[path]
@make_dir[path]             → @file.mkdir[path]
@del_file[path]             → @file.delete[path]
@copy_file[src; dst]        → @file.copy[src; dst]
@move_file[src; dst]        → @file.move[src; dst]

New methods (via api.lib_call)
───────────────────────────────
@file.stem[path]            → filename without extension
@file.absolute[path]        → absolute path string
@file.read_bytes[path]      → raw bytes from file
@file.write_bytes[p; b]     → write bytes to file
@file.is_dir[path]          → True if path is a directory
@file.is_file[path]         → True if path is a regular file
@file.modified[path]        → last modified timestamp (float)
@file.touch[path]           → create file if not exists
@file.line_count[path]      → number of lines in file
@file.find[dir; pattern]    → list all matching files recursively
@file.relpath[path; base]   → relative path from base
@file.joinpath[a; b]        → join two path segments
@file.parent[path]          → parent directory string
@file.with_suffix[p; ext]   → change file extension
@file.stat[path]            → os.stat result for path
"""
from __future__ import annotations

_PL = "__import__('pathlib').Path"
_OS = "__import__('os')"
_SH = "__import__('shutil')"

GLOBAL_REWRITES: dict[str, str] = {
    "@read_file[":    "@file.read[",
    "@write_file[":   "@file.write[",
    "@append_file[":  "@file.append[",
    "@file_lines[":   "@file.lines[",
    "@file_exists[":  "@file.exists[",
    "@file_size[":    "@file.size[",
    "@file_ext[":     "@file.ext[",
    "@file_name[":    "@file.basename[",
    "@file_dir[":     "@file.dirname[",
    "@glob_files[":   "@file.glob[",
    "@list_dir[":     "@file.list[",
    "@make_dir[":     "@file.mkdir[",
    "@del_file[":     "@file.delete[",
    "@copy_file[":    "@file.copy[",
    "@move_file[":    "@file.move[",
}

METHOD_ALIASES: dict[str, str] = {
    "@file.remove[":  "@file.delete[",
    "@file.ls[":      "@file.list[",
    "@file.cd[":      "@file.cwd[",
}


def _new_lib_calls(api) -> None:
    # Only methods NOT already in cruhon/core/libs/file_.py
    api.lib_call("file", "find", lambda a: (
        f"[str(__p) for __p in {_PL}({a[0]}).rglob({a[1]})]"
        if len(a) >= 2 else "[]"
    ))

    api.lib_call("file", "relpath", lambda a: (
        f"str({_PL}({a[0]}).relative_to({a[1]}))"
        if len(a) >= 2 else f"str({_PL}({a[0]}))" if a else "''"
    ))

    api.lib_call("file", "joinpath", lambda a: (
        f"str({_PL}({a[0]}) / {a[1]})"
        if len(a) >= 2 else f"str({_PL}({a[0]}))" if a else "''"
    ))

    api.lib_call("file", "parent", lambda a: (
        f"str({_PL}({a[0]}).parent)" if a else "''"
    ))

    api.lib_call("file", "with_suffix", lambda a: (
        f"str({_PL}({a[0]}).with_suffix({a[1]}))"
        if len(a) >= 2 else f"str({_PL}({a[0]}))" if a else "''"
    ))

    api.lib_call("file", "line_count", lambda a: (
        f"sum(1 for _ in open({a[0]}, encoding='utf-8'))" if a else "0"
    ))

    api.lib_call("file", "read_bytes", lambda a: (
        f"{_PL}({a[0]}).read_bytes()" if a else "b''"
    ))

    api.lib_call("file", "write_lines", lambda a: (
        f"({_PL}({a[0]}).write_text('\\n'.join(str(__ln) for __ln in {a[1]}), encoding='utf-8'), None)[1]"
        if len(a) >= 2 else "None"
    ))

    api.lib_call("file", "modified", lambda a: (
        f"{_PL}({a[0]}).stat().st_mtime" if a else "0.0"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
