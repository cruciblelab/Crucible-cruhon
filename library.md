# Cruhon Library Support

Cruhon wraps Python libraries with its own syntax.
The user must have the relevant Python library already installed when using `@import[lib]`.

---

## ✅ Any Python standard-library module just works

As of the stdlib passthrough, **`@import[<module>]` accepts any module in the
Python standard library** — no per-module registration needed. The transpiler
checks `sys.stdlib_module_names`, so these all work out of the box:

```clpy
@import[sqlite3]
@import[collections]
@import[hashlib]
@import[csv]
@import[itertools]
@import[subprocess]
@import[uuid]
@import[secrets]
# … every stdlib module
```

Once imported, call into them with plain Python expressions:

```clpy
@import[sqlite3]
@var[conn; sqlite3.connect("data.db")]
@var[rows; conn.execute("SELECT * FROM users").fetchall()]
```

Third-party packages (not in the stdlib) must be registered explicitly — see
the table below and the Contributing section.

---

## ✅ Registered third-party libraries

| Cruhon               | Python          |
|----------------------|-----------------|
| `@import[requests]`  | `requests`      |
| `@import[discord]`   | `discord.py`    |
| `@import[httpx]`     | `httpx`         |

---

## ✨ Helper namespaces (simplified, non-coder friendly)

These are Cruhon-native command sets that wrap stdlib modules with a far
simpler surface. You do **not** need `@import` for them.

| Namespace   | Wraps                                   | Commands |
|-------------|-----------------------------------------|----------|
| `@file.*`   | `pathlib` / `os` / `shutil` / `glob` / `tempfile` | read, write, append, copy, move, glob, mkdir, json … |
| `@date.*`   | `datetime` / `time` / `calendar`        | now, format, parse, add, diff, weekday, make … |
| `@http.*`   | `requests`                              | get, post, put, delete |
| `@json.*`   | `json`                                  | load, dump |
| `@db.*`     | `sqlite3` / `psycopg2` / `pymysql` (+ async) | 138 commands — see `mods/cruhon-db` |
| `@discord.*`| `discord.py`                            | ~60 commands — see `mods/cruhon-discord` |
| `@store.*`  | in-memory key/value                     | set, get, clear |
| `@ctx.*`    | execution context dict                  | set, get, push, pop |

### `@file` quick reference

```clpy
@file.write["notes.txt"; "hello"]      # overwrite (creates parent dirs)
@file.append["notes.txt"; " more"]     # append
@var[text; @file.read["notes.txt"]]    # read full text
@var[rows; @file.lines["notes.txt"]]   # list of lines
@file.copy["a.txt"; "b.txt"]           # copy / move / rename / delete
@var[found; @file.glob["*.txt"]]       # glob, list, walk
@file.write_json["d.json"; {"k": 1}]   # JSON read/write
@var[data; @file.read_json["d.json"]]
```

All path-taking `@file` commands are sandboxed to the working directory —
traversal outside cwd (`../../etc/passwd`) is blocked.

### `@date` quick reference

```clpy
@var[now; @date.now[]]
@var[stamp; @date.format["%Y-%m-%d %H:%M"]]   # format now
@var[when; @date.parse["2024-03-10"; "%Y-%m-%d"]]
@var[future; @date.add[@date.now[]; days=7]]   # arithmetic
@var[gap; @date.diff_days[future; @date.now[]]]
@var[name; @date.weekday_name[@date.now[]]]    # "Monday"
@var[d; @date.make[2024; 1; 15]]               # build a date
```

`@date` commands accept either a datetime object or an ISO string.

---

## ❌ Unsupported Library Error

```
@import[pandas]
# Error: Library 'pandas' is not yet supported in Cruhon.
# See library.md for the full list.
```

This only happens for **third-party** packages that haven't been registered.
Standard-library modules never hit this error.

---

## Contributing

Adding a third-party library wrapper is straightforward:

1. Add `register_lib("libname", "python_module")` to `cruhon/core/registry.py`
2. If needed, customize method calls with `register_lib_call()`
3. Add an entry to this file
4. Open a PR

Libraries can also be added as community mods — see `mods/README.md`
