"""
cruhon-shortcuts — system group
=================================
Shortcuts for @shell.* and @sys.* operations.

Global aliases (source rewrites)
─────────────────────────────────
@run[cmd]               → @shell.run[cmd]
@cmd[cmd]               → @shell.output[cmd]
@shell_lines[cmd]       → @shell.lines[cmd]
@shell_code[cmd]        → @shell.code[cmd]
@shell_ok[cmd]          → @shell.ok[cmd]
@bg[cmd]                → @shell.bg[cmd]
@pipe[cmds]             → @shell.pipe[cmds]
@env_get[name]          → @shell.env[name]
@env_set[name; val]     → @shell.env_set[name; val]
@env_del[name]          → @shell.env_del[name]
@env_all[]              → @shell.env_all[]
@which[name]            → @shell.which[name]
@shell_exists[name]     → @shell.exists[name]
@sh_cwd[]               → @shell.cwd[]
@sh_cd[path]            → @shell.cd[path]
@sh_args[]              → @shell.args[]
@sh_exit[code]          → @shell.exit[code]
@sh_platform[]          → @shell.platform[]
@python_version[]       → @shell.python_version[]
@sh_pid[]               → @shell.pid[]
@cpu_count[]            → @shell.cpu_count[]
@hostname[]             → @shell.hostname[]
@sys_argv[]             → @sys.argv[]
@sys_exit[code]         → @sys.exit[code]
@sys_path[]             → @sys.path[]
@sys_version[]          → @sys.version[]
@sys_platform[]         → @sys.platform[]
@sys_maxsize[]          → @sys.maxsize[]
@sys_stdin[]            → @sys.stdin[]
@sys_stdout[]           → @sys.stdout[]
@sys_stderr[]           → @sys.stderr[]
@sys_modules[]          → @sys.modules[]
@sys_executable[]       → @sys.executable[]
@sizeof[obj]            → @sys.getsizeof[obj]
@recursion_limit[]      → @sys.getrecursionlimit[]
@set_recursion[n]       → @sys.setrecursionlimit[n]

Namespace method aliases
─────────────────────────
@shell.cmd[cmd]         → @shell.output[cmd]
@shell.exec[cmd]        → @shell.run[cmd]
@shell.capture[cmd]     → @shell.output[cmd]
@shell.is_ok[cmd]       → @shell.ok[cmd]
@shell.get_env[name]    → @shell.env[name]
@sys.arg[n]             → @sys.argv_get[n]
@sys.ver[]              → @sys.version[]
@sys.py_ver[]           → @sys.version_info[]
@sys.size[obj]          → @sys.getsizeof[obj]

New methods (via api.lib_call)
───────────────────────────────
@shell.run_capture[cmd]     → run and capture both stdout and stderr
@shell.run_lines[cmd]       → run and return stdout as list of lines
@shell.run_json[cmd]        → run command and parse JSON output
@shell.env_or[name; default]→ env var or default value
@shell.has_cmd[name]        → True if command exists on PATH
@shell.shell_type[]         → current shell (bash, zsh, sh, …)
@sys.argv_list[]            → sys.argv[1:] as list (skip script name)
@sys.argv_dict[]            → parse --key=value args to dict
@sys.is_main[]              → __name__ == '__main__'
@sys.frozen[]               → True if running as PyInstaller bundle
@sys.is_64bit[]             → True if Python is 64-bit
@sys.is_windows[]           → True if platform is Windows
@sys.is_linux[]             → True if platform is Linux
@sys.is_mac[]               → True if platform is macOS
@sys.path_add[p]            → append to sys.path (in-place, returns new path)
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@run[":              "@shell.run[",
    "@cmd[":              "@shell.output[",
    "@shell_lines[":      "@shell.lines[",
    "@shell_code[":       "@shell.code[",
    "@shell_ok[":         "@shell.ok[",
    "@bg[":               "@shell.bg[",
    # @pipe is a core Cruhon built-in — use @shell_pipe instead
    "@shell_pipe[":       "@shell.pipe[",
    "@env_get[":          "@shell.env[",
    "@env_set[":          "@shell.env_set[",
    "@env_del[":          "@shell.env_del[",
    "@env_all[":          "@shell.env_all[",
    "@which[":            "@shell.which[",
    "@shell_exists[":     "@shell.exists[",
    "@sh_cwd[":           "@shell.cwd[",
    "@sh_cd[":            "@shell.cd[",
    "@sh_args[":          "@shell.args[",
    "@sh_exit[":          "@shell.exit[",
    "@sh_platform[":      "@shell.platform[",
    "@python_version[":   "@shell.python_version[",
    "@sh_pid[":           "@shell.pid[",
    "@cpu_count[":        "@shell.cpu_count[",
    "@hostname[":         "@shell.hostname[",
    "@sys_argv[":         "@sys.argv[",
    "@sys_exit[":         "@sys.exit[",
    "@sys_path[":         "@sys.path[",
    "@sys_version[":      "@sys.version[",
    "@sys_platform[":     "@sys.platform[",
    "@sys_maxsize[":      "@sys.maxsize[",
    "@sys_stdin[":        "@sys.stdin[",
    "@sys_stdout[":       "@sys.stdout[",
    "@sys_stderr[":       "@sys.stderr[",
    "@sys_modules[":      "@sys.modules[",
    "@sys_executable[":   "@sys.executable[",
    "@sizeof[":           "@sys.getsizeof[",
    "@recursion_limit[":  "@sys.getrecursionlimit[",
    "@set_recursion[":    "@sys.setrecursionlimit[",
}

METHOD_ALIASES: dict[str, str] = {
    "@shell.cmd[":      "@shell.output[",
    "@shell.exec[":     "@shell.run[",
    "@shell.capture[":  "@shell.output[",
    "@shell.is_ok[":    "@shell.ok[",
    "@shell.get_env[":  "@shell.env[",
    "@sys.ver[":        "@sys.version[",
    "@sys.py_ver[":     "@sys.version_info[",
    "@sys.size[":       "@sys.getsizeof[",
}

_SP  = "__import__('subprocess')"
_SY  = "__import__('sys')"
_OS  = "__import__('os')"
_SHU = "__import__('shutil')"
_JSON = "__import__('json')"


def _new_lib_calls(api) -> None:

    api.lib_call("shell", "run_capture", lambda a: (
        f"(lambda _r: (_r.stdout.strip(), _r.stderr.strip()))"
        f"({_SP}.run({a[0]}, shell=True, capture_output=True, text=True))"
        if a else
        f"('', '')"
    ))

    api.lib_call("shell", "run_lines", lambda a: (
        f"{_SP}.run({a[0]}, shell=True, capture_output=True, text=True)"
        f".stdout.splitlines()"
        if a else
        f"[]"
    ))

    api.lib_call("shell", "run_json", lambda a: (
        f"{_JSON}.loads("
        f"{_SP}.run({a[0]}, shell=True, capture_output=True, text=True).stdout)"
        if a else
        f"None"
    ))

    api.lib_call("shell", "env_or", lambda a: (
        f"{_OS}.environ.get({a[0]}, {a[1]})"
        if len(a) > 1 else
        f"{_OS}.environ.get({a[0]}, '')"
    ))

    api.lib_call("shell", "has_cmd", lambda a: (
        f"({_SHU}.which({a[0]}) is not None)"
        if a else
        f"False"
    ))

    api.lib_call("shell", "shell_type", lambda a: (
        f"{_OS}.environ.get('SHELL', {_OS}.environ.get('COMSPEC', 'unknown')).split('/')[-1]"
    ))

    api.lib_call("sys", "argv_list", lambda a: (
        f"{_SY}.argv[1:]"
    ))

    api.lib_call("sys", "argv_dict", lambda a: (
        f"{{_k.lstrip('-'): _v for _a in {_SY}.argv[1:] "
        f"for _k, _, _v in [_a.partition('=')] if '=' in _a}}"
    ))

    api.lib_call("sys", "is_main", lambda a: (
        f"(__name__ == '__main__')"
    ))

    api.lib_call("sys", "frozen", lambda a: (
        f"getattr({_SY}, 'frozen', False)"
    ))

    api.lib_call("sys", "is_64bit", lambda a: (
        f"({_SY}.maxsize > 2**32)"
    ))

    api.lib_call("sys", "is_windows", lambda a: (
        f"({_SY}.platform == 'win32')"
    ))

    api.lib_call("sys", "is_linux", lambda a: (
        f"({_SY}.platform.startswith('linux'))"
    ))

    api.lib_call("sys", "is_mac", lambda a: (
        f"({_SY}.platform == 'darwin')"
    ))

    api.lib_call("sys", "path_add", lambda a: (
        f"(lambda _p: ({_SY}.path.append(_p), {_SY}.path)[1])({a[0]})"
        if a else
        f"{_SY}.path"
    ))

    api.lib_call("sys", "arg", lambda a: (
        f"({_SY}.argv[int({a[0]})] if int({a[0]}) < len({_SY}.argv) else '')"
        if a else
        f"({_SY}.argv[1] if len({_SY}.argv) > 1 else '')"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
