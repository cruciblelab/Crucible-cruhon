# Cruhon

**A modern, extensible scripting language built on Python.**  
By [CrucibleLab](https://github.com/cruciblelab) · `.clpy` files · MIT License · **v2.10.2**

---

## What is Cruhon?

Cruhon is a scripting language that compiles to Python. It replaces Python's
indented block syntax with a uniform `@command[args]` syntax, making scripts
easier to read and write — especially for automation, tooling, and data tasks.

Every Cruhon program is valid Python under the hood. You can always inspect
the generated Python with `cruhon run --show-python`.

The plugin system lets you extend everything: new commands, new block types,
new value syntax, new runtime objects — all without touching the core.

**128 stdlib namespaces · 1880+ built-in commands · 6169 tests**

---

## Install

```bash
pip install cruhon
```

**Requirements:** Python 3.10+

---

## Quick Start

```clpy
# hello.clpy
@var[name; "Cruhon"]
@print[Hello from {name}!]

@func[add; a; b]
    @return[a + b]
@end

@var[result; add(5, 3)]
@print[5 + 3 = {result}]

@for[i; range(3)]
    @print[i = {i}]
@end
```

```bash
cruhon run hello.clpy
```

---

## CLI

| Command | Description |
|---|---|
| `cruhon run file.clpy` | Run a script |
| `cruhon run file.clpy --show-python` | Show generated Python before running |
| `cruhon run file.clpy --watch` | Re-run automatically when `.clpy` files change |
| `cruhon run file.clpy --log cruhon.log [--log-level DEBUG]` | Write diagnostics to a log file |
| `cruhon repl` | Start an interactive session (`:help`, `:vars`, `:history`, `:load`, `:type`, `:clear`, `:quit`) |
| `cruhon docs` | List plugins that ship a command reference |
| `cruhon fmt file.clpy` | Normalize indentation (writes the file) |
| `cruhon fmt file.clpy --check` | Exit non-zero if not formatted (CI-friendly) |
| `cruhon fmt file.clpy --stdout` | Print formatted result without writing |
| `cruhon build file.clpy` | Compile `.clpy` → `.py` |
| `cruhon build file.clpy -o out.py` | Compile to a specific output file |
| `cruhon check file.clpy` | Check for syntax errors without running |
| `cruhon new myproject` | Create a new project scaffold |
| `cruhon new --plugin myplugin` | Create a plugin scaffold in `mods/myplugin/` |
| `cruhon libs` | List all supported libraries |
| `cruhon mods` | Show loaded plugins, APIs, block commands, overrides |
| `cruhon cache` | Show transpile cache stats |
| `cruhon cache --clear` | Clear the transpile cache |
| `cruhon --version` | Show version |

---

## Language Reference

### Syntax Rules

Every statement starts with `@`. Arguments go inside `[...]`, separated by `;`.
Blocks are opened by a command and closed by `@end`.

```
@command[arg1; arg2; key=value]

@block[args]
    # body
@end
```

### Variables and Constants

```clpy
@var[x; 42]              # x = 42
@var[name; "Alice"]      # name = "Alice"
@var[msg; Hello world]   # msg = "Hello world"  (bare text → string)
@var[copy; name]         # copy = name          (identifier → variable reference)
@const[MAX; 100]         # MAX = 100  # const (convention: uppercase)
```

Named parameters work everywhere:

```clpy
@http.post["https://api.example.com/ban"; reason="spam"; days=7]
```

### Type Annotations

Type annotations are first-class — no `@raw` required:

```clpy
@var[score: float; 0.0]
@const[LIMIT: int; 100]
@type[Matrix; list[list[float]]]

@dataclass[Point]
    x: float = 0.0
    y: float = 0.0
@end

@func[distance; p: Point; q: Point; return=float]
    @return[((p.x - q.x)**2 + (p.y - q.y)**2) ** 0.5]
@end
```

| Syntax | Emits |
|---|---|
| `@var[x: int; 42]` | `x: int = 42` |
| `@var[x: int]` | `x: int` (annotation-only) |
| `@const[LIMIT: int; 100]` | `LIMIT: int = 100  # const` |
| `@func[f; a: int; b: str; return=bool]` | `def f(a: int, b: str) -> bool:` |
| `@type[Vector; list[float]]` | `Vector = list[float]  # type alias` |
| `@dataclass[Point] ... @end` | `@dataclass` decorated class block |

### Output and Input

```clpy
@print[Hello, World!]         # print("Hello, World!")
@print[Value is {x}]          # print(f"Value is {x}")
@var[line; @input[Enter: ]]   # line = input("Enter: ")
```

### String Interpolation

Use `{varname}` inside any value to embed a variable:

```clpy
@var[name; "Alice"]
@print[Hello, {name}!]         # f"Hello, {name}!"
@var[msg; "Hi, {name}!"]       # f"Hi, {name}!"
@var[info; age={user.age}]     # f"age={user.age}"
```

> **Limitation:** `@command[...]` cannot be embedded *inside* another
> nested Python expression — not inside `{}` interpolation
> (`@print[{@db.dsn_safe[]}]` ✗), and not inside a list comprehension or
> other bracketed sub-expression (`[f.name for f in @dataclasses.fields[p]]` ✗).
> Bind the inline call to a variable first, then use the variable —
> this always works and is the idiomatic pattern throughout this doc:
> ```clpy
> @var[safe; @db.dsn_safe[]]
> @print[Connected to {safe}]
> @var[fields; @dataclasses.fields[p]]
> @var[names; [f.name for f in fields]]
> ```

### Control Flow

```clpy
@if[x > 0]
    @print[positive]
@elif[x == 0]
    @print[zero]
@else
    @print[negative]
@end

@for[i; range(10)]
    @print[{i}]
@end

@while[x > 0]
    @var[x; x - 1]
@end

@repeat[5]
    @print[hello]
@end

@for[i; range(10)]
    @if[i == 5]
        @break
    @end
    @if[i % 2 == 0]
        @continue
    @end
    @print[{i}]
@end
```

### Pattern Matching (Python 3.10+)

```clpy
@match[status]
    @case[200]
        @print[OK]
    @case[404]
        @print[Not Found]
    @default
        @print[Unknown status]
@end

@match[command.split()]
    @case[["quit"]]
        @print[Quitting]
    @case[["go", direction]]
        @print[Going {direction}]
    @default
        @print[Unknown command]
@end
```

> Case patterns are raw Python match-pattern syntax passed straight through
> — use a real comma `,` for structural list/tuple patterns like
> `["go", direction]`, not Cruhon's `;` argument separator.

### Functions

```clpy
@func[greet; name]
    @print[Hello, {name}!]
    @return[name]
@end

greet("Bob")   # call with Python syntax
```

Async functions:

```clpy
@async[main]
    @var[res; @http.async_get["https://example.com"]]
    @var[data; @http.json[res]]
    @print[Got {len(data)} bytes]
@end

@asyncio.run[main()]
```

Async for and async with:

```clpy
@async[main]
    @async.for[item; async_generator()]
        @print[{item}]
    @end

    @async.with[aiofiles.open("file.txt") as f]
        @var[content; await f.read()]
        @print[{content}]
    @end
@end
```

### Classes

```clpy
@class[Animal]
    @func[__init__; self; name]
        @var[self.name; name]
    @end
@end

@class[Dog; Animal]
    @func[speak; self]
        @print[Woof! I am {self.name}]
    @end
@end

@var[dog; Dog("Rex")]
dog.speak()
```

Multiple inheritance:

```clpy
@class[Cat; Animal; Serializable; JsonMixin]
    ...
@end
```

### Error Handling

```clpy
@try
    @var[x; int("bad")]
@catch[e]
    @print[Error: {e}]
@else
    @print[no error]
@finally
    @print[done]
@end

@raise[ValueError; "invalid input"]

@try
    risky_call()
@catch[e]
    @raise
@end
```

Retry and timeout:

```clpy
@retry[3]
    risky_api_call()
@end

@retry[5; requests.ConnectionError]
    risky_api_call()
@end

@timeout[30]
    slow_operation()
@end
```

### Context Managers

```clpy
@with[open("data.txt") as f]
    @var[content; f.read()]
    @print[{content}]
@end

@with[lock]
    do_work()
@end
```

### Templates and Pipelines

```clpy
@template[greeting]
    Hello, {name}! You have {count} messages.
@end

@var[msg; @render[greeting; name="Alice"; count=5]]
@print[{msg}]

@pipeline[normalize; str.strip; str.lower]
@var[result; @apply[normalize; "  Hello  "]]   # "hello"
```

### Multi-variable assignment and spread

```clpy
@let[x; 10; y; 20; z; 30]

@var[n; @spread[max; [3, 1, 4, 1, 5]]]      # max(*[...]) → 5
@var[r; @unpack[dict; {"a": 1, "b": 2}]]    # dict(**{...})
```

### Other Commands

```clpy
@del[x]
@del[a; b; c]
@assert[x > 0; "x must be positive"]
@var[home; @env[HOME]]
@var[port; @env[PORT; 8080]]
@import[requests]
@import[requests; req]
@include[utils.clpy]
@swap[a; b]
@inc[counter]
@dec[counter; 5]
```

### Raw Python Blocks

```clpy
@raw
    import sys
    from pathlib import Path
    x = [i**2 for i in range(10)]
@end
```

### Collections

```clpy
@var[lst; @list[1; 2; 3]]
@var[d; @dict["name"; "Alice"; "age"; 30]]
```

### Multi-line Expressions

```clpy
@var[result; max(
    score_a,
    score_b,
    score_c
)]

@var[items; [
    "apple",
    "banana",
    "cherry"
]]
```

---

## Errors & Diagnostics

When something goes wrong, Cruhon shows the exact line, a caret under the
problem, a plain-language hint, and a spelling suggestion:

```
✗ NameError  greet.clpy:3

  name 'price' is not defined

     1 │ @var[name; "World"]
     2 │ @print[Hello]
   → 3 │ @var[total; price + tax]

  Hint: 'price' is not defined as a variable.
        If you meant text, wrap it in quotes: "price".
```

`cruhon check file.clpy` shows the same rich excerpt for syntax errors without
running the script. Color auto-disables for pipes and when `NO_COLOR` is set.

### Logging

```bash
# Cruhon engine diagnostics
CRUHON_LOG=cruhon.log cruhon run app.clpy
CRUHON_LOG_LEVEL=DEBUG CRUHON_LOG=cruhon.log cruhon run app.clpy
cruhon run app.clpy --log cruhon.log --log-level DEBUG
```

Levels: `ERROR`, `WARNING`, `INFO` (default), `DEBUG`.

For **script-level** application logging use `@log.*`:

```clpy
@log.setup["DEBUG"; "app.log"]
@log.info["Application started"]
@log.warning["Something looks off"]
@log.error["Critical failure"]
```

### Transpile Cache

Cruhon caches compiled output in `.cruhon_cache/`. Re-runs of unchanged
scripts skip parsing entirely.

```bash
cruhon cache          # show stats
cruhon cache --clear  # delete cache
cruhon run app.clpy --no-cache  # bypass for one run
```

---

## Value Semantics

**`expr` context** — right-hand sides of `@var`, `@const`, `@return`, etc.:
- `"text"` → string literal
- `42`, `3.14` → numeric literal
- `True`, `False`, `None` → Python literal
- `[...]`, `{...}`, `(...)` → collection or expression, passed through
- Expression with operator / call / dot → passed through as Python expression
- Single identifier → Python variable reference
- Bare text → string literal

**`display` context** — `@print`, `@assert` message:
- Same as `expr`, except a **single identifier becomes a string literal**
- Use `{varname}` for variable interpolation

---

## Context Variables (`@ctx`)

`__ctx__` is a shared dict available throughout script execution.

```clpy
@ctx.set["username"; "Alice"]
@var[u; @ctx.get["username"]]
@var[u; @ctx.get["username"; "guest"]]
@ctx.delete["score"]
@ctx.clear[]

# Stack-based scope
@ctx.push[]
    @ctx.set["x"; "inner"]
    @var[inner_x; @ctx["x"]]
    @print[{inner_x}]
@ctx.pop[]
```

---

## Standard Libraries — 128 Namespaces

All namespaces are available without `@import`. Just call them directly.
See [`library.md`](library.md) for the complete method reference.

### Core (Cruhon-native)

| Namespace | What it does |
|---|---|
| `@file.*` | Read, write, copy, move, glob, mkdir, stat, symlink, chmod… |
| `@date.*` | now, format, parse, add, diff, timezone, ISO, weekday… |
| `@text.*` | upper, lower, split, replace, regex, slug, encode, partition… |
| `@http.*` | GET, POST, PUT, DELETE, upload, auth, async variants… |
| `@crypto.*` | SHA-256/512, hmac, pbkdf2, scrypt, UUID, token, base64… |
| `@log.*` | setup, info, warning, error, to_file, get, child, formatter… |
| `@config.*` | load, save, get, set, keys, dotenv, env (JSON/TOML/INI)… |
| `@shell.*` | run, output, lines, bg, kill, wait, env, cpu_count… |
| `@archive.*` | zip, unzip, tar, gzip, bzip2, lzma and all their inverses… |
| `@mail.*` | send, send_html, IMAP connect/search/fetch, SMTP login… |
| `@csv.*` | read, write, filter, to_json, append… |
| `@store.*` | set, get, all, clear, delete (in-memory key-value) |
| `@color.*` | red, green, blue, yellow, bold, dim, reset… |
| `@ctx.*` | set, get, push, pop, clear, delete |
| `@json.*` | load, dump |

### Text & Math

| Namespace | Wraps | Highlights |
|---|---|---|
| `@math.*` | `math` | sqrt, floor, ceil, pow, log, sin/cos/tan, gcd, clamp… |
| `@random.*` | `random` | randint, choice, shuffle, sample, gauss, seed… |
| `@cmath.*` | `cmath` | Complex sqrt, exp, log, polar, rect, phase… |
| `@decimal.*` | `decimal` | Exact arithmetic: add, sub, mul, div, round, compare… |
| `@fraction.*` | `fractions` | make, add, sub, mul, div, simplify, to_float… |
| `@statistics.*` | `statistics` | mean, median, mode, stdev, variance, correlation… |
| `@textwrap.*` | `textwrap` | wrap, fill, indent, dedent, shorten, columns… |
| `@string.*` | `string` | ascii_letters, digits, punctuation, capwords, template… |
| `@unicode.*` | `unicodedata` | name, category, normalize, NFC/NFD, strip_accents… |
| `@colorsys.*` | `colorsys` | RGB↔HSV, RGB↔HLS, RGB↔YIQ, hex helpers, luminance, blend |
| `@codecs.*` | `codecs` | rot13, hex, zlib codec, encode/decode, stream wrappers… |

### Data & Formats

| Namespace | Wraps | Highlights |
|---|---|---|
| `@collections.*` | `collections` | Counter, defaultdict, deque, namedtuple, OrderedDict… |
| `@itertools.*` | `itertools` | chain, cycle, product, combinations, groupby, flatten… |
| `@functools.*` | `functools` | reduce, partial, lru_cache, wraps, singledispatch… |
| `@operator.*` | `operator` | add, sub, mul, itemgetter, attrgetter, lt, gt, and_… |
| `@xml.*` | `xml.etree.ElementTree` | parse, find, findall, text, attr, children, to_string… |
| `@toml.*` | `tomllib` | loads, load, dumps, get, has, keys, to_dict… |
| `@yaml.*` | `pyyaml` | loads, dumps, load_file, dump_file, get, keys… |
| `@diff.*` | `difflib` | ratio, best_match, ndiff, unified_diff, sequence_matcher… |
| `@re.*` | `re` | search, match, findall, sub, split, groups, compile… |
| `@struct.*` | `struct` | pack, unpack, calcsize, pack_into, unpack_from… |
| `@binascii.*` | `binascii` | hexlify, unhexlify, b2a_base64, a2b_base64, crc32… |
| `@pickle.*` | `pickle` | dump, dumps, load, loads, to_file, from_file, copy… |
| `@shelve.*` | `shelve` | open, get, set, delete, keys, values, items, sync… |
| `@plist.*` | `plistlib` | dumps, loads, to_file, from_file, to_dict… |
| `@reprlib.*` | `reprlib` | repr, shorten, maxstring, maxlist, maxdict, maxset… |
| `@graphlib.*` | `graphlib` | sort, is_dag, ancestors, descendants, roots, leaves… |

### File & Path

Path manipulation is covered by `@file.*` (above) — there is no separate
`@pathlib.*` namespace.

| Namespace | Wraps | Highlights |
|---|---|---|
| `@glob.*` | `glob` | glob, iglob, recursive, escape, fnmatch… |
| `@tempfile.*` | `tempfile` | file, dir, named, spooled, mkstemp, mkdtemp… |
| `@fnmatch.*` | `fnmatch` | match, filter, translate, fnmatchcase… |
| `@fileinput.*` | `fileinput` | lines, input, filename, lineno, close… |
| `@stat.*` | `stat` | mode_str, is_dir, is_file, is_link, is_socket, permissions… |
| `@shutil.*` | `shutil` | copy, move, tree, rmtree, disk_usage, which, unpack_archive… |
| `@filecmp.*` | `filecmp` | equal, shallow, dircmp, same_files, diff_files, compare… |
| `@linecache.*` | `linecache` | line, lines, count, check, clear… |
| `@mmap.*` | `mmap` | read, slice, size, find, open, seek, put, flush, close… |
| `@zipapp.*` | `zipapp` | create, interpreter, is_archive, copy… |

### OS & System

| Namespace | Wraps | Highlights |
|---|---|---|
| `@os.*` | `os` | env, path, listdir, getcwd, makedirs… |
| `@sys.*` | `sys` | argv, exit, path, version, platform, getsizeof, stdin… |
| `@platform.*` | `platform` | system, node, release, version, machine, python_version… |
| `@gc.*` | `gc` | collect, enable, disable, isenabled, count, threshold… |
| `@inspect.*` | `inspect` | signature, members, source, module, file, isfunction… |
| `@traceback.*` | `traceback` | format, print, format_exc, extract, lines, last… |
| `@warnings.*` | `warnings` | warn, ignore, error, once, always, simplefilter… |
| `@weakref.*` | `weakref` | ref, proxy, finalize, deref, is_alive… |
| `@types.*` | `types` | new_class, SimpleNamespace, MappingProxy, is_function… |
| `@abc.*` | `abc` | abstract, abstractmethod, isabstract, ABC, ABCMeta… |
| `@signal.*` | `signal` | handler, send, alarm, pause, set_wakeup, getsignal… |
| `@atexit.*` | `atexit` | register, unregister, handlers… |
| `@locale.*` | `locale` | setlocale, getlocale, format_number, currency, strxfrm… |
| `@gettext.*` | `gettext` | translation, gettext, ngettext, bindtextdomain… |
| `@sysconfig.*` | `sysconfig` | get_path, get_config_var, get_platform, variables… |
| `@resource.*` | `resource` | getrlimit, setrlimit, getrusage, RLIMIT_CPU, RLIMIT_AS… |
| `@errno.*` | `errno` | name, description, code, ENOENT, EEXIST, EACCES… |
| `@getpass.*` | `getpass` | password, user, terminal… |

### Networking

| Namespace | Wraps | Highlights |
|---|---|---|
| `@http.*` | `requests` / `httpx` | GET/POST/PUT/DELETE, upload, auth, sessions, async_get/post/put/patch/delete (httpx-backed)… |
| `@socket.*` | `socket` | connect, send, recv, server, bind, accept, udp, tcp… |
| `@ssl.*` | `ssl` | wrap, context, load_cert, verify_mode, check_hostname… |
| `@ftp.*` | `ftplib` | connect, login, list, download, upload, rename, mkdir… |
| `@pop3.*` | `poplib` | connect, list, retrieve, delete, stat, top, uidl… |
| `@xmlrpc.*` | `xmlrpc.client` | client, call, multi_call, fault, close… |
| `@httpserver.*` | `http.server` | serve, serve_async, threaded, stop, close, port… |
| `@selectors.*` | `selectors` | new, watch_read, watch_write, wait, count, modify… |
| `@ip.*` | `ipaddress` | address, network, is_private, is_global, hosts, netmask… |
| `@url.*` | `urllib.parse` | parse, join, quote, unquote, encode, scheme, netloc… |
| `@html.*` | `html` / `re` | escape, unescape, strip_tags, links, images, text… |
| `@webbrowser.*` | `webbrowser` | open, open_new, open_tab, get, browsers, controller… |
| `@mimetypes.*` | `mimetypes` | guess, guess_ext, guess_all, is_text, charset, known… |

### Concurrency

| Namespace | Wraps | Highlights |
|---|---|---|
| `@asyncio.*` | `asyncio` | run, gather, wait_for, task, lock, queue, semaphore, open… |
| `@threading.*` | `threading` | Thread, Lock, RLock, Event, Semaphore, Condition, Barrier… |
| `@multiprocessing.*` | `multiprocessing` | cpus, pool, map, starmap, process, queue, pipe, event… |
| `@futures.*` | `concurrent.futures` | threads, processes, submit, result, map, wait_first… |
| `@queue.*` | `queue` | Queue, LifoQueue, PriorityQueue, put, get, empty, full… |
| `@sched.*` | `sched` | new, run, after, at, cancel, empty, queue… |

### Serialization & Database

| Namespace | Wraps | Highlights |
|---|---|---|
| `@sqlite.*` | `sqlite3` | open, close, execute, fetchall, fetchone, commit, tables… |
| `@pickle.*` | `pickle` | dump, load, dumps, loads, to_file, from_file, copy… |
| `@shelve.*` | `shelve` | open, get, set, delete, keys, items, sync, close… |
| `@plist.*` | `plistlib` | dumps, loads, to_file, from_file… |
| `@configparser.*` | `configparser` | load, new, get, set, sections, add_section, save… |

### Testing & Profiling

| Namespace | Wraps | Highlights |
|---|---|---|
| `@unittest.*` | `unittest` | run, discover, assert_equal, assert_true, mock, patch… |
| `@doctest.*` | `doctest` | run, testmod, testfile, globs, verbose… |
| `@timeit.*` | `timeit` | time, repeat, stmt, setup, auto… |
| `@profile.*` | `cProfile` | run, sort, stats, dump, top, cumulative, callers… |
| `@tracemalloc.*` | `tracemalloc` | start, stop, snapshot, top, compare, peak, size… |

### Developer Tools

| Namespace | Wraps | Highlights |
|---|---|---|
| `@ast.*` | `ast` | parse, dump, unparse, walk, names, functions, is_valid… |
| `@dis.*` | `dis` | bytecode, instructions, opnames, consts, varnames… |
| `@tokenize.*` | `tokenize` | tokens, names, keywords, comments, ops, numbers, count… |
| `@keyword.*` | `keyword` | iskeyword, issoftkeyword, all, soft_all, kwlist… |
| `@importlib.*` | `importlib` | import_module, reload, find_spec, source_hash… |
| `@inspect.*` | `inspect` | signature, members, source, isfunction, isclass… |
| `@pdb.*` | `pdb` | bp, pm, run, runeval, runcall, new, set_bp… |
| `@runpy.*` | `runpy` | module, path, module_ns, path_ns, find, result… |
| `@numbers.*` | `numbers` | is_number, is_complex, is_real, is_rational, is_integral |
| `@reprlib.*` | `reprlib` | repr, shorten, maxstring, maxlist, maxdict… |

### Encoding & Compression

| Namespace | Wraps | Highlights |
|---|---|---|
| `@base64.*` | `base64` | encode, decode, urlsafe, b32, b16, standard, pad… |
| `@codecs.*` | `codecs` | encode, decode, rot13, hex, zlib codec, reader, writer… |
| `@binascii.*` | `binascii` | hexlify, unhexlify, b2a_base64, crc32, rlecode… |
| `@zlib.*` | `zlib` | compress, decompress, crc32, adler32, crc32_hex… |
| `@struct.*` | `struct` | pack, unpack, calcsize, iter_unpack… |
| `@archive.*` | `zipfile`/`tarfile`/`gzip`/`bz2`/`lzma` | zip, unzip, tar, gzip, bzip2, lzma and inverses |

### Foreign Function Interface

| Namespace | Wraps | Highlights |
|---|---|---|
| `@ctypes.*` | `ctypes` | load CDLL, all C scalar types, buffer, pointer, cast… |
| `@array.*` | `array` | typed compact arrays — append, extend, insert, pop, slice… |

### Configuration & Secrets

| Namespace | Wraps | Highlights |
|---|---|---|
| `@env.*` | `os.environ` | get, require, has, typed (`int`/`float`/`bool`/`list`/`json`), set, `.env` load/parse/save, **mask** (hide secrets), expand `$VAR` |
| `@config.*` | `json`/`tomllib`/`configparser` | load, save, get, set, keys, dotenv, env |

```clpy
# Read configuration safely from the environment / a .env file
@env.load[]                                 # auto-load ./.env
@var[port; @env.int["PORT"; 8080]]          # typed, with a default
@var[debug; @env.bool["DEBUG"]]             # 1/true/yes/on → True
@var[key; @env.require["API_KEY"]]          # raises if missing
@var[safe; @env.mask[key]]                  # "ab••••••89" — safe to log
@print[Using key {safe}]
```

### Utilities

| Namespace | Wraps | Highlights |
|---|---|---|
| `@argparse.*` | `argparse` | new, add, run, run_known, parse, parse_dict… |
| `@dataclasses.*` | `dataclasses` | dataclass, field, asdict, astuple, fields, replace… |
| `@typing.*` | `typing` | Optional, Union, List, Dict, Any, Callable, TypeVar… |
| `@enum.*` | `enum` | Enum, IntEnum, StrEnum, Flag, auto, create, names… |
| `@contextlib.*` | `contextlib` | contextmanager, suppress, redirect_stdout, ExitStack… |
| `@copy.*` | `copy` | copy, deepcopy, replace… |
| `@io.*` | `io` | StringIO, BytesIO, read, write, seek, getvalue… |
| `@heapq.*` | `heapq` | heappush, heappop, heapify, nlargest, nsmallest… |
| `@bisect.*` | `bisect` | bisect_left, bisect_right, insort, insort_left… |
| `@calendar.*` | `calendar` | is_leap, days_in_month, month_name, weekday… |
| `@pprint.*` | `pprint` | pformat, pprint, saferepr, isreadable, isrecursive… |
| `@shlex.*` | `shlex` | split, join, quote, lex, punctuation_chars… |
| `@colorsys.*` | `colorsys` | RGB↔HSV/HLS/YIQ, hex_to_rgb, rgb_to_hex, luminance… |
| `@zipapp.*` | `zipapp` | create, is_archive, interpreter, copy… |

---

## Examples

### HTTP API script

```clpy
@var[res; @http.get["https://jsonplaceholder.typicode.com/todos/1"]]
@var[todo; @http.json[res]]
@print[Title: {todo["title"]}]
@print[Done: {todo["completed"]}]
```

### File processing

```clpy
@var[lines; @file.readlines["data.txt"]]
@for[line; lines]
    @var[clean; @text.strip[line]]
    @if[clean]
        @file.append["output.txt"; "{clean}\n"]
    @end
@end
```

### Async HTTP

```clpy
@async[fetch_all; urls]
    @var[tasks; [@asyncio.task[@http.async_get[u]] for u in urls]]
    @var[results; @asyncio.gather[*tasks]]
    @return[results]
@end

@var[urls; ["https://example.com", "https://httpbin.org/get"]]
@asyncio.run[fetch_all(urls)]
```

### CSV → JSON

```clpy
@var[rows; @csv.read["sales.csv"]]
@var[filtered; [r for r in rows if float(r["amount"]) > 100]]
@file.write["big_sales.json"; @json.dump[filtered]]
@print[Exported {len(filtered)} rows]
```

### Parallel processing

```clpy
@func[process; item]
    @return[item * item]
@end

@var[data; list(range(1000))]
@var[pool; @futures.threads[8]]
@var[results; @futures.map[pool; process; data]]
@print[Sum: {sum(results)}]
```

### Color system conversion

```clpy
@var[rgb; @colorsys.hex_to_rgb["#3498db"]]
@var[h; @colorsys.to_hls[rgb[0]; rgb[1]; rgb[2]]]
@print[Hue: {h[0]:.2f}  Lightness: {h[1]:.2f}]
```

### Tokenize Python source

```clpy
@var[src; "def add(a, b):\n    return a + b\n"]
@var[keywords; @tokenize.keywords[src]]
@for[tok; keywords]
    @print[keyword: {tok.string}]
@end
```

### Run code under debugger

```clpy
@var[dbg; @pdb.new[]]
@pdb.set_bp[dbg; "mymodule.py"; 42]
@pdb.run[dbg; "mymodule.run()"]
```

---

## Plugin System

Cruhon's plugin system lets you extend the language itself. Plugins can:

- Add new `@commands` and `@block ... @end` commands
- Override existing commands with middleware chains
- Inject runtime objects into scripts (database connections, config, etc.)
- Register inline expression commands (`@var[x; @uuid[]]`)
- Hook into value evaluation at transpile-time
- Manipulate the AST before code generation
- Communicate with other plugins via expose/consume
- Hook into lifecycle events (before/after run, parse, transpile)

### Project Structure

```
myproject/
├── src/
│   └── main.clpy
└── mods/
    └── my-plugin/
        ├── mod.json
        └── __init__.py
```

```bash
cruhon new --plugin my-plugin
```

### mod.json

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What this plugin does",
  "cruhon": ">=2.0.0"
}
```

Any extra field is accessible via `api.config("key")` inside the plugin.

### `register(api)` — Entry Point

Every plugin must have a `register(api)` function in `__init__.py`:

```python
def register(api):
    api.command("greet", parse_greet, visit_greet)
