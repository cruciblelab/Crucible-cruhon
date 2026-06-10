"""
File system stdlib wrappers for Cruhon — @file.*

Covers pathlib / os / shutil / glob / tempfile so that a non-coder can do
every common file operation without touching raw Python.

━━━ READ / WRITE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @file.read[path]                → full text (utf-8)
  @file.read[path; enc]           → full text with encoding
  @file.lines[path]               → list of lines
  @file.bytes[path]               → raw bytes
  @file.write[path; text]         — overwrite (creates parent dirs)
  @file.write[path; text; enc]    — overwrite with encoding
  @file.append[path; text]        — append
  @file.write_bytes[path; data]   — write raw bytes
  @file.read_json[path]           → parsed JSON
  @file.write_json[path; obj]     — pretty JSON dump

━━━ EXISTENCE / TYPE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @file.exists[path]              → bool
  @file.is_file[path]             → bool
  @file.is_dir[path]              → bool
  @file.is_link[path]             → bool (symlink)
  @file.size[path]                → bytes count
  @file.mtime[path]               → last-modified timestamp (float)
  @file.stat[path]                → os.stat_result object

━━━ CREATE / PERMISSIONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @file.touch[path]               — create empty file or update mtime
  @file.chmod[path; mode]         — change permissions (e.g. 0o755)
  @file.symlink[src; dest]        — create symlink
  @file.hardlink[src; dest]       — create hard link

━━━ COPY / MOVE / DELETE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @file.copy[src; dst]            — copy file (metadata preserved)
  @file.copytree[src; dst]        — copy whole directory
  @file.move[src; dst]            — move/rename
  @file.rename[old; new]          — rename
  @file.delete[path]              — remove a file
  @file.rmdir[path]               — remove a directory tree

━━━ DIRECTORIES / LISTING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @file.mkdir[path]               — create dir (parents ok, no error if exists)
  @file.list[dir]                 → names in directory
  @file.glob[pattern]             → matches ("*.txt", "src/**/*.py")
  @file.walk[dir]                 → list of all file paths under dir

━━━ PATH HELPERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @file.join[a; b; ...]           → joined path
  @file.abspath[path]             → absolute path
  @file.realpath[path]            → canonical path (resolve symlinks)
  @file.basename[path]            → file name
  @file.dirname[path]             → parent directory
  @file.ext[path]                 → extension (".txt")
  @file.stem[path]                → name without extension
  @file.cwd[]                     → current working directory
  @file.home[]                    → user home directory
  @file.samefile[a; b]            → bool (same file on disk)
  @file.expanduser[path]          → expand ~ in path

━━━ TEMP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @file.temp[]                    → fresh temp file path
  @file.tempdir[]                 → fresh temp directory path
"""
from ..registry import register_lib, register_lib_call

_MOD = "cruhon.core.libs.file_"


def _vp(path: str) -> str:
    return str(path)


def _vp_call(expr: str) -> str:
    """Return Python code that validates `expr` through _vp at runtime."""
    return f"__import__({_MOD!r}, fromlist=['_vp'])._vp({expr})"


def _mkparents(path_expr: str) -> str:
    """Code that ensures the parent directory of a validated path exists."""
    return (
        f"(lambda _p: (__import__('os').makedirs("
        f"__import__('os').path.dirname(__import__('os').path.abspath(_p)) or '.', "
        f"exist_ok=True), _p)[1])({path_expr})"
    )


