"""
cruhon/core/libs/zipapp_.py
===========================
ZIP application archives for Cruhon — @zipapp.*

Create self-contained, runnable Python ZIP archives (.pyz files) that can
be executed with `python app.pyz` directly.

━━━ CREATE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @zipapp.create[source; target]           → create archive from directory
  @zipapp.create[source; target; main]     → with __main__ entry point
  @zipapp.create[source; target; main; py] → with specific interpreter path

━━━ INSPECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @zipapp.interpreter[path]       → get interpreter shebang from archive
  @zipapp.main[path]              → get __main__ module from archive
  @zipapp.is_archive[path]        → True if path is a valid ZIP archive

━━━ COPY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @zipapp.copy[source; target]    → copy archive, optionally change interpreter
  @zipapp.copy[source; target; py] → copy and set new interpreter
"""
from ..registry import register_lib, register_lib_call

_ZA = "__import__('zipapp')"


def register():
    register_lib("zipapp", None)

    # ── Create ─────────────────────────────────────────────────
    register_lib_call("zipapp", "create",
        lambda a: (
            f"{_ZA}.create_archive({a[0]}, {a[1]}, interpreter={a[3]}, main={a[2]})" if len(a) > 3 else
            f"{_ZA}.create_archive({a[0]}, {a[1]}, main={a[2]})" if len(a) > 2 else
            f"{_ZA}.create_archive({a[0]}, {a[1]})"
        ))

    # ── Inspect ───────────────────────────────────────────────
    register_lib_call("zipapp", "interpreter",
        lambda a: f"{_ZA}.get_interpreter({a[0]})")
    register_lib_call("zipapp", "main",
        lambda a: (
            f"(lambda _p: __import__('zipfile').ZipFile(_p).read('__main__.py').decode())({a[0]})"
        ))
    register_lib_call("zipapp", "is_archive",
        lambda a: f"__import__('zipfile').is_zipfile({a[0]})")

    # ── Copy ──────────────────────────────────────────────────
    register_lib_call("zipapp", "copy",
        lambda a: (
            f"{_ZA}.create_archive({a[0]}, {a[1]}, interpreter={a[2]})" if len(a) > 2 else
            f"{_ZA}.create_archive({a[0]}, {a[1]})"
        ))
