# Changelog

All notable changes are documented here.

---

## v2.10.0 (current) — Config & Secrets, Env-aware DB, Live Panel

This release rounds out real-world deployment: read configuration safely,
connect databases from the environment, and watch everything live in a
browser.

### New namespace — `@env.*` (environment variables & secrets)

A single, safe surface for configuration. 18 commands:

| Group | Commands |
|---|---|
| Read | `get`, `require` (fail fast if missing), `has`, `all`, `prefix` |
| Typed | `int`, `float`, `bool` (1/true/yes/on), `list`, `json` |
| Write | `set`, `unset`, `setdefault` |
| `.env` files | `load` (auto-loads `./.env`), `parse`, `save` |
| Secrets | `mask` (`"ab••••••89"` — safe to log/stream), `expand` (`$VAR`) |

```clpy
@env.load[]
@var[port; @env.int["PORT"; 8080]]
@var[key;  @env.require["API_KEY"]]
@print[key = {@env.mask[key]}]
```

### cruhon-db — env-aware connection, migrations, seeding

Four new commands on the `@db.*` plugin:

| Command | Does |
|---|---|
| `@db.connect_env[]` / `@db.connect_env[VAR]` | Connect using a DSN from an env var (default `DATABASE_URL`) — keeps secrets out of source |
| `@db.migrate[dir]` | Apply every `*.sql` file in order, once each, tracked in a `_cruhon_migrations` table (idempotent) |
| `@db.seed[table; file]` | Bulk-insert rows from a `.json` or `.csv` file |
| `@db.dsn_safe[]` | The active DSN with the password masked — safe to print/log |

### New plugin — `@panel.*` (live log-stream dashboard)

A zero-dependency web panel (`mods/cruhon-panel`). Start it, open the URL,
and watch logs, metrics, and events stream into the browser over
Server-Sent Events — pure standard library, no pip installs.

| Command | Does |
|---|---|
| `@panel.start[port]` | Start the dashboard server → returns the URL |
| `@panel.log[msg; level]` · `info`/`warn`/`error`/`debug` | Stream a log line |
| `@panel.metric[name; value]` | Push/update a metric tile |
| `@panel.event[type; data]` | Push an arbitrary JSON event |
| `@panel.attach_logging[level]` | Mirror all `@log.*` output to the panel |
| `@panel.open[]` · `url[]` · `clients[]` · `wait[]` · `stop[]` | Lifecycle |

```clpy
@panel.start[8787]
@panel.attach_logging["INFO"]
@log.info["server warming up"]
@panel.metric["users online"; 42]
@panel.wait[]
```

### Counts

- **128 stdlib namespaces** (was 127) · **1839 handlers** (was 1821)
- cruhon-db: **170+ commands** (was 166)
- New plugin: cruhon-panel
- **4034 tests** passing (was 3999)

---

## v2.9.0 — Async, FFI, Color Math, Tokenizer, Debugger

8 new namespaces · 131 new handler methods · 3999 tests

### New namespaces

| Namespace | Wraps | What you can do |
|---|---|---|
| `@asyncio.*` | `asyncio` | Run coroutines (`run`, `gather`, `wait_for`), create tasks, async primitives (lock, event, semaphore, queue), open async connections, `asyncio.timeout` context manager |
| `@codecs.*` | `codecs` | ROT-13, hex codec, zlib codec encode/decode, named codec encode/decode with error handlers, `getreader`/`getwriter` stream wrappers |
| `@colorsys.*` | `colorsys` | RGB ↔ HSV, RGB ↔ HLS, RGB ↔ YIQ — plus hex helpers (`hex_to_rgb`, `rgb_to_hex`, `hex_to_hsv`, `hex_to_hls`), perceptual luminance, linear color blend |
| `@ctypes.*` | `ctypes` | Load C libraries (`CDLL`, `load_util`), all C scalar types (`c_int`, `c_double`, `c_char_p`, …), buffer creation, pointer/byref/cast ops, `sizeof`, raw memory (`memmove`, `memset`) |
| `@tokenize.*` | `tokenize` | Tokenize Python source strings — list all tokens or filter by category (`names`, `keywords`, `comments`, `ops`, `numbers`, `strings`), token type constants, `untokenize`, `unique_names` |
| `@zipapp.*` | `zipapp` | Create runnable `.pyz` ZIP archives (`create` with optional main entry and interpreter), inspect `interpreter`, test `is_archive`, copy archives |
| `@runpy.*` | `runpy` | Run any Python module as `__main__` (`module`, `module_ns`), run a script file (`path`, `path_ns`), check if a module exists (`is_module`), `find` spec |
| `@pdb.*` | `pdb` | Set breakpoints (`bp`, `set_bp`), post-mortem analysis (`pm`), run code under debugger (`run`, `runeval`, `runcall`), create `Pdb` instances |

### Handler count: 1690 → 1822

---

## v2.8.0 — Major stdlib Expansion (49 New Namespaces)

49 new namespaces · ~900 new handler methods · 3807 tests

### New namespaces by category

**Text & Math**

| Namespace | Wraps | Highlights |
|---|---|---|
| `@textwrap.*` | `textwrap` | wrap, fill, shorten, dedent, indent, columns |
| `@getpass.*` | `getpass` | password, user, terminal |
| `@cmath.*` | `cmath` | Complex sqrt, exp, log, polar, rect, phase, pi, e, inf, nan |
| `@array.*` | `array` | Typed compact arrays — append, extend, insert, pop, remove, set, slice, from_file, to_file |

**OS & System**