```

---

## Plugin API Reference

### `api.command(name, parser_fn, visitor_fn)`

```python
from cruhon.core.ast_nodes import Node
from dataclasses import dataclass

@dataclass
class GreetNode(Node):
    target: str = ""

def parse_greet(parser):
    parser.advance()
    args = parser.parse_args()
    return GreetNode(target=args[0] if args else '"world"', line=0)

def visit_greet(transpiler, node):
    return transpiler._line(f'print("Hello, " + str({node.target}))', node.line)

def register(api):
    api.command("greet", parse_greet, visit_greet)
```

### `api.block_command(name, visitor_fn, scoped=False)`

```python
def visit_section(transpiler, node):
    title = node.args[0] if node.args else '"Untitled"'
    body_code = "\n".join(r for n in node.body if (r := n.accept(transpiler)))
    return (
        transpiler._line(f'print("=== " + {title} + " ===")') +
        "\n" + body_code
    )

def register(api):
    api.block_command("section", visit_section)
    # scoped=True → __ctx__ snapshot, changes don't leak
    api.block_command("isolated", visit_isolated, scoped=True)
```

### `api.override(command, fn)`

Multiple overrides form a middleware chain:

```python
def timed_print(transpiler, node, next_fn):
    before = transpiler._line('__t0__ = __import__("time").monotonic()')
    result = next_fn()
    after  = transpiler._line('print(f"[{__import__(\"time\").monotonic()-__t0__:.3f}s]")')
    return before + "\n" + result + "\n" + after

