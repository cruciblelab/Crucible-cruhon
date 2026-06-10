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

### Core namespaces

| Namespace   | Wraps                                   | Commands |
|-------------|-----------------------------------------|----------|
| `@file.*`   | `pathlib` / `os` / `shutil` / `glob` / `tempfile` | read, write, append, copy, move, glob, mkdir, json, touch, symlink, chmod, stat… |
| `@date.*`   | `datetime` / `time` / `calendar` / `zoneinfo` | now, format, parse, add, diff, weekday, timezone, UTC, ISO calendar… |
| `@text.*`   | `re` / `str` / `textwrap` / `html` | upper, lower, split, replace, regex, encode, decode, slug, partition… |
| `@http.*`   | `requests` / `httpx`                    | get, post, put, delete, upload, auth, async_get, async_post… |
| `@json.*`   | `json`                                  | load, dump |
| `@store.*`  | in-memory key/value                     | set, get, clear |
| `@ctx.*`    | execution context dict                  | set, get, push, pop |

### Extended namespaces (stdlib wrappers)

| Namespace   | Wraps                                   | Commands |
|-------------|-----------------------------------------|----------|
| `@crypto.*` | `hashlib` / `hmac` / `secrets` / `base64` / `uuid` | md5, sha256, hash, pbkdf2, scrypt, hmac, token, uuid, b64_encode… |
| `@log.*`    | `logging`                               | setup, debug, info, warning, error, to_file, get, child… |
| `@config.*` | `configparser` / `json` / `tomllib` / `os.environ` | load, save, get, set, keys, dotenv, env… |
| `@shell.*`  | `subprocess` / `os` / `sys` / `shutil`  | run, output, lines, code, ok, bg, kill, terminate, wait, env… |
| `@archive.*`| `zipfile` / `tarfile` / `gzip` / `bz2` / `lzma` | zip, unzip, tar, untar, gzip, gunzip, bzip2, lzma… |
| `@mail.*`   | `smtplib` / `imaplib` / `email`         | send, send_html, imap_connect, imap_search, imap_fetch… |
| `@csv.*`    | `csv`                                   | read, write, filter, to_json… |

### Plugin namespaces

| Namespace   | Type    | Commands |
|-------------|---------|----------|
| `@db.*`     | plugin  | 138 commands — see `mods/cruhon-db` |
| `@discord.*`| plugin  | ~60 commands — see `mods/cruhon-discord` |

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
