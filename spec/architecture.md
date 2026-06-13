# Cruhon Engine Architecture

**Version:** 2.7.0
**Status:** Stable

---

## Philosophy

Cruhon is as free as Python, but easier.
No artificial restrictions on what users can build.
The only immutable things are the syntax contract.

---

## Engine Pipeline

Five primary machines plus three support machines. Each has one job.

```
.clpy source
  → [Syntax Machine]     Lexer + SyntaxEngine + Parser
  → [Semantic Machine]   _eval_value(value, context)
  → [Transform Machine]  Transpiler → Python source
  → [Runtime Machine]    Runner → exec()
      ↑ ↓
  [Extension Machine]    ModLoader — hooks into all stages
  [Diagnostics Machine]  diagnostics.py — error rendering
  [LSP Machine]          lsp/cruhon_lsp/ — editor integration
  [Namespace Runtime]    namespace_runtime.py — mod namespaces
```

---

## Syntax Machine

Three components: SyntaxEngine, Lexer, Parser.

### SyntaxEngine (v0.6)

Single truth source for argument and expression parsing.
File: `core/syntax_engine.py`

Both the Lexer and the Parser delegate to SyntaxEngine. No other code performs
depth-aware argument splitting.

| Method | Description |
|--------|-------------|
| `split_args(source) → list[str]` | Split a Cruhon argument string on top-level `;`. Handles depth (brackets, parens, braces) and strings. |
| `read_block(line, start) → (str, int)` | Read raw content until `]` or `;` at depth 0. Used by `Lexer._read_raw`. |
| `validate_arg(arg, line) → None` | Detect unbalanced parentheses; raise a helpful `ParseError`. |

Before v0.6, `lexer.py` had `_read_raw()` (16 lines, depth-aware, no string
handling) and `parser.py` had `parse_args()` (54 lines, token-based, no depth
awareness). These produced inconsistent results for inputs like
`@var[x; [1,2,3]]`. SyntaxEngine unifies them.

### Lexer

Tokenizes `.clpy` source into a flat token list.
File: `core/lexer.py`

`_read_raw()` delegates to `SyntaxEngine.read_block()`.

**Token types:**

| Token | Description |
|-------|-------------|
| `AT_CMD` | `@commandname` |
| `NAMESPACE` | `@ns.method` |
| `STRING` | Quoted string literal |
| `NUMBER` | Numeric literal |
| `IDENT` | Bare identifier |
| `NEWLINE` | Line end |
| `INDENT` | Indentation increase |
| `DEDENT` | Indentation decrease |
| `LBRACKET` | `[` |
| `RBRACKET` | `]` |
| `EOF` | End of file |

### Parser

Converts the token list into an AST.
File: `core/parser.py`

`parse_args()` delegates to `SyntaxEngine.split_args()`.

- Registers core commands and plugin commands via `register_command` /
  `register_block_command`.
- Runs pre-hooks before tokenization begins and post-hooks after the full AST
  is assembled.
- Tracks module aliases in `Parser._module_aliases` for the module system.
- Performs circular dependency detection at parse time.

---

## Semantic Machine

Single evaluation function for all value fields.
File: `core/transpiler.py` — `_eval_value(value, context)`

### Contexts

- `"expr"` — right-hand side of `@var`, `@const`, `@return`, etc. Bare
  identifiers are variable references.
- `"display"` — `@print`, `@assert` message arguments. Bare identifiers become
  string literals.

### 8-Rule Priority Order

1. Quoted string → string literal
2. Quoted or bare with `{var}` → f-string
3. Numeric literal → number
4. `True` / `False` / `None` → bool / None
5. Collection literal (`[`, `{`, `(`) → emitted as-is
6. Python expression (operator / call / dot / subscript) → emitted as-is
7. Single identifier → variable reference (`expr`) or string literal (`display`)
8. Bare text → string literal

See `spec/semantics.md` for the full specification.

---

## Transform Machine

Converts the AST to Python source code via the visitor pattern.
File: `core/transpiler.py`