def register(api):
    api.override("print", timed_print)
```

### `api.inject(key, value_or_factory)`

```python
def register(api):
    api.inject("APP_VERSION", "2.9.0")
    api.inject("db", lambda: sqlite3.connect(":memory:"))
```

### `api.inject_once(key, factory)`

Factory runs once at load time; shared across all runs:

```python
def register(api):
    api.inject_once("pool", lambda: ConnectionPool(max_connections=10))
```

### `api.inline_command(name, handler_fn)`

```python
def handle_uuid(parser):
    parser.advance()
    parser.parse_args()
    return "str(__import__('uuid').uuid4())"

def register(api):
    api.inline_command("uuid", handle_uuid)
```

### `api.eval_hook(fn)`

Hook into value evaluation at transpile-time:

```python
def dollar_env(value, context):
    if value.startswith("$") and value[1:].isidentifier():
        return f'__import__("os").environ.get("{value[1:]}", "")'
    return None

def register(api):
    api.eval_hook(dollar_env)
```

### `api.ast_hook(node_type, fn)`

```python
def prefix_vars(node):
    if not node.name.startswith("_"):
        node.name = "safe_" + node.name
    return node

def register(api):
    api.ast_hook("VarNode", prefix_vars)
```

### `api.transform(target, fn)`

Wrap another plugin's block output:

```python
def register(api):
    api.transform("route", time_route)