| Namespace | Wraps | Highlights |
|---|---|---|
| `@gc.*` | `gc` | collect, enable/disable, count, threshold, get_objects, freeze |
| `@inspect.*` | `inspect` | signature, members, source, isfunction, isclass, stack, annotations |
| `@traceback.*` | `traceback` | format, print, format_exc, extract_tb, extract_stack |
| `@warnings.*` | `warnings` | warn, ignore, error, once, always, simplefilter, resetwarnings |
| `@weakref.*` | `weakref` | ref, proxy, finalize, deref, is_alive, WeakValueDictionary |
| `@types.*` | `types` | new_class, SimpleNamespace, MappingProxy, is_function, FunctionType |
| `@abc.*` | `abc` | abstract, abstractmethod, isabstract, ABC, ABCMeta |
| `@signal.*` | `signal` | handler, send, alarm, pause, getsignal, SIGINT, SIGTERM |
| `@mmap.*` | `mmap` | read, slice, find, open (writable), seek, put, flush, close |
| `@atexit.*` | `atexit` | register, unregister, handlers |
| `@locale.*` | `locale` | setlocale, getlocale, format_number, currency, strxfrm |
| `@gettext.*` | `gettext` | translation, gettext, ngettext, bindtextdomain |
| `@argparse.*` | `argparse` | new, add, run, run_known, parse, parse_dict, to_dict |
| `@sysconfig.*` | `sysconfig` | get_path, get_config_var, get_platform, variables |
| `@resource.*` | `resource` | getrlimit, setrlimit, getrusage, RLIMIT_CPU, RLIMIT_AS, utime |

**Networking**

| Namespace | Wraps | Highlights |
|---|---|---|
| `@socket.*` | `socket` | hostname, connect, server, tcp, udp, send, recv, bind, accept |
| `@ssl.*` | `ssl` | wrap, client_context, server_context, load_cert, verify_mode |
| `@ftp.*` | `ftplib` | connect, login, list, download, upload, rename, mkdir, passive |
| `@pop3.*` | `poplib` | connect, list, retrieve, delete, stat, top, uidl |
| `@xmlrpc.*` | `xmlrpc.client` | client, call, multi_call, fault |
| `@httpserver.*` | `http.server` | serve, threaded, serve_async, stop, close, port |
| `@selectors.*` | `selectors` | new, watch_read, watch_write, wait, count, modify, unwatch |

**HTML & Web**

| Namespace | Wraps | Highlights |
|---|---|---|
| `@html.*` | `html` / `re` | escape, unescape, strip_tags, text, links, images, tags |
| `@webbrowser.*` | `webbrowser` | open, open_new, open_tab, get, controller |
| `@mimetypes.*` | `mimetypes` | guess, guess_ext, is_text, charset, known |

**Concurrency**

| Namespace | Wraps | Highlights |
|---|---|---|
| `@multiprocessing.*` | `multiprocessing` | cpus, pool, map, starmap, apply, process, queue, pipe, value |
| `@futures.*` | `concurrent.futures` | threads, processes, submit, result, map, wait_first, as_done |
| `@sched.*` | `sched` | new (uses `time.time`/`time.sleep`), run, after, at, cancel |

**Testing & Profiling**

| Namespace | Wraps | Highlights |
|---|---|---|
| `@timeit.*` | `timeit` | time, repeat, stmt, auto |
| `@profile.*` | `cProfile` | run, sort, stats, dump, top, cumulative |
| `@doctest.*` | `doctest` | run, testmod, testfile, verbose |
| `@unittest.*` | `unittest` | run, discover, assert_equal, assert_true, mock, patch |

**Developer Tools**

| Namespace | Wraps | Highlights |
|---|---|---|
| `@ast.*` | `ast` | parse, dump, unparse, walk, names, functions, classes, is_valid |
| `@dis.*` | `dis` | bytecode, instructions, opnames, consts, varnames, stack_size |
| `@keyword.*` | `keyword` | iskeyword, issoftkeyword, all, kwlist |
| `@importlib.*` | `importlib` | import_module, reload, find_spec, source_hash |
| `@graphlib.*` | `graphlib` | sort, is_dag, ancestors, roots, leaves |
| `@reprlib.*` | `reprlib` | repr, shorten, maxstring, maxlist, maxdict |
| `@tracemalloc.*` | `tracemalloc` | start, stop, snapshot, top, compare, peak |

**File Management & Utilities**

| Namespace | Wraps | Highlights |
|---|---|---|
| `@shutil.*` | `shutil` | copy, move, tree, rmtree, disk_usage, which, make_archive |
| `@filecmp.*` | `filecmp` | equal, shallow, dircmp, same_files, diff_files |
| `@configparser.*` | `configparser` | load, new, get, set, sections, save |
| `@errno.*` | `errno` | name, description, code, ENOENT, EEXIST, EACCES |
| `@linecache.*` | `linecache` | line, lines, count, check, clear |
| `@numbers.*` | `numbers` | is_number, is_complex, is_real, is_rational, is_integral |

**Database & Serialization**

| Namespace | Wraps | Highlights |
|---|---|---|
| `@sqlite.*` | `sqlite3` | open, execute, fetchall, commit, tables, columns, transaction |
| `@pickle.*` | `pickle` | dump, load, dumps, loads, to_file, from_file, copy |
| `@shelve.*` | `shelve` | open, get, set, delete, keys, items, sync |
| `@plist.*` | `plistlib` | dumps, loads, to_file, from_file |

**File & Path (expanded)**

| Namespace | Wraps | Highlights |
|---|---|---|
| `@glob.*` | `glob` | glob, iglob, recursive, fnmatch |
| `@tempfile.*` | `tempfile` | file, dir, named, mkstemp, mkdtemp |
| `@fnmatch.*` | `fnmatch` | match, filter, translate |
| `@fileinput.*` | `fileinput` | lines, input, filename, lineno |
| `@stat.*` | `stat` | mode_str, is_file, is_dir, is_link, permissions |

### Safety net test

New parametrized test (`test_handlers_compile.py`) verifies every registered
handler produces valid Python syntax for at least one arity. Async handlers
(`await ...`) are validated by wrapping in `async def`.

---

