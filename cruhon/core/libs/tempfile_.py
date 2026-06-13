"""
cruhon/core/libs/tempfile_.py
=============================
Tempfile wrappers for Cruhon — @tempfile.*

All helpers return paths (strings), not file handles. Files are created but
not deleted automatically unless you delete them yourself.

━━━ TEMP FILES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @tempfile.file[]                → path to a new temp file
  @tempfile.file[suffix]
  @tempfile.file[suffix; prefix]
  @tempfile.file[suffix; prefix; dir]
  @tempfile.named[suffix]         → same as file[suffix] — explicit naming
  @tempfile.in_dir[dir]           → temp file inside a given directory
  @tempfile.mkstemp[]             → (fd, path) — low-level, you close fd
  @tempfile.mkstemp[suffix]

━━━ TEMP DIRS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @tempfile.dir[]                 → path to a new temp directory
  @tempfile.dir[prefix]
  @tempfile.dir[suffix]
  @tempfile.dir[prefix; suffix]
  @tempfile.in_dir_dir[dir]       → temp sub-directory inside a given directory

━━━ INFO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @tempfile.gettempdir[]          → system temp directory path
"""
from ..registry import register_lib, register_lib_call

_TF = "__import__('tempfile')"


def register():
    register_lib("tempfile", None)

    # ── Temp files ────────────────────────────────────────────
    register_lib_call("tempfile", "file",
        lambda a: (
            f"(lambda _s, _p, _d: {_TF}.NamedTemporaryFile(suffix=_s, prefix=_p, dir=_d, delete=False).name)({a[0]}, {a[1]}, {a[2]})"
            if len(a) > 2 else
            f"(lambda _s, _p: {_TF}.NamedTemporaryFile(suffix=_s, prefix=_p, delete=False).name)({a[0]}, {a[1]})"
            if len(a) > 1 else
            f"(lambda _s: {_TF}.NamedTemporaryFile(suffix=_s, delete=False).name)({a[0]})"
            if len(a) > 0 else
            f"{_TF}.NamedTemporaryFile(delete=False).name"
        ))

    register_lib_call("tempfile", "named",
        lambda a: (
            f"{_TF}.NamedTemporaryFile(suffix={a[0]}, delete=False).name"
            if len(a) > 0 else
            f"{_TF}.NamedTemporaryFile(delete=False).name"
        ))

    register_lib_call("tempfile", "in_dir",
        lambda a: f"{_TF}.NamedTemporaryFile(dir={a[0]}, delete=False).name")

    register_lib_call("tempfile", "mkstemp",
        lambda a: (
            f"{_TF}.mkstemp(suffix={a[0]})"
            if len(a) > 0 else
            f"{_TF}.mkstemp()"
        ))

    # ── Temp dirs ─────────────────────────────────────────────
    register_lib_call("tempfile", "dir",
        lambda a: (
            f"(lambda _p, _s: {_TF}.mkdtemp(prefix=_p, suffix=_s))({a[0]}, {a[1]})"
            if len(a) > 1 else
            f"{_TF}.mkdtemp(prefix={a[0]})"
            if len(a) > 0 else
            f"{_TF}.mkdtemp()"
        ))

    register_lib_call("tempfile", "in_dir_dir",
        lambda a: f"{_TF}.mkdtemp(dir={a[0]})")

    # ── Info ──────────────────────────────────────────────────
    register_lib_call("tempfile", "gettempdir",
        lambda a: f"{_TF}.gettempdir()")