- Each AST node type is handled by a corresponding `visit_{NodeName}(node)` method
  that returns a Python source string.
- `_line_map` — dict mapping each generated Python line number to the originating
  Cruhon source line. Used by the Runner and Diagnostics Machine for error attribution.
- `_eval_value(value, context)` is called for every value field during visitation.
- `_block(nodes)` renders a list of nodes as an indented Python block.

---

## Runtime Machine

Runs the generated Python code.
File: `core/runner.py`

Responsibilities:

- Resolves `@include` nodes by inlining referenced source files before the parse
  pass — the parser never sees raw include directives.
- Auto-injects standard imports (`os`, `requests`, store helpers, `asyncio` when
  an `async def` is present in the generated output).
- Executes via `exec()` for synchronous programs or `asyncio.run()` for async
  programs.
- Maps Python runtime exceptions back to Cruhon source lines using `_line_map`
  from the Transpiler, then attaches structured context via `_attach_context()`
  for rich rendering by the Diagnostics Machine.
- Handles `--show-python` output formatting.

---

## Diagnostics Machine (v2.1)

Single source of truth for error rendering.
File: `core/diagnostics.py`

Used by the lexer, parser, transpiler, runner, and CLI so every error is
rendered the same way: error type, mapped Cruhon line, source excerpt with a
caret, a plain-language hint, and a "did you mean?" suggestion.

| Symbol | Description |
|--------|-------------|
| `render_report(...)` | Master renderer for structured diagnostic reports |
| `render_exception(...)` | Master renderer for caught exceptions |
| `source_excerpt(...)` | Context lines plus caret pointing at the error column |
| `suggest(...)` | Difflib-based spelling suggestions from identifiers in the source |
| `DiagnosticLog` | Opt-in, append-only file logging of engine diagnostics |

`DiagnosticLog` is enabled by the `CRUHON_LOG` / `CRUHON_LOG_LEVEL` environment
variables or the `cruhon run --log` flag. It never raises; it is inert when
unset. It is entirely separate from the `@log.*` stdlib library, which handles
a script's own application-level logging.

The runner attaches structured fields (`source`, `filename`, `cruhon_line`,
`hint`, `suggestion`, `error_type`) to in-flight exceptions via
`_attach_context()`, so any consumer can re-render them with full context.

---

## Extension Machine

Deterministic plugin loading system.
File: `core/mod_loader.py`

### Load Order

Always enforced, never configurable:

```
1. core        built-in core commands (always first)
2. stdlib      built-in standard library (always second)
3. pip plugins cruhon-* packages, sorted alphabetically
4. local mods  mods/ subfolders, sorted alphabetically
```

### Override Chain

Multiple plugins overriding the same command form a middleware chain.
First loaded = outermost wrapper. This is a deliberate design: core
definitions are the innermost target; each override wraps the previous.

### DependencyResolver

At load time, `DependencyResolver` checks each plugin's declared `requires`,
`consumes`, and `exposes` metadata and raises a `PluginError` for any
unsatisfied dependency before any plugin code runs.

---

## ModAPI — Complete Public Interface (v2.7.0)

All plugin interaction with the engine goes through the `ModAPI` object passed
to each plugin's `register(api)` entry point.