## v2.7.0 — Type Annotations, Transpile Cache, REPL Polish

### Type system

Type annotations are now first-class in the language — no `@raw` required.

| Syntax | Emits |
|---|---|
| `@var[x: int; 42]` | `x: int = 42` |
| `@var[x: int]` | `x: int` (annotation-only) |
| `@const[LIMIT: int; 100]` | `LIMIT: int = 100  # const` |
| `@func[f; a: int; b: str; return=bool]` | `def f(a: int, b: str) -> bool:` |
| `@type[Vector; list[float]]` | `Vector = list[float]  # type alias` |
| `@dataclass[Point] ... @end` | `@dataclass` decorated class block |

```clpy
@var[score: float; 0.0]
@const[MAX: int; 100]
@type[Matrix; list[list[float]]]

@dataclass[Point]
    x: float = 0.0
    y: float = 0.0
@end

@func[distance; p: Point; q: Point; return=float]
    @return[((p.x - q.x)**2 + (p.y - q.y)**2) ** 0.5]
@end
```

### Transpile cache

Cruhon now skips re-parsing and re-transpiling files that have not changed.
The cache is written to `.cruhon_cache/` and invalidated automatically when
the source, dependencies, Cruhon version, or Python version changes.

- Binary format — marshal'd code objects with a `CRUHON\x00CACHE\x00V1` magic header
- Atomic writes — temp-file + `os.replace` prevents torn reads
- `cruhon cache` — show stats (file count, total bytes, cache dir)
- `cruhon cache --clear` — delete all cache files
- `--no-cache` / `run_file(no_cache=True)` — bypass for one run

### REPL improvements

- **Persistent history** — `~/.cruhon_history` survives across sessions
- **Tab completion** — completes `@commands` and `:meta-commands`
- **`:history [n]`** — show the last n REPL inputs (default 20)
- **`:load <file.clpy>`** — run a `.clpy` file from the REPL
- **`:type <expr>`** — show the Python type of a value

### Bug fixes

- **Multiple inheritance** — `@class[Dog; Animal; Serializable]` now correctly emits all parents
- **`try`/`except`/`else`** — `@else` between `@catch` and `@finally` is now parsed and emitted

### Tests: 1556 (+82 from v2.6.0)



Type annotations are now first-class in the language — no `@raw` required.

| Syntax | Emits |
|---|---|
| `@var[x: int; 42]` | `x: int = 42` |
| `@var[x: int]` | `x: int` (annotation-only) |
| `@const[LIMIT: int; 100]` | `LIMIT: int = 100  # const` |
| `@func[f; a: int; b: str; return=bool]` | `def f(a: int, b: str) -> bool:` |
| `@type[Vector; list[float]]` | `Vector = list[float]  # type alias` |
| `@dataclass[Point] ... @end` | `@dataclass` decorated class block |

```clpy
@var[score: float; 0.0]
@const[MAX: int; 100]
@type[Matrix; list[list[float]]]

@dataclass[Point]
    x: float = 0.0
    y: float = 0.0
@end

@func[distance; p: Point; q: Point; return=float]
    @return[((p.x - q.x)**2 + (p.y - q.y)**2) ** 0.5]
@end
```

### Transpile cache

Cruhon now skips re-parsing and re-transpiling files that have not changed.
The cache is written to `.cruhon_cache/` next to your project root, mirrors
the source directory structure, and is automatically invalidated when the
source, any `@include`/`@use` dependency, the Cruhon version, or the Python
version changes.