def time_route(transpiler, node, code):
    path = node.args[0] if node.args else '"unknown"'
    before = transpiler._line('__t0__ = __import__("time").monotonic()')
    after  = transpiler._line(f'print(f"route {path} took {{__import__(\"time\").monotonic()-__t0__:.3f}}s")')
    return before + "\n" + code + "\n" + after
```

### `api.hook(event, fn)`

| Event | Signature | When |
|---|---|---|
| `before_run` | `fn(source=str)` | Before parsing |
| `after_run` | `fn(source=str, python_code=str)` | After exec finishes |
| `before_parse` | `fn(source) -> source` | Modify source text |
| `after_parse` | `fn(ast) -> ast` | Modify AST |
| `before_transpile` | `fn(ast) -> ast` | Transpiler pre-hook |
| `after_transpile` | `fn(code) -> code` | Modify generated Python |
| `on_error` | `fn(error=exc)` | On any error |

```python
def register(api):
    api.hook("before_run", lambda source: print("[run start]"))
    api.hook("on_error",   lambda error: print(f"[error] {error}"))
```

### `api.expose` / `api.consume`

```python
# Plugin A
def register(api):
    api.expose("slugify", lambda s: s.lower().replace(" ", "-"))

# Plugin B
def register(api):
    slugify = api.consume("plugin-a", "slugify")
