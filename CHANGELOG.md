# Changelog

All notable changes are documented here.

---

## v2.2.0 (current) — Shortcut Plugin & 5 New Namespaces

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
