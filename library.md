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

### Python stdlib wrappers (new in v2.1)

One-line access to the most-used Python standard libraries. No `@import` needed.

| Namespace        | Wraps          | Commands |
|------------------|----------------|----------|
| `@random.*`      | `random`       | random, randint, randrange, uniform, choice, choices, sample, shuffle, seed, gauss… |
| `@collections.*` | `collections`  | Counter, defaultdict, deque, namedtuple, OrderedDict, ChainMap… |
| `@itertools.*`   | `itertools`    | chain, cycle, product, permutations, combinations, groupby, accumulate, islice, flatten, pairwise… |
| `@functools.*`   | `functools`    | reduce, partial, lru_cache, cache, cached_property, wraps, total_ordering, singledispatch… |
| `@sys.*`         | `sys`          | argv, exit, path, version, platform, getsizeof, maxsize, stdin/out/err… |
| `@io.*`          | `io`           | StringIO, BytesIO, read, write, getvalue, seek, tell, open… |
| `@copy.*`        | `copy`         | copy, deepcopy, replace |
| `@base64.*`      | `base64`       | encode, decode, urlsafe_encode, urlsafe_decode, b32/b16… |
| `@url.*`         | `urllib.parse` | parse, join, quote, unquote, encode, parse_qs, scheme, netloc, path, query… |
| `@statistics.*`  | `statistics`   | mean, fmean, median, mode, multimode, quantiles, stdev, variance, correlation… |
| `@contextlib.*`  | `contextlib`   | contextmanager, suppress, nullcontext, redirect_stdout, closing, ExitStack… |
| `@enum.*`        | `enum`         | Enum, IntEnum, StrEnum, Flag, auto, create, unique, names, values… |
| `@dataclasses.*` | `dataclasses`  | dataclass, field, asdict, astuple, fields, replace, is_dataclass, make_dataclass… |
| `@typing.*`      | `typing`       | Optional, Union, List, Dict, Tuple, Any, Callable, cast, TypeVar, Literal… |
| `@threading.*`   | `threading`    | Thread, Lock, RLock, Event, Semaphore, Condition, Barrier, Timer, current_thread… |
| `@queue.*`       | `queue`        | Queue, LifoQueue, PriorityQueue, SimpleQueue, put, get, empty, full, qsize… |
| `@heapq.*`       | `heapq`        | heappush, heappop, heapify, heappushpop, heapreplace, nlargest, nsmallest, merge |
| `@bisect.*`      | `bisect`       | bisect_left, bisect_right, bisect, insort_left, insort_right, insort |
| `@operator.*`    | `operator`     | itemgetter, attrgetter, methodcaller, add, sub, mul, eq, lt, contains… |
| `@pprint.*`      | `pprint`       | print, format, pp, isreadable, isrecursive, saferepr, PrettyPrinter |

### More stdlib wrappers (new in v2.2)

Backing namespaces for the `cruhon-shortcuts` plugin. No `@import` needed.

| Namespace        | Wraps          | Commands |
|------------------|----------------|----------|
| `@string.*`      | `string`       | ascii_letters, ascii_lowercase, digits, punctuation, whitespace, printable, template, substitute, safe_substitute, capwords |
| `@struct.*`      | `struct`       | pack, unpack, pack_into, unpack_from, iter_unpack, calcsize, compile |
| `@zlib.*`        | `zlib`         | compress, decompress, decompress_text, crc32, crc32_hex, adler32, compressor, decompressor, ratio |
| `@calendar.*`    | `calendar`     | is_leap, leap_days, month_range, days_in_month, weekday, month_name, month_abbr, day_name, day_abbr, month_dates, month_text, weekheader, timegm |
| `@email.*`       | `email`        | message, make, set_content, add_html, set_header, attach_file, parse, parse_bytes, subject, sender, recipients, header, headers, body, is_multipart, parts, as_string, parse_address, format_address, valid_address |

### Plugin namespaces

| Namespace   | Type    | Commands |
|-------------|---------|----------|
| `@db.*`     | plugin  | 138 commands — see `mods/cruhon-db` |
| `@discord.*`| plugin  | ~60 commands — see `mods/cruhon-discord` |

### Shortcut plugin (`cruhon-shortcuts`)

A fully configurable shortcut layer over **every** namespace. It does not add
a namespace of its own — instead it installs:

- **Global aliases** — `@read` → `@file.read`, `@now` → `@date.now`,
  `@uuid` → `@crypto.uuid`, `@rand` → `@random.randint`, `@mean` →
  `@statistics.mean`, and hundreds more.
- **Method aliases** — `@file.cat`, `@file.ls`, `@date.ts`, `@http.fetch`, …
- **200+ new convenience methods** — `@file.head`, `@file.tail`, `@file.grep`,
  `@date.tomorrow`, `@date.age`, `@random.password`, `@statistics.summary`,
  `@collections.histogram`, `@string.random`, `@struct.hexdump`, …

Everything is toggleable from `mods/cruhon-shortcuts/mod.json`:

```json
{
  "groups": "all",
  "global_aliases": true,
  "method_aliases": true,
  "disabled": ["@get[", "@post["],
  "custom": { "@slurp[": "@file.read[" }
}
```

`groups` accepts `"all"` or any subset of: `file`, `http`, `date`, `text`,
`math`, `crypto`, `collections`, `system`, `data`, `stdlib`, `types`, `io`,
`binary`. See `mods/cruhon-shortcuts/` for the full per-group command list.

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

---

## Community

- **Discord:** https://discord.gg/SPf5VZ6QPG
- **Email:** cruciblelab@hotmail.com
