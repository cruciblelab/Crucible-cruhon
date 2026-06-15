"""
cruhon/core/libs/env_.py
========================
Environment variables and secrets for Cruhon — @env.*

A single, safe surface for configuration: read typed values, require that
critical variables exist, auto-load `.env` files, expand `$VAR` references,
and mask secrets so tokens never leak into logs or a panel.

━━━ READ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @env.get[key]                   → value or None
  @env.get[key; default]          → value or default
  @env.require[key]               → value, or raise if missing/empty
  @env.has[key]                   → True if set (and non-empty)
  @env.all[]                      → dict of every environment variable
  @env.prefix[prefix]             → dict of vars whose name starts with prefix

━━━ TYPED ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @env.int[key]                   → int, or None
  @env.int[key; default]          → int, or default
  @env.float[key]                 → float, or None / default
  @env.bool[key]                  → True for 1/true/yes/on (case-insensitive)
  @env.bool[key; default]         → … with a fallback when unset
  @env.list[key]                  → comma-separated value → list of strings
  @env.list[key; sep]             → split on a custom separator
  @env.json[key]                  → parse the value as JSON

━━━ WRITE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @env.set[key; value]            → set a variable (returns the value)
  @env.unset[key]                 → remove a variable (safe if absent)
  @env.setdefault[key; value]     → set only if not already present

━━━ .env FILES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @env.load[]                     → load ./.env into the environment → dict
  @env.load[path]                 → load a specific .env file
  @env.load[path; override]       → override existing vars when override=True
  @env.parse[path]                → read a .env file into a dict (no side effects)
  @env.save[path; mapping]        → write a dict out as a .env file

━━━ SECRETS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @env.mask[value]                → "abcd••••••wxyz" — safe to print/log
  @env.mask[value; show]          → keep `show` chars at each end
  @env.expand[text]               → expand $VAR and ${VAR} inside a string
"""
from ..registry import register_lib, register_lib_call

_OS = "__import__('os')"
_SELF = "__import__('cruhon.core.libs.env_', fromlist=['_x'])"

_TRUE = {"1", "true", "yes", "on", "y", "t"}


# ── Helper functions (referenced from generated code via _SELF) ──────────

def _parse_dotenv(path):
    """Parse a .env file into a dict. Tolerant: skips blanks/comments,
    strips surrounding quotes, supports `export KEY=val`."""
    import os
    data = {}
    if not os.path.exists(path):
        return data
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].lstrip()
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
                val = val[1:-1]
            if key:
                data[key] = val
    return data


def _load(path=".env", override=False):
    """Load a .env file into os.environ and return the dict that was loaded."""
    import os
    data = _parse_dotenv(path)
    for key, val in data.items():
        if override or key not in os.environ:
            os.environ[key] = val
    return data


def _save(path, mapping):
    """Write a mapping out as a .env file. Values with spaces/# are quoted."""
    lines = []
    for key, val in mapping.items():
        sval = str(val)
        if sval == "" or any(c in sval for c in (" ", "#", "\t", "\n")):
            sval = '"' + sval.replace('"', '\\"') + '"'
        lines.append(f"{key}={sval}")
    text = "\n".join(lines) + ("\n" if lines else "")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def _to_bool(val, default=False):
    if val is None:
        return default
    return str(val).strip().lower() in _TRUE


def _mask(value, show=2):
    """Mask a secret: keep `show` chars at each end, bullet the middle."""
    if value is None:
        return None
    s = str(value)
    if len(s) <= show * 2:
        return "•" * len(s)
    return s[:show] + "•" * max(4, len(s) - show * 2) + s[-show:]


def _expand(text):
    """Expand $VAR and ${VAR} using the current environment."""
    import os
    return os.path.expandvars(str(text))


def register():
    register_lib("env", None)

    # ── Read ──────────────────────────────────────────────────
    register_lib_call("env", "get",
        lambda a: (
            f"{_OS}.environ.get({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_OS}.environ.get({a[0]})"
        ))
    register_lib_call("env", "require",
        lambda a: (
            f"(lambda _k: {_OS}.environ[_k] if {_OS}.environ.get(_k) "
            f"else (_ for _ in ()).throw("
            f"RuntimeError('[env] required variable ' + _k + ' is not set')))({a[0]})"
        ))
    register_lib_call("env", "has",
        lambda a: f"bool({_OS}.environ.get({a[0]}))")
    register_lib_call("env", "all",
        lambda a: f"dict({_OS}.environ)")
    register_lib_call("env", "prefix",
        lambda a: (
            f"(lambda _p: {{_k: _v for _k, _v in {_OS}.environ.items() "
            f"if _k.startswith(_p)}})({a[0]})"
        ))

    # ── Typed ─────────────────────────────────────────────────
    register_lib_call("env", "int",
        lambda a: (
            f"(lambda _v: int(_v) if _v not in (None, '') else {a[1]})"
            f"({_OS}.environ.get({a[0]}))" if len(a) > 1 else
            f"(lambda _v: int(_v) if _v not in (None, '') else None)"
            f"({_OS}.environ.get({a[0]}))"
        ))
    register_lib_call("env", "float",
        lambda a: (
            f"(lambda _v: float(_v) if _v not in (None, '') else {a[1]})"
            f"({_OS}.environ.get({a[0]}))" if len(a) > 1 else
            f"(lambda _v: float(_v) if _v not in (None, '') else None)"
            f"({_OS}.environ.get({a[0]}))"
        ))
    register_lib_call("env", "bool",
        lambda a: (
            f"{_SELF}._to_bool({_OS}.environ.get({a[0]}), {a[1]})" if len(a) > 1 else
            f"{_SELF}._to_bool({_OS}.environ.get({a[0]}))"
        ))
    register_lib_call("env", "list",
        lambda a: (
            f"(lambda _v: _v.split({a[1]}) if _v else [])({_OS}.environ.get({a[0]}, ''))"
            if len(a) > 1 else
            f"(lambda _v: _v.split(',') if _v else [])({_OS}.environ.get({a[0]}, ''))"
        ))
    register_lib_call("env", "json",
        lambda a: f"__import__('json').loads({_OS}.environ[{a[0]}])")

    # ── Write ─────────────────────────────────────────────────
    register_lib_call("env", "set",
        lambda a: (
            f"(lambda _k, _v: ({_OS}.environ.__setitem__(_k, str(_v)), _v)[1])"
            f"({a[0]}, {a[1]})"
        ))
    register_lib_call("env", "unset",
        lambda a: f"{_OS}.environ.pop({a[0]}, None)")
    register_lib_call("env", "setdefault",
        lambda a: f"{_OS}.environ.setdefault({a[0]}, str({a[1]}))")

    # ── .env files ────────────────────────────────────────────
    register_lib_call("env", "load",
        lambda a: (
            f"{_SELF}._load({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_SELF}._load({a[0]})" if len(a) == 1 else
            f"{_SELF}._load()"
        ))
    register_lib_call("env", "parse",
        lambda a: f"{_SELF}._parse_dotenv({a[0]})")
    register_lib_call("env", "save",
        lambda a: f"{_SELF}._save({a[0]}, {a[1]})")

    # ── Secrets ───────────────────────────────────────────────
    register_lib_call("env", "mask",
        lambda a: (
            f"{_SELF}._mask({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_SELF}._mask({a[0]})"
        ))
    register_lib_call("env", "expand",
        lambda a: f"{_SELF}._expand({a[0]})")
