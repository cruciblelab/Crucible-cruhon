# Changelog

All notable changes are documented here.

---

## v2.10.2 (current) — Discord cog commands were crashing at load time

Building a comprehensive, modular test bot (6 files: moderation, fun,
utility, server management, welcome/automod, logging — each a
`@discord.cog[...]`, wired together with `@include`) surfaced a severe
bug: `@discord.command`/`@discord.hybrid`/`@discord.slash` **inside a
`@discord.cog[...]` block** rendered through `_render_cog_method` — a
separate, drifted reimplementation of the top-level command renderers
that never received the `_typed_param()` fix from the previous release.
`@discord.command[ban; ctx; member:member]` inside a cog produced the
literal, broken signature `async def ban(self, ctx, member:member):` —
`member` used as its own type annotation, referencing a name that
doesn't exist. Since annotations are evaluated at class-definition
time, this isn't a runtime edge case: the entire bot crashes with
`NameError` the moment the file is imported, before it can even try to
log in.

`@discord.slash[...]` inside a cog was worse — it never parsed
`@param[...]`/`@choice[...]` sub-blocks at all (a completely separate
gap from the typed-param one), so a parameter declared via `@param[...]`
was silently dropped from both the function signature and Discord's
command schema, while the `@param[...]` line itself rendered as a dead
`# @_dc_param block (no visitor registered)` comment.

Neither bug was caught by the existing test suite because every cog
test only ran the output through `compile()` (a syntax check) —
`member:member` and a missing-but-unused parameter are both
syntactically valid Python; only executing the code raises the
NameError. Found by actually `exec()`-ing a full multi-cog bot against
a real installed `discord.py`, not just checking it compiles.

**Fix:** rewrote `_render_cog_method`'s command/hybrid/slash branches to
match the top-level renderers exactly — extra params go through
`_typed_param()`, and slash commands get full `_parse_slash_config()`
handling (typed params, `@describe`, `@choice`, `@autocomplete`) instead
of a stripped-down reimplementation. 6 new regression tests, including
one that `exec()`s a real multi-cog bot end-to-end with discord.py
installed — the same bar that caught the bug in the first place, not
just a `compile()` check. Full suite: 6210-6211 passed on Python
3.10/3.11/3.12.

## v2.10.1 — CI green, Python 3.10 compatibility, real-bot fixes

The 2.10.0 release commits were pushed without anyone checking the GitHub
Actions tab — CI had been failing on every single push since the Tests
workflow was added, for four unrelated reasons. All fixed and verified
directly against Python 3.10/3.11/3.12 interpreters (not just this
sandbox's default), plus the actual sdist+wheel build and `twine check`
steps CI runs.

**Test suite: locale-dependent UnicodeDecodeError.** `cruhon bundle`
writes its output with `encoding="utf-8"` (its header comment has an
em dash), but two tests read it back with a bare `.read_text()` — no
encoding, so it falls back to the platform's locale-preferred encoding,
which is ASCII on the GitHub Actions runner. Fixed those two tests, then
swept the whole suite for the same latent pattern (bare `.read_text()`
with no explicit encoding) and pinned all of them to `encoding="utf-8"`.
Verified against the exact CI failure by reproducing it locally with
`LC_ALL=C LANG=C PYTHONUTF8=0`.

**`@toml.*` was broken on Python 3.10.** `tomllib` is stdlib only since
Python 3.11 — Cruhon's `pyproject.toml` claims `requires-python = ">=3.10"`,
but every `@toml.*`/`@toml_load` call unconditionally did
`__import__('tomllib')`, so anything using it crashed with
`ModuleNotFoundError` on 3.10. Added a `_get_tomllib()` fallback (tomllib
→ tomli backport, same pattern `@config.load` already used for `.toml`
files) in both `cruhon/core/libs/toml_.py` and the duplicate `_TL`
constant in `cruhon-shortcuts-data/data_format.py`'s `@toml.flatten`.
Declared `tomli>=2.0; python_version < "3.11"` as a real dependency in
`pyproject.toml` so it installs automatically where it's needed.

**`@pickle.save_gz` could write a truncated file.** It did
`gzip.open(path, 'wb').write(data)` with no explicit `.close()` — gzip's
CRC32/size trailer is only written on close, and relying on GC
finalization timing to call it is not guaranteed across Python versions.
On Python 3.12 a `@pickle.load_gz` immediately after a `@pickle.save_gz`
could read a file missing its trailer and fail with `EOFError: Ran out
of input`. Fixed by closing the GzipFile explicitly.

**A test used a Python-3.10-specific interpreter quirk as its example.**
`TestRunpy::test_module_ns` used `@runpy.module_ns["os.path"]` — on
Python 3.10, `os.path` is aliased to `posixpath`/`ntpath` internally, and
`runpy.run_module` chokes on that aliasing with `ImportError: loader for
posixpath cannot handle os.path`. This is a genuine CPython 3.10 quirk
unrelated to Cruhon's `@runpy.*` wrapper (which just calls
`runpy.run_module` correctly) — switched the test to `urllib.parse`,
a plain dotted submodule that exercises the same code path without the
aliasing issue.