- **Binary format** — cache files are not readable Python source (marshal'd code objects with a `CRUHON\x00CACHE\x00V1` magic header)
- **Atomic writes** — temp-file + `os.replace` prevents torn reads on interruption
- **`cruhon cache`** — show stats (file count, total bytes, cache dir)
- **`cruhon cache --clear`** — delete all cache files
- **`--no-cache`** / `run_file(no_cache=True)` — bypass for one run without deleting the cache

### REPL improvements

- **Persistent history** — `~/.cruhon_history` survives across sessions (readline)
- **Tab completion** — completes `@commands` and `:meta-commands`
- **`:history [n]`** — show the last n REPL inputs (default 20)
- **`:load <file.clpy>`** — run a `.clpy` file directly from the REPL
- **`:type <expr>`** — show the Python type of a value

### Bug fixes

- **Multiple inheritance** — `@class[Dog; Animal; Serializable]` now correctly emits `class Dog(Animal, Serializable):`. Previously only the first parent was used.
- **`try`/`except`/`else`** — `@else` between `@catch` and `@finally` is now parsed and emitted. The `else` branch runs only when no exception was raised.

### Tests: **1556** (+82 from v2.6.0)

---

## v2.6.0 — Templates, Pipelines, Spread/Unpack, LSP

### 6 new language commands

| Command | Usage | Description |
|---|---|---|
| `@template[name] ... @end` | block | Define a named string template with `{key}` placeholders |
| `@render[name; key=value]` | inline/stmt | Render a template with substitutions |
| `@let[x; v1; y; v2; ...]` | stmt | Assign multiple variables in one command |
| `@pipeline[name; fn1; fn2; ...]` | stmt | Define a named function-composition pipeline |
| `@apply[name; value]` | inline/stmt | Apply a pipeline to a value |
| `@spread[fn; iter]` | inline/stmt | Call `fn(*iterable)` — spread positional args |
| `@unpack[fn; dict]` | inline/stmt | Call `fn(**mapping)` — spread keyword args |

```clpy
@template[greeting]
    Hello, {name}! You have {count} messages.
@end

@var[msg; @render[greeting; name="Alice"; count=5]]
@print[{msg}]   # Hello, Alice! You have 5 messages.

@pipeline[normalize; str.strip; str.lower]
@var[result; @apply[normalize; "  Hello  "]]   # "hello"

@let[x; 10; y; 20; z; 30]   # x = 10, y = 20, z = 30

@var[n; @spread[max; [3, 1, 4, 1, 5]]]   # max(*[3,1,4,1,5])
```

### Language Server Protocol (LSP) support

- VS Code extension (`lsp/vscode-cruhon/`) — completions, diagnostics, hover, go-to-definition, symbols for `.clpy` files
- Neovim integration (`lsp/neovim/cruhon_lsp.lua`) — nvim-lspconfig setup with filetype detection and syntax fallback
- Python server package (`lsp/cruhon_lsp/`) — pygls 2.x, `pip install cruhon-lsp`
- 91 command completions + 48 namespace completions with inline docs
- Real-time diagnostics (parse + transpile errors) with line/column positions
- Document symbols panel: `@var`, `@const`, `@func`, `@macro`, `@class`, `@template`, `@pipeline`, `@module`
- Go-to-definition for `@call[macro]`, `@apply[pipeline]`, `@render[template]`

### Bug fix

`_apply_ast_hooks` no longer corrupts `TemplateDefNode.body` — a string field was previously iterated as a character list. Fixed with an `isinstance(list)` guard.

### Tests: **1474** (+32 from v2.5.0)

---

## v2.5.0 — Retry/Timeout/Macro, 4 New Namespaces, CLI tools

### 3 new language block commands

| Command | Usage | Description |
|---|---|---|
| `@retry[n]` or `@retry[n; ExcType]` | block | Retry the body up to n times on exception |
| `@timeout[seconds]` | block | Run body with a wall-clock deadline; raises TimeoutError |
| `@macro[name; p1; ...] ... @end` | block | Define a reusable named macro |
| `@call[name; arg1; arg2]` | stmt | Call a defined `@macro` |

```clpy
@retry[3]
    risky_call()
@end

@retry[5; requests.Timeout]
    @var[data; @http.get["https://api.example.com"]]
@end

@timeout[10]
    @var[result; slow_operation()]
@end

@macro[greet; name]
    @print[Hello, {name}!]
@end
@call[greet; "Alice"]
```

### 4 new stdlib namespaces

| Namespace | Wraps | Highlights |
|---|---|---|
| `@re.*` | `re` | `match`, `search`, `fullmatch`, `findall`, `finditer`, `sub`, `subn`, `split`, `compile`, `escape`, `is_match`, `groups`, `group1`, `named`, `count`, `replace_first` |
| `@yaml.*` | `PyYAML` | `loads`, `dumps`, `load_file`, `dump_file`, `parse`, `stringify`, `get`, `to_json`, `from_json` |
| `@image.*` | `Pillow` | `open`, `new`, `save`, `resize`, `rotate`, `crop`, `convert`, `size`, `width`, `height`, `thumbnail`, `flip_h`, `flip_v`, `grayscale`, `show`, `format`, `to_bytes`, `paste` |
| `@pdf.*` | `pdfplumber` | `open`, `pages`, `page_count`, `text`, `text_of`, `words`, `tables`, `table_of`, `metadata`, `lines` |

```clpy
@var[m; @re.search["(\d+)"; "order 42"]]
@var[n; @re.group1[m]]   # "42"

@var[data; @yaml.loads["name: Alice\nage: 30"]]
@var[name; @yaml.get[data; "name"]]

@var[img; @image.open["photo.png"]]
@var[thumb; @image.thumbnail[img; 128; 128]]
@image.save[thumb; "thumb.png"]

@var[doc; @pdf.open["report.pdf"]]
@var[txt; @pdf.text[doc]]
```

### 3 new CLI commands

| Command | Description |
|---|---|
| `cruhon lint file.clpy` | Static analysis — style warnings without running |
| `cruhon test` | Run `cruhon/tests/` (or a specified directory) |
| `cruhon bundle file.clpy -o out.py` | Bundle `.clpy` + all includes into a single `.py` |

### cruhon-shortcuts-pro: 3 new groups

- **regex group** — `@re_match`, `@re_find`, `@re_sub`, `@re_split`, `@re_groups`, `@re_named`, `@re_count`, `@is_match`, `@replace_first`
- **http group** — `@retry_get`, `@bearer`, `@json_post`, `@put_json`, `@patch_json`, `@del_req`, `@http_ok`, `@http_status_text`, `@multipart_post`, `@stream_get`
- **file group** — `@read_file`, `@write_file`, `@file_find`, `@joinpath`, `@file_ext`, `@file_stem`, `@file_size`, `@file_modified`, `@is_file`, `@is_dir`, `@file_lines`, `@file_words`

### Tests: **1442** (+41 from v2.4.0)

---

## v2.4.0 — Data & Format Namespaces & cruhon-shortcuts-data

### 10 new stdlib namespaces

All standard-library backed — no `@import` needed, fully sandboxed codegen.

| Namespace      | Wraps                  | Highlights |
|----------------|------------------------|-----------|
| `@xml.*`       | `xml.etree.ElementTree`| `parse`, `from_string`, `find`, `find_all`, `find_text`, `to_dict`, `attrib`, `children`, `count` |
| `@toml.*`      | `tomllib`              | `loads`, `load`, `get`, `keys`, `has` (read-only) |
| `@diff.*`      | `difflib`              | `ratio`, `is_similar`, `unified`, `context`, `ndiff`, `lines`, `close_matches`, `best_match` |
| `@decimal.*`   | `decimal`              | exact base-10: `make`, `add/sub/mul/div`, `round`, `quantize`, `sum`, `sqrt`, `compare` |
| `@fraction.*`  | `fractions`            | exact rationals: `make`, `from_float`, `add/sub/mul/div`, `numerator`, `denominator`, `limit` |
| `@ip.*`        | `ipaddress`            | `address`, `network`, `is_private/global/loopback`, `version`, `hosts`, `num_addresses`, `contains` |
| `@platform.*`  | `platform`             | `system`, `release`, `machine`, `python_version`, `is_windows/linux/mac`, `is_64bit`, `uname` |
| `@unicode.*`   | `unicodedata`          | `name`, `lookup`, `category`, `numeric`, `normalize`, `nfc/nfd/nfkc/nfkd`, `strip_accents` |
| `@binascii.*`  | `binascii`             | `hexlify`, `unhexlify`, `b2a_base64`, `a2b_base64`, `crc32`, `crc_hqx` |
| `@shlex.*`     | `shlex`                | `split`, `join`, `quote`, `quote_all` |

Note: `@decimal.add["0.1"; "0.2"]` returns exactly `0.3` — no binary
floating-point error.

### `cruhon-shortcuts-data` plugin

A third configurable shortcut plugin (`mods/cruhon-shortcuts-data/`,
6 files, 3 groups) covering the new namespaces. Loads cleanly alongside
`cruhon-shortcuts` and `cruhon-shortcuts-pro` — all rewrite names distinct.

- **format group** — `@xml_parse`, `@xml_load`, `@xml_dict`, `@xml_text`,
  `@toml_load`, `@toml_get`, `@diff_ratio`, `@similar`, `@closest`,
  `@fuzzy`, plus `@xml.text_all`, `@xml.attr_all`, `@diff.changed`,
  `@toml.flatten`
- **numbers group** — `@dec_of`, `@dec_add`, `@dec_round`, `@money`,
  `@frac`, `@frac_str`, `@frac_add`, plus `@decimal.money`,
  `@decimal.percent`, `@decimal.average`, `@fraction.as_percent`,
  `@fraction.reciprocal`
- **system group** — `@ip_addr`, `@is_private_ip`, `@ip_hosts`,
  `@os_name`, `@py_version`, `@machine`, `@hostname`, `@char_name`,
  `@strip_accents`, `@hexlify`, `@unhexlify`, `@sh_split`, `@sh_quote`,
  plus `@ip.is_ipv4/is_ipv6`, `@ip.first_host`, `@platform.summary`,
  `@binascii.hex_spaced`

### Tests: **1401** (+85 from v2.3.0)

---

## v2.3.0 — Full Namespace Expansion & cruhon-shortcuts-pro

### Fully expanded 5 stdlib namespaces

All five namespaces added in v2.2 now have comprehensive method coverage:

**`@string.*`** — new char utilities and random generators:
`ascii_to_int`, `int_to_ascii`, `filter`, `exclude`, `count_in`,
`maketrans`, `translate`, `random_lower`, `random_upper`,
`random_digits_str`, `formatter`

**`@struct.*`** — new convenience methods:
`unpack_list`, `first`, `pad`, `byte_order`, `to_hex`,
`from_hex_str`, `native`

**`@zlib.*`** — base64 wrappers and utilities:
`compress_b64`, `decompress_b64`, `compress_str`, `decompress_str`,
`adler32_hex`, `saved_bytes`, `is_zlib`

**`@calendar.*`** — weekday checks and navigation:
`is_weekday`, `is_weekend`, `first_weekday_of`, `day_of_year`,
`week_of_year`, `year_text`, `quarter`, `next_month`, `prev_month`,
`get_first_weekday`

**`@email.*`** — header getters, setters, and attachment helpers:
`cc`, `bcc`, `reply_to`, `date_header`, `message_id`, `content_type`,
`to_bytes`, `html_body`, `attach_text`, `attach_bytes`,
`all_attachments`, `set_cc`, `set_bcc`, `set_reply_to`, `address_list`

### `cruhon-shortcuts-pro` plugin

A second configurable shortcut plugin (`mods/cruhon-shortcuts-pro/`,
7 files) with 5 domain groups. Loads alongside `cruhon-shortcuts`
without conflicts — all global-rewrite names are distinct.

- **math group** — `@clamp`, `@lerp`, `@sign`, `@round_to`, `@percent`,
  `@frange`, `@log2`, `@log10`, `@gcd`, `@lcm`, `@factorial`, `@hypot`,
  `@sin`, `@cos`, `@tan`, `@degrees`, `@radians`, `@is_close`, plus
  `@math.inf`, `@math.e`, `@math.tau`, `@math.nan`, `@math.is_nan`, …

- **lists group** — `@window`, `@transpose`, `@unzip`, `@rotate_list`,
  `@head_n`, `@tail_n`, `@interleave`, `@dedupe`, `@flat`, `@zip_all`,
  `@cartesian`, `@chunks`, `@sorted_by`, `@pairs`, `@take_while`,
  `@drop_while`, plus `collections.sum_of`, `collections.min_by/max_by`,
  `collections.avg_of`, `collections.enumerate_from`

- **dicts group** — `@pick_keys`, `@omit_keys`, `@map_vals`,
  `@filter_keys`, `@deep_merge`, `@dict_diff`, `@flat_dict`,
  `@unflatten_dict`, `@swap_kv`, `@rename_key`, `@key_of`,
  `@values_where`, `@dict_product`

- **text group** — `@camel_case`, `@snake_case`, `@kebab_case`,
  `@pascal_case`, `@word_freq`, `@normalize_ws`, `@excerpt`, `@initials`,
  `@squeeze`, `@ordinal`, `@pluralize`, `@de_accent`, `@wrap_lines`,
  `@sentence_count`, `@char_freq`, `@longest_word`, `@shortest_word`,
  plus `text.pad_center`, `text.mirror`

- **logic group** — `@coalesce`, `@first_true`, `@count_if`,
  `@any_match`, `@all_match`, `@none_match`, `@first_where`,
  `@last_where`, `@default_if_none`, `@safe_get`, `@unless_empty`,
  `@one_of`, `@not_in`, `@index_of`, `@find_all`, `@group_by`, `@tally`

### `cruhon-shortcuts` binary group expanded

Added 17 more global aliases and 13 more method aliases covering the
newly added core methods (`@is_weekday`, `@is_weekend`, `@day_of_year`,
`@week_of_year`, `@next_month`, `@prev_month`, `@compress_b64`,
`@compress_str`, `@adler32_hex`, `@ascii_to_int`, `@rnd_lower`, etc.).

### Tests: **1316** (+45 from v2.2.0)

---

## v2.2.0 — Shortcut Plugin & 5 New Namespaces

### `cruhon-shortcuts` plugin

A new bundled plugin (`mods/cruhon-shortcuts/`, 14 files) that adds a fully
configurable shortcut layer over every namespace:

- **Global aliases** via a `before_parse` rewrite hook — `@read` →
  `@file.read`, `@now` → `@date.now`, `@uuid` → `@crypto.uuid`, `@rand` →
  `@random.randint`, `@mean` → `@statistics.mean`, and hundreds more.
- **Method aliases** — `@file.cat`, `@file.ls`, `@date.ts`, `@http.fetch`,
  `@itertools.flat`, `@statistics.avg`, etc.
- **200+ new convenience methods** registered via `api.lib_call()` —
  `@file.head/tail/grep/wc/sha256_file`, `@date.tomorrow/yesterday/age/quarter`,
  `@random.roll/flip/password/alphanumeric`, `@collections.histogram/window`,
  `@statistics.summary/normalize/zscore`, `@text.camel_to_snake`,
  `@string.random`, `@struct.hexdump`, and more.

Configuration (`mod.json`): `groups` (`"all"` or a subset of 13 groups),
`global_aliases`, `method_aliases`, `disabled`, and `custom` rewrites.

### 5 new core stdlib namespaces

Added to back the shortcut plugin (no `@import` needed):

- **`@string.*`** — character-class constants, `Template` substitution, `capwords`.
- **`@struct.*`** — binary `pack`/`unpack`, `calcsize`, compiled `Struct`.
- **`@zlib.*`** — `compress`/`decompress`, `crc32`/`crc32_hex`, `adler32`.
- **`@calendar.*`** — `is_leap`, `days_in_month`, `weekday`, month/day names.
- **`@email.*`** — build, parse, and inspect MIME messages; address utilities.

### Tests

Suite grows to **1271** tests (24 new for the 5 namespaces).

---

## v2.1.0 — Diagnostics, More Stdlib, Plugin Freedom

### Rich, readable diagnostics

Cruhon now reports errors more clearly than Python. Every error shows the
error type, the Cruhon line it maps to, a source excerpt with surrounding
context, a caret (`^^^`) under the offending token, a plain-language hint,
and a "did you mean …?" spelling suggestion.

- New module `cruhon/core/diagnostics.py` — single source of truth for error
  rendering (used by the lexer, parser, transpiler, runner, and CLI).
- `_diagnose()` covers many runtime error types (NameError, TypeError,
  AttributeError, KeyError, IndexError, ZeroDivisionError, ValueError,
  FileNotFoundError, PermissionError, ModuleNotFoundError, RecursionError,
  AssertionError) with readable, actionable hints.
- `cruhon check` and `cruhon run` print rich, colored error excerpts.
  Color auto-disables for pipes, files, and `NO_COLOR`.

### Diagnostic logging to a file (opt-in, no code changes)

Route Cruhon's own diagnostics to a log file via environment variables or a
CLI flag — no script changes required:

- `CRUHON_LOG=cruhon.log` (or `CRUHON_LOG=1` → `./cruhon.log`)
- `CRUHON_LOG_LEVEL=DEBUG|INFO|WARNING|ERROR` (default `INFO`)
- `cruhon run file.clpy --log cruhon.log --log-level DEBUG`

At `DEBUG` the log captures the source, the generated Python, run timings,
and the full diagnostic plus Python traceback for every run. This is separate
from the `@log.*` library, which is for a *script's own* application logging.

### Standard library: 20 new namespaces

`@random` `@collections` `@itertools` `@functools` `@sys` `@io` `@copy`
`@base64` `@url` `@statistics` `@contextlib` `@enum` `@dataclasses`
`@typing` `@threading` `@queue` `@heapq` `@bisect` `@operator` `@pprint`.

### Plugin / mod system freedom and correctness

- `api.override()` now maps all 40+ node types correctly (CamelCase fallback
  fixed — `async_for` → `AsyncForNode`, previously a silent no-op).
- `api.inject_once()` — evaluate a factory once at registration for
  connection pools / singletons (vs. per-run `api.inject()`).
- `api.unregister_command()`, `remove_hook()`, `remove_inject()`,
  `remove_eval_hook()` — clean teardown for testing and conditional loading.
- `on_error` hook now fires for `ParseError` / `RunError` too.
- `after_run` hook now receives `source=` and `python_code=`.
- Pip mods: version compatibility check (`CRUHON_REQUIRES` / `Requires-Dist`)
  and `api.config()` support via a `CRUHON_CONFIG` dict.
- Full tracebacks printed when a mod's `register()` fails.

### Tests

Suite grows to **1247** passing (was 1083 at the start of the v2.1 cycle).

---

## v2.0.0 — Standard Library Completion

### Standard Library: 13 namespaces, 500+ commands

**Full Python parity without `@raw`.** Every Python stdlib operation has a Cruhon shortcut:

#### New namespaces (Groups 1–4)

- **`@file`** (Group 1) — 40+ commands: read/write/append with encoding, touch, chmod, symlink, hardlink, is_link, stat, realpath, samefile, expanduser, and more
- **`@date`** (Group 1) — 30+ commands: datetime/date/time/calendar/zoneinfo, timezone (ZoneInfo), UTC constant, ISO calendar, to_timezone
- **`@text`** (Group 2) — 54 commands: case, trim, split, partition, rsplit, encode/decode, regex (with flags), translate/maketrans, slug, clean
- **`@http`** (Group 2) — 37+ commands: sync + async, upload (multipart), auth_get/auth_post, elapsed, encoding, session management
- **`@csv`** (Group 2) — 12 commands: read, write, filter, to_json
- **`@crypto`** (Group 3) — 25+ commands: hash (SHA3, BLAKE2), hmac, token, UUID, base64, pbkdf2, scrypt, hash_file
- **`@log`** (Group 3) — 15 commands: setup, file handlers, levels, formatters, get/child loggers, disable/enable
- **`@config`** (Group 3) — 15 commands: load/save (JSON/TOML/INI/.env), get/set, sections, keys, env vars, dotenv
- **`@shell`** (Group 4) — 32 commands: run, output, lines, code, bg, kill, terminate, wait, communicate, poll, env, cpu_count, hostname, username, home
- **`@archive`** (Group 4) — 18 commands: zip/unzip, tar/untar, gzip/gunzip, bzip2/bunzip2, lzma/unlzma, inspect
- **`@mail`** (Group 4) — 17 commands: send (plain/HTML/attachment), SMTP, IMAP (connect, list, select, search, fetch), parse

#### Design

- **No @raw required** — all 5 groups 100% cover Python stdlib, no gaps
- **Python-level freedom** — `@import[X]` for any stdlib module, `@raw` blocks for everything else
- **Encoding support** — file read/write with custom encoding parameter
- **Timezone support** — `@date.timezone` (ZoneInfo), `@date.to_timezone`, `@date.utc` constant
- **Key derivation** — `@crypto.pbkdf2`, `@crypto.scrypt` for password security
- **Compression formats** — zip, tar, gzip, bzip2, lzma/xz
- **IMAP/POP3** — receive emails: `@mail.imap_*`
- **Process control** — kill, terminate, wait, communicate for subprocess management

#### Test coverage

- 778 tests passing (714 existing + 64 new)
- Groups 1–4 fully tested: `test_file_date.py`, `test_text_http_csv.py`, `test_crypto_log_config.py`, `test_shell_archive_mail.py`, `test_gap_fill.py`
- No @raw escapes required in test suite

#### Documentation

- Updated `library.md` with all 13 namespaces and 500+ commands
- Updated `README.md` with v2.0.0 standard library reference
- Updated `pyproject.toml` version

---

## v1.6.0

### Module System — Real Encapsulation

- **`@module[name] ... @end`** — block module with its own isolated scope. Inner variables never leak; only exported symbols are accessible from outside.
- **`@export[name1; name2; ...]`** — explicit visibility control. `@export[*]` or no `@export` → all non-private names public. Private convention: `_underscore` prefix.
- **`@use[path]`** / **`@use[path as alias]`** — load a `.clpy` file as a module. Searches current dir then `modules/` subdirectory. Circular dependency detection.
- **`@from[module; name1; name2 as alias; ...]`** — selective import from a module into local scope.
- **`@module.method[args]`** — namespace call syntax works for user modules (routes to `module.method(args)` instead of runtime mod dispatch).
- **`@include` unchanged** — legacy compile-time flatten, fully backward compatible.
- **Plugin compatibility** — all v1.5.0 APIs (`api.inject`, `api.eval_hook`, `api.ast_hook`, `api.block_command`, etc.) work transparently inside module bodies. Injected globals are visible within module init functions via exec() scope.
- **f-string template detection improved** — `{func()}` and `{obj.method()}` patterns now correctly recognized as f-string interpolation in display context. `{expr + op}` fallthrough in display context wraps as f-string.
- Test suite: 210 → 237 tests (`TestModuleBlock`, `TestModuleFrom`, `TestModuleFile`, `TestModulePluginCompat`)

---

## v1.5.0

### Plugin Freedom — Runtime Injection, Inline Commands, Eval Hooks

- **`api.inject(key, value_or_factory)`** — injects values/objects into exec() globals; scripts access them directly by name. Callable factories are called before each exec(), static values are used as-is.
- **`api.inline_command(name, handler_fn)`** — registers inline expression commands (`@var[x; @uuid[]]`, `@var[t; @now[]]`). `handler_fn(parser) → str` consumes tokens and returns a Python expression string.
- **`api.eval_hook(fn)`** — hooks into `_eval_value()` at transpile-time. `fn(value, context) → str | None`; return a Python expression to override default evaluation, `None` to pass through.
- `get_inject_globals()` public function — resolves all inject providers to a dict
- Test suite: 194 → 210 tests (`TestInject`, `TestInlineCommand`, `TestEvalHook`)

---

## v1.4.0

### Plugin System Hardening

- **`api.ast_hook(node_type, fn)`** — parse-time AST hook; `fn(node) → node` fires on every matching node after parse, before transpile. Plugins can inspect, mutate, or replace any AST node.
- **`@async.for[var; iterable] ... @end`** — async iteration inside `@async func` blocks
- **`@async.with[expr as var] ... @end`** — async context manager
- **Plugin error attribution** — `api.command()` visitors now include the owning plugin name in error messages
- **`list_block_commands()`** — returns `{plugin_name: [cmd, ...]}` for all registered block commands
- **`cruhon mods` enrichment** — now shows Exposed APIs and Plugin block commands sections
- **`cruhon new --plugin <name>`** — scaffolds `mods/<name>/mod.json` + `__init__.py` with register skeleton
- Test suite: 172 → 194 tests (`TestAsyncFor`, `TestAsyncWith`, `TestAsyncForWithRun`, `TestAstHooks`, `TestModEnrichment`, `TestVisitorOwner`)

---

## v1.3.0

### Language Completion

- **`@with[expr as var] ... @end`** — context manager block; `with open(...) as f:` is now Cruhon syntax
- **`@match[value] / @case[pattern] / @default`** — Python 3.10+ pattern matching
- **`@del[var1; var2]`** — delete variables
- **`@raise[ExceptionType; msg]`** / **`@raise`** (bare re-raise) — explicit exception raising
- **Multi-line fix** — `parse_args` now skips INDENT/DEDENT/COMMENT tokens; multi-line expressions inside parentheses work
- Test suite: 156 → 172 tests (`TestWith`, `TestMatch`, `TestDel`, `TestRaise`, `TestMultiLine`)

---

## v1.2.0

### Plugin System — Scope, Transforms, Block Hooks

- **`api.block_command(..., scoped=True)`** — `__ctx__` auto save/restore; changes inside the block don't leak out
- **`@ctx.push[]` / `@ctx.pop[]`** — manual stack-based ctx scope (for nested blocks)
- **`api.transform(target, fn)`** — wrap another plugin's block output with fn(transpiler, node, code)
- **`api.block_hook("enter" | "exit", fn)`** — runtime block lifecycle: fn(plugin_name, args) fires on every block enter/exit
- `__ctx_stack__` and `__ph__` injected into exec namespace
- Test suite: 149 → 156 tests

---

## v1.1.0

### Plugin Foundation System

- **`api.expose(key, value)`** — Plugin publishes an API/utility for other plugins
- **`api.consume(plugin, key)`** — Consume what another plugin published; supports defaults
- **`api.is_loaded(name)`** — Check if a plugin is loaded (bool)
- **`api.config(key, default)`** — Read data from the plugin's own `mod.json` manifest
- **Version-aware dependency** — `require("cruhon-utils >= 1.2.0")` actually checks version constraints
- **Error attribution** — Errors from plugin visitors show the plugin name
- **`list_exposed_apis()`** — List all published plugin APIs

### Testing

- Test suite: 139 → 150 tests
- New: `TestPluginFoundation`

---

## v1.0.0

### New Features

- **Named parameters** — `@command[pos1; pos2; key=value]` syntax.  
  `parse_named_args()` returns `(positional_list, kwargs_dict)`.  
  `split_named_args()` added to `SyntaxEngine`.

- **Friendly error hints** — runtime errors now include actionable hints:
  - `NameError` → suggests adding quotes if the name looks like a string
  - `ZeroDivisionError`, `IndexError`, `KeyError`, `TypeError`, `AttributeError` — each gets a specific message

- **Block plugin commands** — `api.block_command("name", visitor_fn)` registers a block that opens with `@name[...]`, contains a body, and closes with `@end`.  
  No custom AST node class needed — body lands in `PluginBlockNode`.  
  Plugin visitors receive `node.args`, `node.kwargs`, `node.body`.

- **Context variables** — lightweight `__ctx__` dict for plugin→code data passing:
  - `@ctx["key"]` / `@ctx["key"; default]` — read context (inline expression)
  - `@ctx.set["key"; value]` — write context at runtime
  - `@ctx.get["key"]` / `@ctx.clear[]` / `@ctx.delete["key"]` — full dict API
  - Plugins emit `__ctx__["key"] = value` before running block bodies

### New APIs

- `PluginBlockNode(plugin_name, args, kwargs, body)` — generic block node
- `Parser.parse_plugin_block(name)` — parse args + body + `@end` in one call
- `Transpiler._block_visitors` — dict for per-plugin block dispatch
- `ModAPI.block_command(name, visitor_fn)` — one-line block command registration

### Testing

- Test suite expanded from 117 → 139 tests
- New: `TestNamedArgs`, `TestHints`, `TestBlockPlugin`, `TestContextVars`

---

## v0.9.2

- Namespace conflict resolution: first registrant wins, second gets existing namespace back
- Path traversal guard in `@file.*` and `@json.read/write`
- HTTP `timeout=30` on all sync requests
- SSRF guard in `@http.*` (blocks private/loopback addresses)
- Version consistency across all files
- English documentation

**Bug fixes in this release:**
- `@raw` block parsing: INDENT/DEDENT tokens correctly handled before `@end`
- `@input` command fully implemented (was defined in AST but missing from parser and transpiler)
- Unknown inline commands now raise `ParseError` instead of silently returning `None`
- Indirect circular `@include` detection fixed (A→B→C→A now caught, not only A→B→A)
- `examples/hello.clpy` corrected: string literals must be quoted in expr context
- `pyproject.toml` build backend updated for setuptools 82+

---

## v0.9.1

- `@raw` blocks implemented (parser, ast_nodes, transpiler)
- Dict literal false positive fixed in `_eval_value` (`_is_python_expression` / `_is_fstring_template` helpers added)

---

## v0.9.0

- Minimal async runtime: runner detects `async def main` and appends `asyncio.run()`
- `@http.async_get`, `@http.async_post`, `@http.async_json` via httpx

---

## v0.9.0a1

- Namespace isolation: `access_state` / `write_state` / `allow_peer`

---

## v0.8.0

- Namespace runtime system
- `NamespaceCallNode`
- `ModAPI.namespace()` / `require()`
- `DependencyResolver`
- `__ns__` injected into `exec()`
- Example Discord mod

---

## v0.7.0

- Stdlib: `@file`, `@time`, `@math`, `@json`, `@color`
- SyntaxWarning fix

---

## v0.6.0

- `SyntaxEngine`: unified argument parsing
- Fixed list/dict literals in `@var`
- `spec/architecture.md`

---

## v0.5.0

- Semantic stabilization: unified `_eval_value`
- `;` enforcement
- `spec/semantics.md`
- Line map fix

---

## v0.4.0

- All missing commands
- `@http.*`, `@store.*`
- Inline `@commands`
- Auto-imports
- Line numbers in errors

---

## v0.3.0

- Deterministic plugin loader
- Middleware override chain
- `--show-python`
- Version compatibility checks

---

## v0.2.0

- Bug fixes
- `@const`, `@env`, `@include`, `@assert`, `@list`, `@dict`

---

## v0.1.0

- MVP: lexer, parser, transpiler, runner, mod system, CLI