def register():
    register_lib("file", "builtins")

    vp = _vp_call

    # ── READ / WRITE ──────────────────────────────────────────
    register_lib_call("file", "read",
        lambda a: (
            f"open({vp(a[0])}, encoding={a[1]}).read()" if len(a) > 1 else
            f"open({vp(a[0])}, encoding='utf-8').read()"
        ))

    register_lib_call("file", "lines",
        lambda a: f"open({vp(a[0])}, encoding='utf-8').read().splitlines()")

    register_lib_call("file", "bytes",
        lambda a: f"open({vp(a[0])}, 'rb').read()")

    register_lib_call("file", "write",
        lambda a: (
            f"open({_mkparents(vp(a[0]))}, 'w', encoding={a[2]}).write({a[1]})" if len(a) > 2 else
            f"open({_mkparents(vp(a[0]))}, 'w', encoding='utf-8').write({a[1]})" if len(a) > 1 else
            f"open({_mkparents(vp(a[0]))}, 'w', encoding='utf-8').close()"
        ))

    register_lib_call("file", "append",
        lambda a: (
            f"open({_mkparents(vp(a[0]))}, 'a', encoding='utf-8').write({a[1]})"
            if len(a) > 1 else
            f"open({_mkparents(vp(a[0]))}, 'a', encoding='utf-8').close()"
        ))

    register_lib_call("file", "write_bytes",
        lambda a: f"open({_mkparents(vp(a[0]))}, 'wb').write({a[1]})")

    register_lib_call("file", "read_json",
        lambda a: f"__import__('json').load(open({vp(a[0])}, encoding='utf-8'))")

    register_lib_call("file", "write_json",
        lambda a: (
            f"__import__('json').dump({a[1]}, "
            f"open({_mkparents(vp(a[0]))}, 'w', encoding='utf-8'), "
            f"indent=2, ensure_ascii=False, default=str)"
        ))

    # ── EXISTENCE / TYPE ──────────────────────────────────────
    register_lib_call("file", "exists",
        lambda a: f"__import__('os').path.exists({vp(a[0])})")

    register_lib_call("file", "is_file",
        lambda a: f"__import__('os').path.isfile({vp(a[0])})")

    register_lib_call("file", "is_dir",
        lambda a: f"__import__('os').path.isdir({vp(a[0])})")

    register_lib_call("file", "size",
        lambda a: f"__import__('os').path.getsize({vp(a[0])})")

    register_lib_call("file", "mtime",
        lambda a: f"__import__('os').path.getmtime({vp(a[0])})")

    # ── COPY / MOVE / DELETE ──────────────────────────────────
    register_lib_call("file", "copy",
        lambda a: f"__import__('shutil').copy2({vp(a[0])}, {_mkparents(vp(a[1]))})")

    register_lib_call("file", "copytree",
        lambda a: f"__import__('shutil').copytree({vp(a[0])}, {vp(a[1])}, dirs_exist_ok=True)")

    register_lib_call("file", "move",
        lambda a: f"__import__('shutil').move({vp(a[0])}, {_mkparents(vp(a[1]))})")

    register_lib_call("file", "rename",
        lambda a: f"__import__('os').rename({vp(a[0])}, {_mkparents(vp(a[1]))})")

    register_lib_call("file", "delete",
        lambda a: f"__import__('os').remove({vp(a[0])})")

    register_lib_call("file", "rmdir",
        lambda a: f"__import__('shutil').rmtree({vp(a[0])}, ignore_errors=True)")

    # ── DIRECTORIES / LISTING ─────────────────────────────────
    register_lib_call("file", "mkdir",
        lambda a: f"__import__('os').makedirs({vp(a[0])}, exist_ok=True)")

    register_lib_call("file", "list",
        lambda a: f"sorted(__import__('os').listdir({vp(a[0])}))" if a
                  else "sorted(__import__('os').listdir('.'))")

    register_lib_call("file", "glob",
        lambda a: f"sorted(__import__('glob').glob({vp(a[0])}, recursive=True))")

    register_lib_call("file", "walk",
        lambda a: (
            f"[__import__('os').path.join(_r, _f) "
            f"for _r, _d, _fs in __import__('os').walk({vp(a[0])}) for _f in _fs]"
        ))

    # ── PATH HELPERS (no _vp — pure string ops, no disk access) ─
    register_lib_call("file", "join",
        lambda a: f"__import__('os').path.join({', '.join(a)})")

    register_lib_call("file", "abspath",
        lambda a: f"__import__('os').path.abspath({a[0]})")

    register_lib_call("file", "basename",
        lambda a: f"__import__('os').path.basename({a[0]})")

    register_lib_call("file", "dirname",
        lambda a: f"__import__('os').path.dirname({a[0]})")

    register_lib_call("file", "ext",
        lambda a: f"__import__('os').path.splitext({a[0]})[1]")

    register_lib_call("file", "stem",
        lambda a: f"__import__('os').path.splitext(__import__('os').path.basename({a[0]}))[0]")

    register_lib_call("file", "cwd",
        lambda a: "__import__('os').getcwd()")

    register_lib_call("file", "home",
        lambda a: "__import__('os').path.expanduser('~')")

    # ── TEMP ──────────────────────────────────────────────────
    register_lib_call("file", "temp",
        lambda a: "__import__('tempfile').mkstemp()[1]")

    register_lib_call("file", "tempdir",
        lambda a: "__import__('tempfile').mkdtemp()")

    # ── CREATE / PERMISSIONS ──────────────────────────────────
    register_lib_call("file", "touch",
        lambda a: f"__import__('pathlib').Path({vp(a[0])}).touch()")

    register_lib_call("file", "chmod",
        lambda a: f"__import__('os').chmod({vp(a[0])}, {a[1]})")

    register_lib_call("file", "symlink",
        lambda a: f"__import__('os').symlink({vp(a[0])}, {vp(a[1])})")

    register_lib_call("file", "hardlink",
        lambda a: f"__import__('os').link({vp(a[0])}, {vp(a[1])})")

    register_lib_call("file", "is_link",
        lambda a: f"__import__('os').path.islink({vp(a[0])})")

    register_lib_call("file", "stat",
        lambda a: f"__import__('os').stat({vp(a[0])})")

    # ── EXTRA PATH HELPERS ────────────────────────────────────
    register_lib_call("file", "realpath",
        lambda a: f"__import__('os').path.realpath({a[0]})")

    register_lib_call("file", "samefile",
        lambda a: f"__import__('os').path.samefile({vp(a[0])}, {vp(a[1])})")

    register_lib_call("file", "expanduser",
        lambda a: f"__import__('os').path.expanduser({a[0]})")
