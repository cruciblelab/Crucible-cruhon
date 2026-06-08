# Changelog

All notable changes are documented here.

---

## v1.4.0 (current)

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

### Dil Tamamlama — Language Completion

- **`@with[expr as var] ... @end`** — context manager bloğu; `with open(...) as f:` artık Cruhon syntax'ı
- **`@match[value] / @case[pattern] / @default`** — Python 3.10+ pattern matching
- **`@del[var1; var2]`** — değişken silme
- **`@raise[ExceptionType; msg]`** / **`@raise`** (bare re-raise) — explicit exception fırlatma
- **Multi-line fix** — `parse_args` artık INDENT/DEDENT/COMMENT token'larını atlıyor; parantez içi multi-line expression çalışıyor
- Test suite: 156 → 172 tests (`TestWith`, `TestMatch`, `TestDel`, `TestRaise`, `TestMultiLine`)

---

## v1.2.0

### Plugin System — Scope, Transforms, Block Hooks

- **`api.block_command(..., scoped=True)`** — `__ctx__` otomatik save/restore, block içindeki değişiklikler dışarı sızmaz
- **`@ctx.push[]` / `@ctx.pop[]`** — manuel stack-based ctx scope (iç içe bloklar için)
- **`api.transform(target, fn)`** — başka plugin'in block çıktısını fn(transpiler, node, code) ile sarıp dönüştür
- **`api.block_hook("enter" | "exit", fn)`** — runtime block lifecycle: fn(plugin_name, args) her block girişinde/çıkışında çalışır
- `__ctx_stack__` ve `__ph__` exec namespace'e inject edildi
- Test suite: 149 → 156 tests

---

## v1.1.0

### Plugin Foundation System

- **`api.expose(key, value)`** — Plugin başka pluginler için API/utility yayınlar
- **`api.consume(plugin, key)`** — Başka plugin'in yayınladığını alır; default destekler
- **`api.is_loaded(name)`** — Plugin yüklü mü kontrol eder (bool)
- **`api.config(key, default)`** — Plugin'in kendi `mod.json` manifest'inden veri okur
- **Versiyon-aware bağımlılık** — `require("cruhon-utils >= 1.2.0")` gerçekten versiyon kısıtlamasını kontrol eder
- **Hata attribution** — Plugin visitor'larından gelen hatalar plugin adını gösterir
- **`list_exposed_apis()`** — Tüm yayınlanmış plugin API'lerini listeler

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