```

### `api.namespace(name)`

```python
def register(api):
    ns = api.namespace("db")
    ns.register("query", lambda args: f'__db__.execute({args[0]}).fetchall()')
    ns.hook("init",    lambda ns: print("db ready"))
    ns.hook("destroy", lambda ns: print("db closed"))
```

### Cleanup

```python
api.unregister_command("print")
api.remove_hook("before_run", fn)
api.remove_inject("db_pool")
api.remove_eval_hook(dollar_env)
```

### Other helpers

```python
api.alias("say", "print")           # @say → @print
api.require("cruhon-utils >= 1.2.0")
api.is_loaded("cruhon-redis")
api.config("my_setting", default="x")
api.block_hook("enter", on_enter)   # runtime block start/end events
api.lexer_hook(lambda src: src.replace("§", "@"))
api.token_hook(lambda toks: [t for t in toks if t.type != "COMMENT"])
```

---

## Complete Plugin Example

> Pick a namespace your plugin doesn't already share with a stdlib
> namespace (`@log.*`, `@http.*`, `@file.*`, … are all reserved — see
> [`library.md`](library.md) for the full list). This example uses
> `applog` to stay clear of the built-in `@log.*` namespace. Even when a
> custom `api.block_command`/`api.command` registration *does* share a
> prefix with a stdlib namespace, the plugin's own registration always
> wins for that exact dotted name — but picking a distinct name avoids
> the confusion of two different things answering to `@log.*`.
>
> `api.command(name, parser_fn, visitor_fn)` expects a matching AST node
> class named `name.title() + "Node"` — for `"applog"` that's `ApplogNode`.

```python
"""
mods/cruhon-applog/__init__.py
Adds @applog["msg"] and @applog.timed[label] ... @end
"""
import datetime


