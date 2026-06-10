"""
Config stdlib wrappers for Cruhon — @config.*

Covers configparser / tomllib / json / os.environ so a non-coder can
read and write config files and environment variables with one-liners,
without knowing which module to use — @config.load detects the format
from the file extension automatically.

━━━ LOAD / SAVE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @config.load[path]               → dict  (.json / .toml / .ini / .cfg / .env)
  @config.save[path; data]         — write dict to file (json or ini)
  @config.reload[path]             → re-read and return updated dict

━━━ GET / SET ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @config.get[path; key]           → value (top-level key for json/toml)
  @config.get[path; section; key]  → value from section (ini)
  @config.set[path; key; value]    — update key and save (json only)
  @config.set[path; section; key; value] — update section.key and save (ini)

━━━ SECTIONS / KEYS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @config.sections[path]           → list of section names (.ini)
  @config.keys[path]               → top-level keys (.json/.toml)
  @config.keys[path; section]      → keys in section (.ini)
  @config.has[path; key]           → bool

━━━ ENVIRONMENT VARIABLES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @config.env[key]                 → os.environ.get(key)  or  None
  @config.env[key; default]        → os.environ.get(key, default)
  @config.env_set[key; value]      — set environment variable
  @config.env_del[key]             — delete environment variable
  @config.env_all[]                → dict copy of os.environ
  @config.dotenv[path]             — load .env file into os.environ
"""
from ..registry import register_lib, register_lib_call

_MOD = "cruhon.core.libs.config_"


# ── Runtime helpers (called from generated code) ─────────────────────────────

def _load(path: str) -> dict:
    import os, json
    basename = os.path.basename(str(path)).lower()
    ext = os.path.splitext(basename)[1].lower()
    if basename == ".env" or basename.startswith(".env."):
        return _load_dotenv_as_dict(path)
    if ext == ".json":
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    if ext == ".toml":
        try:
            import tomllib
            with open(path, "rb") as f:
                return tomllib.load(f)
        except ImportError:
            try:
                import tomli  # type: ignore
                with open(path, "rb") as f:
                    return tomli.load(f)
            except ImportError:
                raise ImportError("[cruhon-config] TOML support requires Python 3.11+ or 'pip install tomli'")
    if ext in (".ini", ".cfg"):
        import configparser
        cp = configparser.ConfigParser()
        cp.read(path, encoding="utf-8")
        return {s: dict(cp[s]) for s in cp.sections()}
    if ext == ".env":
        return _load_dotenv_as_dict(path)
    # Unknown extension — try JSON first
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_dotenv_as_dict(path: str) -> dict:
    result = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip().strip('"').strip("'")
    return result


def _save(path: str, data: dict):
    import os, json
    ext = os.path.splitext(str(path))[1].lower()
    if ext == ".json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    elif ext in (".ini", ".cfg"):
        import configparser
        cp = configparser.ConfigParser()
        for section, values in data.items():
            cp[section] = {str(k): str(v) for k, v in values.items()} \
                if isinstance(values, dict) else {}
        with open(path, "w", encoding="utf-8") as f:
            cp.write(f)
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def _cfg_get(path: str, *keys):
    data = _load(path)
    if len(keys) == 1:
        return data.get(keys[0])
    # section + key
    section = data.get(keys[0], {})
    return section.get(keys[1]) if isinstance(section, dict) else None


def _cfg_set(path: str, *args):
    data = _load(path)
    if len(args) == 2:          # key, value
        data[args[0]] = args[1]
    elif len(args) == 3:        # section, key, value
        if args[0] not in data:
            data[args[0]] = {}
        data[args[0]][args[1]] = args[2]
    _save(path, data)


def _dotenv(path: str):
    import os
    for k, v in _load_dotenv_as_dict(path).items():
        os.environ[k] = v


def _ref(fn: str) -> str:
    return f"__import__({_MOD!r}, fromlist=[{fn!r}]).{fn}"


def register():
    register_lib("config", None)

    # ── LOAD / SAVE ──────────────────────────────────────────
    register_lib_call("config", "load",
        lambda a: f"{_ref('_load')}({a[0]})")

    register_lib_call("config", "save",
        lambda a: f"{_ref('_save')}({a[0]}, {a[1]})")

    register_lib_call("config", "reload",
        lambda a: f"{_ref('_load')}({a[0]})")

    # ── GET / SET ────────────────────────────────────────────
    register_lib_call("config", "get",
        lambda a: f"{_ref('_cfg_get')}({', '.join(a)})")

    register_lib_call("config", "set",
        lambda a: f"{_ref('_cfg_set')}({', '.join(a)})")

    # ── SECTIONS / KEYS ──────────────────────────────────────
    register_lib_call("config", "sections",
        lambda a: f"list({_ref('_load')}({a[0]}).keys())")

    register_lib_call("config", "keys",
        lambda a: (
            f"list({_ref('_load')}({a[0]}).get({a[1]}, {{}}).keys())" if len(a) > 1 else
            f"list({_ref('_load')}({a[0]}).keys())"
        ))

    register_lib_call("config", "has",
        lambda a: f"({a[1]} in {_ref('_load')}({a[0]}))")

    # ── ENVIRONMENT VARIABLES ────────────────────────────────
    register_lib_call("config", "env",
        lambda a: (
            f"__import__('os').environ.get({a[0]}, {a[1]})" if len(a) > 1 else
            f"__import__('os').environ.get({a[0]})"
        ))

    register_lib_call("config", "env_set",
        lambda a: f"__import__('os').environ.__setitem__({a[0]}, str({a[1]}))")

    register_lib_call("config", "env_del",
        lambda a: f"__import__('os').environ.pop({a[0]}, None)")

    register_lib_call("config", "env_all",
        lambda a: "dict(__import__('os').environ)")

    register_lib_call("config", "dotenv",
        lambda a: f"{_ref('_dotenv')}({a[0]})")