```python
# Commands
api.command(name, parser_fn, visitor_fn)
api.block_command(name, parser_fn, visitor_fn, scoped=False)
api.inline_command(name, fn)
api.override(name, fn, warn=True)

# Lifecycle hooks
api.hook(event, fn)
# events: before_parse / after_parse / before_transpile / after_transpile
#         / before_exec / after_run / on_error
api.ast_hook(fn)          # parse-time AST transformation
api.eval_hook(fn)         # hook into _eval_value
api.lexer_hook(fn)        # token stream hook
api.token_hook(fn)        # individual token hook

# Node transforms
api.transform(node_name, fn)   # rewrite AST nodes of the given type

# Block lifecycle
api.block_hook(event, name, fn)   # events: on_enter / on_exit for named block commands

# Runtime injection
api.inject(name, value)           # inject a name into exec() globals
api.inject_once(name, value)      # inject only if not already present

# Stdlib registration
api.lib(name, python_module)             # register a namespace
api.lib_call(ns, method, fn)             # register a method on a namespace
api.namespace(name) → NamespaceProxy     # obtain the runtime namespace object

# Plugin interop
api.expose(key, value)            # share a value with other plugins
api.consume(key) → value          # receive a value from another plugin
api.is_loaded(name) → bool        # check whether a plugin is loaded
api.require(name, version=None)   # assert a dependency is satisfied

# Unregister (v2.1)
api.unregister_command(name)
api.remove_hook(event, fn)
api.remove_inject(name)
api.remove_eval_hook(fn)

# Config
api.config(key, default=None) → value
api.syntax(name, handler)         # register a syntax rewrite rule
```

---

## Namespace Runtime (v0.8)

Stateful runtime objects for mod namespaces.
File: `core/namespace_runtime.py`

Mod namespaces are stateful runtime objects as distinct from stateless stdlib
`lib_call` registrations. The transpiler emits `__ns__["namespace"].call("method", *args)`
in the generated Python for any `@ns.method[...]` invocation.

| Feature | Description |
|---------|-------------|
| `access_state` | Namespaces may expose read access to their internal state |
| `write_state` | Namespaces may permit controlled writes to their internal state |
| `allow_peer` | Namespaces may grant access to named peer namespaces |
| `init_all()` | Called by the runner before `exec()` to initialize all namespaces |
| `destroy_all()` | Called by the runner after execution to tear down all namespaces |

---

## Module System (v1.6)

File-level encapsulation and selective import for `.clpy` programs.

| Directive | Description |
|-----------|-------------|
| `@module[name] ... @end` | Declare a named module scope within a file |
| `@export[names]` | Declare the public API of a module |
| `@use[path]` | Load a `.clpy` file as a module |
| `@from[module; names]` | Selective import from a named module |

- Circular dependencies are detected at parse time and produce a `ParseError`
  with the full cycle in the message.
- Module aliases are tracked in `Parser._module_aliases` and used by the
  transpiler to qualify generated names.

---

## LSP Machine (v2.6)

Editor integration via the Language Server Protocol.
Base path: `lsp/cruhon_lsp/`

| File | Responsibility |
|------|----------------|
| `server.py` | `pygls` 2.x `LanguageServer` — entry point, capability registration, dispatch |
| `completions.py` | Static completion data for commands and namespaces |
| `diagnostics.py` | Runs parse + transpile on the open document; emits `LSP Diagnostic` objects |
| `hover.py` | Hover documentation for commands and namespace methods |

**Capabilities:**

- Completions
- Diagnostics (published via `ls.text_document_publish_diagnostics(PublishDiagnosticsParams(...))`)
- Hover
- Document symbols
- Go-to-definition

---

## CLI Commands

```
cruhon run <file> [--show-python] [--log] [--watch]
cruhon repl                           interactive REPL with readline history and tab-complete
cruhon fmt <file> [--check] [--stdout] [--indent N]
cruhon lint [files...]                static lint warnings
cruhon test [path] [-v]               run .clpy test files
cruhon bundle <file> [-o output]      bundle to a single .py file
cruhon docs [plugin]                  show plugin documentation
cruhon mods                           list loaded plugins
cruhon new --plugin <name>            scaffold a new plugin
```

---

## Syntax Contract (immutable forever)

The items below are frozen. No future version of Cruhon may change them
without a breaking-change major version bump.

```
@command[arg; arg]   command invocation format
@end                 block terminator
{var}                string interpolation
#                    comment prefix
.clpy                source file extension
;                    argument separator inside [ ]
```

Additionally frozen:

- Core command names listed in `spec/grammar.md`
- `Node.accept()` and `Node.line` on all AST base nodes
- All `ModAPI` public method signatures listed above