class Logger:
    def __init__(self):
        self.lines = []

    def log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        self.lines.append(line)
        print(line)


_logger = Logger()


def parse_log(parser):
    from cruhon.core.ast_nodes import Node
    from dataclasses import dataclass

    @dataclass
    class ApplogNode(Node):
        msg: str = ""

    parser.advance()
    args = parser.parse_args()
    return ApplogNode(msg=args[0] if args else '""', line=0)


def visit_log(transpiler, node):
    # Route the message through Cruhon's own value evaluator so
    # {variable} interpolation works exactly like it does in @print.
    msg = transpiler._eval_value(node.msg, "display")
    return transpiler._line(f'logger.log({msg})', node.line)


def visit_timed(transpiler, node):
    label = (node.args[0] if node.args else '"block"').strip('"')
    body = "\n".join(r for n in node.body if (r := n.accept(transpiler)))
    t = transpiler
    return "\n".join([
        t._line("__t0__ = __import__('time').monotonic()"),
        body or t._line("pass"),
        t._line(f'logger.log(f"{label} took {{__import__(\'time\').monotonic()-__t0__:.3f}}s")'),
    ])


def register(api):
    api.inject("logger", lambda: _logger)
    api.command("applog", parse_log, visit_log)
    api.block_command("applog.timed", visit_timed)
    api.expose("get_log_lines", lambda: _logger.lines)
