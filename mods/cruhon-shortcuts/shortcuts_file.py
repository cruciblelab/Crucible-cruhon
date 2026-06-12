"""
cruhon-shortcuts — file group
==============================
Shortcuts for @file.* operations.

Global aliases (source rewrites)
─────────────────────────────────
@read[path]             → @file.read[path]
@write[path; text]      → @file.write[path; text]
@append[path; text]     → @file.append[path; text]
@lines[path]            → @file.lines[path]
@bytes_read[path]       → @file.bytes[path]
@cat[path]              → @file.read[path]
@ls[path]               → @file.list[path]
@glob[pattern]          → @file.glob[pattern]
@walk[dir]              → @file.walk[dir]
@rm[path]               → @file.delete[path]
@rmdir[path]            → @file.rmdir[path]
@mv[src; dst]           → @file.move[src; dst]
@cp[src; dst]           → @file.copy[src; dst]
@mkdir[path]            → @file.mkdir[path]
@touch[path]            → @file.touch[path]
@chmod[path; mode]      → @file.chmod[path; mode]
@symlink[src; dst]      → @file.symlink[src; dst]
@jread[path]            → @file.read_json[path]
@jwrite[path; obj]      → @file.write_json[path; obj]
@exists[path]           → @file.exists[path]
@isfile[path]           → @file.is_file[path]
@isdir[path]            → @file.is_dir[path]
@abspath[path]          → @file.abspath[path]
@realpath[path]         → @file.realpath[path]
@basename[path]         → @file.basename[path]
@dirname[path]          → @file.dirname[path]
@joinpath[a; b]         → @file.join[a; b]
@ext[path]              → @file.ext[path]
@stem[path]             → @file.stem[path]
@cwd[]                  → @file.cwd[]
@home[]                 → @file.home[]
@ftemp[]                → @file.temp[]
@ftempdir[]             → @file.tempdir[]

Namespace method aliases
─────────────────────────
@file.cat[path]                   → @file.read[path]
@file.open[path]                  → @file.read[path]
@file.slurp[path]                 → @file.read[path]
@file.save[path; text]            → @file.write[path; text]
@file.spit[path; text]            → @file.write[path; text]
@file.ls[path]                    → @file.list[path]
@file.dir[path]                   → @file.list[path]
@file.rm[path]                    → @file.delete[path]
@file.del[path]                   → @file.delete[path]
@file.mv[src; dst]                → @file.move[src; dst]
@file.cp[src; dst]                → @file.copy[src; dst]
@file.copytree[src; dst]          → already exists
@file.name[path]                  → @file.basename[path]
@file.parent[path]                → @file.dirname[path]

New methods (via api.lib_call)
───────────────────────────────
@file.head[path]                  → first 10 lines
@file.head[path; n]               → first N lines
@file.tail[path]                  → last 10 lines
@file.tail[path; n]               → last N lines
@file.count_lines[path]           → number of lines in file
@file.grep[path; pattern]         → lines matching regex pattern
@file.grep[path; pattern; flags]  → with re flags (e.g. "i" for ignore-case)
@file.first_line[path]            → first non-empty line
@file.last_line[path]             → last non-empty line
@file.size_kb[path]               → file size in kilobytes (float)
@file.size_mb[path]               → file size in megabytes (float)
@file.replace_text[path; old; new] → replace text in file, return new content
@file.append_line[path; text]     → append a line (with newline)
@file.prepend[path; text]         → write text then original content
@file.contains[path; text]        → True if file text contains substring
@file.line_count[path]            → alias for count_lines
@file.wc[path]                    → (lines, words, chars) tuple
@file.md5[path]                   → MD5 hex digest of file content
@file.sha256_file[path]           → SHA-256 hex digest of file content
@file.newer[a; b]                 → True if file a is newer than b
@file.older[a; b]                 → True if file a is older than b
@file.empty[path]                 → True if file is empty
@file.ensure[path]                → touch path, return it
"""
from __future__ import annotations

# ─────────────────────────────────────────────────────────────
# SOURCE REWRITES
# key   = what the user writes (including @)
# value = what it becomes after the before_parse hook runs
# ─────────────────────────────────────────────────────────────

GLOBAL_REWRITES: dict[str, str] = {
    "@read[":       "@file.read[",
    "@write[":      "@file.write[",
    "@append[":     "@file.append[",
    "@lines[":      "@file.lines[",
    "@bytes_read[": "@file.bytes[",
    "@cat[":        "@file.read[",
    "@ls[":         "@file.list[",
    "@glob[":       "@file.glob[",
    "@walk[":       "@file.walk[",
    "@rm[":         "@file.delete[",
    "@rmdir[":      "@file.rmdir[",
    "@mv[":         "@file.move[",
    "@cp[":         "@file.copy[",
    "@mkdir[":      "@file.mkdir[",
    "@touch[":      "@file.touch[",
    "@chmod[":      "@file.chmod[",
    "@symlink[":    "@file.symlink[",
    "@jread[":      "@file.read_json[",
    "@jwrite[":     "@file.write_json[",
    "@exists[":     "@file.exists[",
    "@isfile[":     "@file.is_file[",
    "@isdir[":      "@file.is_dir[",
    "@abspath[":    "@file.abspath[",
    "@realpath[":   "@file.realpath[",
    "@basename[":   "@file.basename[",
    "@dirname[":    "@file.dirname[",
    "@joinpath[":   "@file.join[",
    "@ext[":        "@file.ext[",
    "@stem[":       "@file.stem[",
    "@cwd[":        "@file.cwd[",
    "@home[":       "@file.home[",
    "@ftemp[":      "@file.temp[",
    "@ftempdir[":   "@file.tempdir[",
}