Also includes the Discord plugin fixes below (interpolation, variable
passthrough, typed prefix-command params), found and fixed by building
and live-testing a real Discord bot. Full suite verified at 6204-6205
passed (count varies slightly by Python version due to environment-gated
skips) on 3.10, 3.11, and 3.12, plus a clean `python -m build` +
`twine check`.

## v2.10.0 — Config & Secrets, Env-aware DB, Live Panel

### Discord plugin — typed prefix-command params (live-bot bug)

Running the demo bot above against a real Discord server surfaced a
second real bug: `@discord.command[ban; ctx; member]`'s extra params
(`member`, `count`, `minutes`, ...) had no way to be typed, so
discord.py always passed them as the raw text the user typed —
`!ban @someone` gave `member` the literal mention *string*, never a
resolved `discord.Member`. `member.ban()` then crashed with
`AttributeError: 'str' object has no attribute 'ban'`, silently, since
nothing was listening for `on_command_error` — the command author saw
nothing happen in Discord at all, only a traceback in the bot's own
console. Same failure mode for `!purge <count>` (`channel.purge(limit="10")`)
and `!timeoutuser <member> <minutes>` (`timedelta(minutes="5")`).

**Fix:** extra params on `@discord.command`/`@discord.hybrid` now accept
`name:type` (reusing the same type names as slash `@param[...]` — member,
user, int, float, bool, channel, role, ...), e.g.
`@discord.command[ban; ctx; member:member]` → `async def ban(ctx, member:
discord.Member):`, letting discord.py resolve/convert before the command
body runs. Untyped params are unchanged (still plain strings). Also added
a global `@discord.on[error; ctx; error]` handler to the demo bot so
future command failures reply in Discord instead of vanishing into the
console, and exempted anyone with Manage Messages from the profanity
filter (it was deleting moderators' own messages during testing). 8 new
regression tests (`TestTypedPrefixParams`). Full suite: 6204 passed.

### Discord plugin hardening — `{}` interpolation and variable passthrough

Built a real Discord bot in Cruhon (webhooks, roles, channel management,
a profanity filter, native AutoMod, moderation commands) to dogfood
`cruhon-discord`, then inspected the transpiled Python by eye line by
line — no `discord.py`/network access in this environment, so this was
verified as far as "generates correct Python," not "runs against a real
Discord server." Inspection surfaced that the plugin's own text-argument
helper, `_as_str()`, was far weaker than core's value-evaluation engine:
it never upgraded a quoted string containing `{}` to an f-string, and it
`repr()`-wrapped every bare (unquoted) argument regardless of whether it
was meant as literal display text or as a reference to the caller's own
variable.

**`{}` interpolation was silently dropped everywhere.** `@discord.reply`,
`send`, `dm`, `respond`, `followup`, `edit`, `log`, `send_tts`,
`respond_ephemeral`, `send_webhook`, `confirm`, `status`, and every embed
field (`title`, `description`, `add_field`, `set_footer`, `set_image`,
`set_thumbnail`, `set_author`) took their text argument as raw source
text — `"Banned by {ctx.author}"` came out as the literal string
`"Banned by {ctx.author}"`, never an f-string. This is the single
highest-impact bug found in the plugin, since almost every real bot
reply needs dynamic content.

**Bare variable arguments were stringified into their own name.**
`@discord.create_webhook[ctx.channel; name]` produced `name='name'`
instead of `name=name` — any unquoted argument was always `repr()`-
wrapped, with no way to tell "the user typed a bare word as literal
text" from "the user typed an identifier meaning a variable." Same bug
in `create_role`'s `name`, `get_role`/`find_member`'s lookup `name`,
`nickname`'s `nick`, and the `reason=` kwargs on `ban`/`kick`/`unban`.

**`@discord.color[a_variable]` called a nonexistent method** —
`discord.Color.hex_color()` — because any identifier-shaped argument was
treated as a named-color shortcut (correct for `@discord.color[red]`,
wrong for a variable that merely happens to also be a valid identifier).
Fixed with a fixed 36-name `_COLOR_NAMES` set for genuine shortcuts, plus
a new runtime helper `__discord_color__` that resolves a variable's
actual value (hex string / int / named-color string / already a
`discord.Color`) at bot runtime, since the transpiler can't know the
type at compile time.

**Fix:** rewrote `_as_str()` to (1) upgrade `"quoted {text}"` to an
f-string when it contains braces, and (2) detect real Python-expression
arguments — via `ast.parse(arg, mode="eval")`, so arbitrarily nested
expressions like `str(ctx.guild.created_at.date())` or
`any(w in content for w in banned_words)` pass through correctly, not
just simple `a.b.c` chains — and only fall back to `repr()` for genuine
non-coder prose that isn't valid Python. Wired all ~30 affected handlers
to route their text arguments through the fixed helper. One call site
(`@choice[Label=value]` inside `@discord.slash`) intentionally keeps
`repr()` directly instead, since a choice label is always literal text
by the DSL's own grammar, never a variable reference. Added 22
regression tests (`TestTextArgHardening`) covering interpolation across
every affected handler, variable passthrough for webhook/role/channel
names, the color-from-variable runtime path, and the literal-text
fallback. Full suite: 6196 passed, 0 regressions.

### Second hardening pass — duplicates, security, coverage, performance

A broader sweep beyond the doc/registry audit above: conflicting
registrations, a missing safe subprocess path, untested namespaces, and
scaling checks.

**Duplicate/conflicting registration scan.** Statically found every
`register_lib_call`/`api.lib_call` call site across core + all `mods/`
and grouped by `(namespace, method)`. 19 keys are registered from more
than one file. Reviewed each: `@math.*` (18 keys) legitimately duplicates
between core and `cruhon-shortcuts-pro`'s `pro_math.py` — functionally
equivalent, and mods overriding core is the plugin system working
exactly as designed (documented load order: core → pip mods → local
mods), not a bug. `@collections.deque_rotate`/`@csv.headers`/
`@file.line_count` diverge slightly (a plugin's version is more
defensive about edge cases) — also fine, same reasoning. No fix needed;
noted for awareness.

**No safe way to run a subprocess without `shell=True`.** Every
`@shell.*` command (`run`, `output`, `lines`, `code`, `ok`, `bg`,
`bg_stdin`) passed a string through `subprocess.run(cmd, shell=True,
...)` — exactly the same shell-metacharacter injection surface as
`os.system()` in plain Python, with no argv-list alternative. A script
author who wanted to safely run a command built from partially-untrusted
data (a filename from `@input`, a value from an HTTP response) had to
drop to `@raw` + `import subprocess` — contradicting the project's own
"nothing should need `@raw` to escape into real Python" goal. Added
`@shell.exec[argv]`/`exec_output`/`exec_code`/`exec_ok`/`exec_bg` — the
same five operations, but taking an argv list and never invoking a
shell. Verified the actual safety difference with a real injection
payload: the same string interpreted by `@shell.output` (two lines of
output, `&&` ran a second command) stays one inert, literal argument
under `@shell.exec_output`.

**Security spot-checks that came back clean** (worth recording, not
just silence): `@db.query[sql; params...]` correctly uses parameterized
placeholders — an injection payload passed as a bound parameter matches
zero rows rather than altering the query. Cruhon's own "quoted string
containing `{}` → f-string" behavior only ever applies to literal source
text the script author wrote, never to runtime data that happens to
contain brace characters — external/untrusted values can't retroactively
become executable code through that path. No `os.system`/`os.popen`/
`shell=True` found outside `@shell.*`'s own (now-optional) string-command
path.

**Coverage audit: which namespaces had zero execution tests?** Five —
`@contextlib.*`, `@dataclasses.*`, `@enum.*`, `@env.*`, `@typing.*` (71
methods, previously exercised only by the generic compile-only safety
net, never actually run). Writing real tests for all five surfaced one
more bug: `@enum.Enum["Color"; "RED GREEN BLUE"]` silently discarded
both arguments and returned the bare `enum.Enum` class — Python's own
`Enum` behaves differently when *called* with args (constructs a new
enum) vs. referenced bare (the type itself), and Cruhon only implemented
the bare-reference half, so passing args produced no error at the call
site, only a confusing `AttributeError` far downstream at first member
access. Fixed `Enum`/`IntEnum`/`StrEnum`/`Flag`/`IntFlag` to match
Python's dual behavior. Also confirmed (documented in README) that inline
`@command[...]` calls cannot be embedded inside a nested Python
expression like a list comprehension — the same class of limitation as
the existing `{}`-interpolation restriction, not new, just previously
undocumented for this shape.

**Performance:** confirmed parse+transpile scales near-linearly (not
quadratically) from 250 to 4000 statements (~2x time per 2x size at
every step). The new engine fingerprint (previous entry) costs ~3ms
once per process, ~0 after memoization — not a meaningful regression.

Tests: `test_shell_safe_exec.py` (7), `test_previously_untested_namespaces.py`
(17). Full suite: 6169 passing, 10 skipped, 0 regressions.

### Engine-wide hardening pass

A systematic audit of the whole core — not reactive one-bug-at-a-time
fixes — triggered by a real bug report. Two mechanical, whole-registry
scans plus what they turned up:

**Scan 1 — bare unimported module references** (the `@http`/`@json`/`@os`
bug class from the previous entry below). Every one of the then-1873
registered handlers was invoked with dummy args, its generated code
parsed with `ast`, and checked for any bare `Name.attr` pattern matching
a stdlib module name outside an `__import__(...)` call. Result: **zero**
further instances in the core registry (verified the detector itself
first against known-bad code to rule out a silently-broken scanner).

**Scan 2 — documentation vs. reality.** Cross-checked every method name
listed in library.md's `@ns.*` tables against the actual registry.
Result: **456 method names across 75+ namespaces did not exist** —
`@os.*` documented 14 methods, only 2 (`env`, `path`) were real;
`@sys.*`, `@signal.*`, `@resource.*` documented entirely different method
*names* than what was ever registered; `@httpx.*` and `@pathlib.*` were
100% fabricated (zero real handlers under either namespace, despite full
highlighted rows in both README and library.md).

Fixed by:
- Regenerating every method-list cell in library.md programmatically
  from the registry (133 rows rewritten) — now provably accurate.
- Implementing the highest-value real gaps instead of just deleting
  claims: **34 `@math.*` methods** (`clamp`, `lerp`, `sign`, `hypot`,
  `dist`, `gcd`, `lcm`, `factorial`, `comb`, `perm`, `prod`, `degrees`,
  `radians`, `log2`, `log10`, `exp`, full trig, `isclose`/`isfinite`/
  `isinf`/`isnan`, `e`/`tau`/`inf`/`nan`, `min`/`max`/`sum`), plus
  `@store.clear[]` and `@color.dim[...]`.
- Removing `@httpx.*`/`@pathlib.*` from the docs entirely (zero real
  functionality existed to preserve) with a pointer to their real
  equivalents — async HTTP is `@http.async_*` (already httpx-backed),
  path ops are `@file.*`.
- A **permanent regression test** (`test_docs_match_registry.py`) that
  parses library.md the same way and generates one pytest case per
  documented method (2011 cases) — this class of silent doc/reality
  drift can never reappear without CI catching it immediately.

**A severe bug in `cruhon-shortcuts`** (the headline, README-recommended
shortcut plugin) surfaced while testing the fixes above: its "data"
group registered `@store.all`/`@store.keys`/`@store.values`/`@store.has`
against `cruhon.core.libs.store_._STORE` — an attribute that has never
existed (`@store.*` is backed by a JSON file via injected
`__cruhon_store_*` helpers, never an in-memory `_STORE` dict). Any real
user who loaded `cruhon-shortcuts` had these four calls raise
`AttributeError` on every use, and the plugin's `all` override silently
replaced (and broke) the otherwise-correct core handler. Fixed to use
the real `__cruhon_store_load()` helper.

**`@store.*` had the same inline-call auto-injection blind spot as
`@http.*`/`@json.*`/`@os.*`** (see below): `@var[x; @store.get[...]]`
never triggered the runtime helper-function injection, because inline
namespace calls resolve straight to a code string at parse time and
never become a walkable `LibCallNode`. Fixed the same way — a
`_needs_store` flag set directly in `_parse_namespace_inline()`.

**Transpile cache could serve stale bytecode after a rebuild without a
version bump.** The cache key hashed the `cruhon.__version__` string but
nothing about the engine's actual code — during active development
(or if a maintainer ships a fix without bumping `__version__`), a
rebuilt/reinstalled wheel with genuinely different handler code would
produce an *identical* cache key for an unchanged script, silently
reusing pre-fix compiled bytecode. Fixed by adding a cheap engine
fingerprint (path + size + mtime_ns of every `.py` file under
`cruhon/core/`, no full-content hashing) as a 6th cache key input —
any core code change now invalidates old caches regardless of the
version string.

Tests: `test_docs_match_registry.py` (2011 cases), `test_store_color_extra.py`
(4), `test_shortcuts_store_bug.py` (6). Full suite: 6140 passing, 10 skipped,
0 regressions. Handler count: 1873 → 1875 (store.clear, color.dim).

### @math.* — 34 methods implemented for real

README/library.md always *documented* `clamp`, `lerp`, `sign`, `hypot`,
`dist`, `gcd`, `lcm`, `factorial`, `comb`, `perm`, `prod`, `degrees`,
`radians`, `log2`, `log10`, `exp`, `sin`/`cos`/`tan`/`asin`/`acos`/`atan`/
`atan2`, `isclose`/`isfinite`/`isinf`/`isnan`, `e`/`tau`/`inf`/`nan`, and
`min`/`max`/`sum` under `@math.*` — but none of them were ever actually
registered. Calling any of them (e.g. `@math.clamp[57; 0; 50]`) silently
fell through to a generic `namespace.method(args)` fallback that assumed
a bare `math` global was already imported, raising `NameError: name
'math' is not defined`. All 34 are now real, tested handlers.

### Auto-import fix — a critical execution bug

Found and fixed by building the actual pip package and running a full
demo end to end (not just unit tests): `@http.*`/`@requests.*` used
inline — `@var[r; @http.get[url]]`, the overwhelmingly common pattern —
raised `NameError: name 'requests' is not defined` on every real
execution. The transpiler's auto-import detection never covered inline
namespace calls (they resolve straight to a code string at parse time,
never becoming a walkable AST node), only the core `@fetch[...]` command
and bare top-level statements. This made the README's very first
non-trivial example broken for anyone actually running it — no existing
test caught it, since every prior HTTP test either only checked the
generated code string or manually pre-injected a fetched response object,
bypassing the real `requests.get(...)` call path. Also fixed the same
bare-import gap in `@json.load`/`@json.dump` and `@os.env`/`@os.path`
(a second, forgotten registration in `registry.py` predating the
current `json_.py`/proper handlers).

### Transpiler — natural display text false positives

Three more `@print[...]` edge cases found while writing prose that
mentions parentheses/colons/filenames, all in `_is_python_expression`'s
heuristics for "does this look like Python vs. plain text":
- `"sqrt(144): {result}"` — a `(` followed later by an unrelated `{...}`
  interpolation was mistaken for `func({...})` dict-argument syntax
  purely by position; now requires the `{` to fall inside the call's
  *matching* `)`.
- `"notes (joined with users) ---"` — any `(`/`)` pair anywhere in the
  text triggered "this is a function call"; now requires the `(` to be
  immediately preceded by an identifier (real call syntax never has a
  space there).
- `"Log file:     app.log"` — mentioning a filename with an extension
  triggered "this is `obj.attr` access"; dot-detection is now excluded
  from display-context text entirely (live attribute display still
  works via `{obj.attr}` interpolation, an unaffected code path).

### Parser fix — dotted plugin command names

`api.command("ns.method", ...)` and `api.block_command("ns.method", ...)`
— registering a plugin command whose name contains a `.` — were silently
unreachable via `@ns.method[...]` syntax. The lexer always splits a dotted
identifier into `NAMESPACE + DOT + AT_CMD` tokens, and the parser's
namespace-call path never checked for a matching custom registration
before falling through to generic stdlib/mod namespace dispatch. The
practical impact:

- The block body was silently dropped (no error — just missing code).
- If the dotted prefix happened to match an existing stdlib namespace
  (e.g. a plugin registering `"log.timed"`, with `@log.*` already a
  built-in namespace), the call produced `NameError: name 'log' is not
  defined` instead of ever reaching the plugin.

This is exactly the pattern `mods/*/register(api)` docstrings and the
README's own "Complete Plugin Example" demonstrate (`api.command("db.get",
...)` in `ModAPI`'s own docstring, `api.block_command("log.timed", ...)`
in the README) — the flagship example never actually ran end to end.

Fixed in `_parse_statement()`: dotted `@ns.method[...]` calls are now
checked against `self._block_commands`/`self._commands` for an exact
match *before* falling through to namespace-call routing, so a plugin's
own registration always takes priority over a same-prefixed stdlib
namespace. Verified with a new dedicated regression suite
(`test_dotted_block_commands.py`) plus the corrected README example
running end to end through the real mod loader.

---

This release also rounds out real-world deployment: read configuration
safely, connect databases from the environment, and watch everything
live in a browser.

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
@var[safe; @env.mask[key]]
@print[key = {safe}]
```