```

Usage:

```clpy
@applog["Script started"]

@applog.timed["data processing"]
    @var[data; [1, 2, 3]]
    @var[result; sum(data)]
    @applog["Processed {result} items"]
@end

@applog["Done"]
```

---

## Publishing a Plugin

```
cruhon-logger/
├── pyproject.toml
└── cruhon_logger/
    ├── __init__.py
    └── mod.json
```

```toml
# pyproject.toml
[project]
name = "cruhon-logger"
version = "1.0.0"

[project.entry-points."cruhon.mods"]
cruhon-logger = "cruhon_logger:register"
```

```bash
pip install cruhon-logger
cruhon run script.clpy   # plugin auto-loaded
cruhon mods              # see it in the list
```

**Load order:** core → stdlib → pip plugins (alphabetical) → local `mods/` (alphabetical)

---

## Shortcut Plugins

Four configurable shortcut plugins add shorter aliases and extra convenience
methods. All four load together without conflicts:

```clpy
# cruhon-shortcuts (base)
@var[text; @read["notes.txt"]]         # @read → @file.read
@var[stamp; @now[]]                     # @now  → @date.now
@var[id; @uuid[]]                       # @uuid → @crypto.uuid

# cruhon-shortcuts-pro (math / lists / dicts / text / logic)
@var[x; @clamp[value; 0; 100]]
@var[slug; @snake_case["Hello World"]]
@var[g; @group_by[items; key_fn]]