METHOD_ALIASES: dict[str, str] = {
    "@file.cat[":   "@file.read[",
    "@file.open[":  "@file.read[",
    "@file.slurp[": "@file.read[",
    "@file.save[":  "@file.write[",
    "@file.spit[":  "@file.write[",
    "@file.ls[":    "@file.list[",
    "@file.dir[":   "@file.list[",
    "@file.rm[":    "@file.delete[",
    "@file.del[":   "@file.delete[",
    "@file.mv[":    "@file.move[",
    "@file.cp[":    "@file.copy[",
    "@file.name[":  "@file.basename[",
    "@file.parent[":"@file.dirname[",
}

_P = "__import__('pathlib').Path"
_OS = "__import__('os')"
_RE = "__import__('re')"
_HH = "__import__('hashlib')"


def _new_lib_calls(api) -> None:
    """Register genuinely new @file.* methods that have no core equivalent."""

    api.lib_call("file", "head", lambda a: (
        f"open({a[0]}, encoding='utf-8').readlines()[:{a[1]}]"
        if len(a) > 1 else
        f"open({a[0]}, encoding='utf-8').readlines()[:10]"
    ))

    api.lib_call("file", "tail", lambda a: (
        f"open({a[0]}, encoding='utf-8').readlines()[-{a[1]}:]"
        if len(a) > 1 else
        f"open({a[0]}, encoding='utf-8').readlines()[-10:]"
    ))

    api.lib_call("file", "count_lines", lambda a: (
        f"sum(1 for _ in open({a[0]}, encoding='utf-8'))"
    ))

    api.lib_call("file", "line_count", lambda a: (
        f"sum(1 for _ in open({a[0]}, encoding='utf-8'))"
    ))

    api.lib_call("file", "grep", lambda a: (
        f"[l for l in open({a[0]}, encoding='utf-8').readlines() "
        f"if {_RE}.search({a[1]}, l, flags={_RE}.IGNORECASE if {a[2]!r}=='i' else 0)]"
        if len(a) > 2 else
        f"[l for l in open({a[0]}, encoding='utf-8').readlines() "
        f"if {_RE}.search({a[1]}, l)]"
    ))

    api.lib_call("file", "first_line", lambda a: (
        f"next((l.rstrip('\\n') for l in open({a[0]}, encoding='utf-8') if l.strip()), '')"
    ))

    api.lib_call("file", "last_line", lambda a: (
        f"(lambda lines: lines[-1].rstrip('\\n') if lines else '')"
        f"(open({a[0]}, encoding='utf-8').readlines())"
    ))

    api.lib_call("file", "size_kb", lambda a: (
        f"{_OS}.path.getsize({a[0]}) / 1024"
    ))

    api.lib_call("file", "size_mb", lambda a: (
        f"{_OS}.path.getsize({a[0]}) / (1024 * 1024)"
    ))

    api.lib_call("file", "replace_text", lambda a: (
        f"(lambda _p, _o, _n: (open(_p, 'w', encoding='utf-8').write("
        f"(lambda _t: _t.replace(_o, _n))("
        f"open(_p, encoding='utf-8').read())) or "
        f"open(_p, encoding='utf-8').read())"
        f")({a[0]}, {a[1]}, {a[2]})"
        if len(a) > 2 else
        f"'replace_text requires 3 arguments: path, old, new'"
    ))

    api.lib_call("file", "append_line", lambda a: (
        f"open({a[0]}, 'a', encoding='utf-8').write({a[1]} + '\\n')"
    ))

    api.lib_call("file", "prepend", lambda a: (
        f"(lambda _p, _t: open(_p, 'w', encoding='utf-8').write("
        f"_t + open(_p, encoding='utf-8').read()))({a[0]}, {a[1]})"
        if len(a) > 1 else
        f"None"
    ))

    api.lib_call("file", "contains", lambda a: (
        f"({a[1]} in open({a[0]}, encoding='utf-8').read())"
        if len(a) > 1 else
        f"False"
    ))

    api.lib_call("file", "wc", lambda a: (
        f"(lambda _t: (len(_t.splitlines()), len(_t.split()), len(_t)))"
        f"(open({a[0]}, encoding='utf-8').read())"
    ))

    api.lib_call("file", "md5", lambda a: (
        f"{_HH}.md5(open({a[0]}, 'rb').read()).hexdigest()"
    ))

    api.lib_call("file", "sha256_file", lambda a: (
        f"{_HH}.sha256(open({a[0]}, 'rb').read()).hexdigest()"
    ))

    api.lib_call("file", "newer", lambda a: (
        f"({_OS}.path.getmtime({a[0]}) > {_OS}.path.getmtime({a[1]}))"
        if len(a) > 1 else
        f"False"
    ))

    api.lib_call("file", "older", lambda a: (
        f"({_OS}.path.getmtime({a[0]}) < {_OS}.path.getmtime({a[1]}))"
        if len(a) > 1 else
        f"False"
    ))

    api.lib_call("file", "empty", lambda a: (
        f"({_OS}.path.getsize({a[0]}) == 0)"
    ))

    api.lib_call("file", "ensure", lambda a: (
        f"(lambda _p: ({_P}(_p).touch(), _p)[1])({a[0]})"
    ))


def register_group(api, cfg) -> dict[str, str]:
    """
    Register file shortcuts.

    Returns the combined rewrites dict (global + namespace aliases)
    so the caller can merge it into the global before_parse hook.
    """
    rewrites: dict[str, str] = {}

    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))

    if cfg.method_aliases:
        _new_lib_calls(api)

    return rewrites