### cruhon-db — env-aware connection, migrations, seeding, live panel

Six new commands on the `@db.*` plugin:

| Command | Does |
|---|---|
| `@db.connect_env[]` / `@db.connect_env[VAR]` | Connect using a DSN from an env var (default `DATABASE_URL`) — keeps secrets out of source |
| `@db.migrate[dir]` | Apply every `*.sql` file in order, once each, tracked in a `_cruhon_migrations` table (idempotent) |
| `@db.seed[table; file]` | Bulk-insert rows from a `.json` or `.csv` file |
| `@db.dsn_safe[]` | The active DSN with the password masked — safe to print/log |
| `@db.attach_panel[]` | Stream every query on this connection to a running `@panel` dashboard (SQL, row count, backend) — requires `@panel.start[]` first |
| `@db.detach_panel[]` | Stop streaming |

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
@db.attach_panel[]
@panel.wait[]
```

### Bug fixes — found by dogfooding a real `pip install cruhon`

Building the package, installing it into a clean venv, and running a real
database-backed demo project end to end surfaced three real transpiler/
runner bugs:

- **f-string misdetected as dict literal** — `{u["id"]}: {u["name"]}` (an
  f-string template with multiple `{}` groups followed by literal text
  containing `:`) was misdetected as a single dict literal `{key: val}`
  and passed through unwrapped, producing invalid Python. Fixed with a
  proper single-brace-group check before treating a leading `{` as a
  dict/set literal.
- **Bare text ending in `.` broke `@print`** — `@print[Done.]` (an
  extremely common pattern under the documented "bare text → string"
  rule) was misdetected as Python attribute access (`obj.attr`) because
  any `.` in the text triggered pass-through. Now requires an identifier
  character on *both* sides of the dot.
- **Local `mods/` were never discovered from the documented workflow** —
  `cruhon run src/main.clpy` resolved `mods/` relative to the script's own
  directory (`src/mods/`) instead of the project root, so the standard
  `cruhon new myproject && cd myproject && cruhon run src/main.clpy` flow
  could never load `@db`, `@panel`, or any other local plugin. Fixed to
  check the current working directory first (matching every other CLI
  subcommand), then walk up from the script looking for `mods/`.

### CI

Added `.github/workflows/test.yml` — runs the full test suite plus a
build/`twine check` on every push and pull request across Python
3.10/3.11/3.12. `publish.yml` (tag-triggered PyPI release) now also runs
the test suite and `twine check` before publishing, so a broken build can
never reach PyPI.

### Counts

- **128 stdlib namespaces** · **1873 handlers**
- cruhon-db: **172+ commands** (was 166) — now includes the live-panel bridge
- New plugin: cruhon-panel
- **4038 tests** passing (was 3999)

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