# cruhon-shortcuts-data (xml / toml / diff / decimal / re / yaml / image / pdf)
@var[cfg; @toml_load["port = 8080"]]
@var[amt; @money["3.14159"]]            # decimal.money → 2dp
@var[ok; @is_private_ip["10.0.0.1"]]
```

---

## Bundled Plugins

These ship in `mods/` and load automatically:

### `@db.*` — multi-backend database (cruhon-db)

SQLite, PostgreSQL, MySQL with full CRUD, transactions, and async — 170+
commands. Also env-aware connection, migrations, seeding, and a live
`@panel` bridge:

```clpy
@db.connect_env["DATABASE_URL"]        # DSN from the environment
@db.migrate["./migrations"]            # apply *.sql files once, in order
@db.seed["users"; "fixtures/users.json"]   # bulk-load JSON or CSV
@var[safe; @db.dsn_safe[]]
@print[Connected to {safe}]            # DSN with the password masked

@panel.start[8787]
@db.attach_panel[]                     # every query now streams to the panel
```

### `@panel.*` — live log-stream dashboard (cruhon-panel)

A zero-dependency web panel that streams logs, metrics, and events to the
browser over Server-Sent Events — pure standard library.

```clpy
@panel.start[8787]                     # → http://127.0.0.1:8787
@panel.attach_logging["INFO"]          # mirror all @log.* output to the panel
@log.info["server warming up"]         # …shows up live in the browser
@panel.metric["users online"; 42]      # update a metric tile
@panel.event["deploy"; {"version": "2.10"}]
@db.attach_panel[]                     # stream every SQL query too (needs @db)
@panel.open[]                          # open the dashboard in a browser
@panel.wait[]                          # keep the panel alive
```

### `@discord.*` — Discord bot toolkit (cruhon-discord)

~60 commands for building bots — see `mods/cruhon-discord`.

---

## Creating a New Project

```bash
cruhon new myproject
cd myproject
cruhon run src/main.clpy
```

Creates:

```
myproject/
├── src/
│   └── main.clpy
└── mods/
    └── README.md
```

---

## Contributing

```bash
git clone https://github.com/cruciblelab/cruhon
cd cruhon
pip install -e .
python -m pytest cruhon/tests/
cruhon run cruhon/examples/hello.clpy
```

---

## Contact

- **Discord:** [discord.gg/SPf5VZ6QPG](https://discord.gg/SPf5VZ6QPG)
- **Email:** [cruciblelab@hotmail.com](mailto:cruciblelab@hotmail.com)
- **GitHub:** [github.com/cruciblelab](https://github.com/cruciblelab)

---

## License

MIT — CrucibleLab
