# Cruhon

**A modern, extensible scripting language built on Python.**  
By [CrucibleLab](https://github.com/cruciblelab) · `.clpy` files · MIT License · v1.6.0

---

## What is Cruhon?

Cruhon is a scripting language that compiles to Python. It replaces Python's
indented block syntax with a uniform `@command[args]` syntax, making scripts
easier to read and write — especially for automation, tooling, and data tasks.

Every Cruhon program is valid Python under the hood. You can always inspect
what Python gets generated with `cruhon run --show-python`.

The plugin system lets you extend everything: new commands, new block types,
new value syntax, new runtime objects — all without touching the core.

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
| `cruhon build file.clpy` | Compile `.clpy` → `.py` |
| `cruhon build file.clpy -o out.py` | Compile to a specific output file |
| `cruhon check file.clpy` | Check for syntax errors without running |
| `cruhon new myproject` | Create a new project scaffold |
| `cruhon new --plugin myplugin` | Create a plugin scaffold in `mods/myplugin/` |
| `cruhon libs` | List all supported libraries |
| `cruhon mods` | Show loaded plugins, exposed APIs, block commands, overrides |
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
```

Break and continue:

```clpy
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
    @await[asyncio.sleep(1)]
    @print[Done!]
@end
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

### Error Handling

```clpy
@try
    @var[x; int("bad")]
@catch[e]
    @print[Error: {e}]
@finally
    @print[done]
@end

# Raise exceptions
@raise[ValueError; "invalid input"]

# Re-raise inside @catch
@try
    risky_call()
@catch[e]
    @raise
@end
```

### Context Managers

```clpy
@with[open("data.txt") as f]
    @var[content; f.read()]
    @print[{content}]
@end

# Without binding
@with[lock]
    do_work()
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

# Structural patterns work too
@match[command.split()]
    @case[["quit"]]
        @print[Quitting]
    @case[["go"; direction]]
        @print[Going {direction}]
    @default
        @print[Unknown command]
@end
```

### Delete Variables

```clpy
@del[x]
@del[a; b; c]
```

### Assertions

```clpy
@assert[x > 0; "x must be positive"]
```

### Environment Variables

```clpy
@var[home; @env[HOME]]
@var[port; @env[PORT; 8080]]   # with default
```

### Imports

```clpy
@import[requests]
@import[requests; req]   # with alias
```

### Include Other Files

```clpy
@include[utils.clpy]
@include[../shared/helpers.clpy]
```

Circular includes are detected and raise a runtime error.

### Raw Python Blocks

Use `@raw` to pass Python code through unchanged — no Cruhon processing:

```clpy
@raw
    import sys
    from pathlib import Path
    x = [i**2 for i in range(10)]
@end
```

### Collections

```clpy
@var[lst; @list[1; 2; 3]]                        # [1, 2, 3]
@var[d; @dict["name"; "Alice"; "age"; 30]]        # {"name": "Alice", "age": 30}
```

### Multi-line Expressions

Expressions can span multiple lines inside parentheses, brackets, or braces:

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

## Value Semantics

Cruhon has two evaluation contexts:

**`expr` context** — right-hand sides of `@var`, `@const`, `@return`, etc.:
- `"text"` → string literal
- `42`, `3.14` → numeric literal
- `True`, `False`, `None` → Python literal
- `[...]`, `{...}`, `(...)` → collection literal, passed through
- Expression with operator/call/dot → passed through as Python expression
- Single identifier → Python variable reference
- Bare text (anything else) → string literal

**`display` context** — `@print`, `@assert` message:
- Same as `expr`, except a **single identifier becomes a string literal**
- Use `{varname}` for variable interpolation

```clpy
@var[x; 42]           # x = 42
@var[name; "Alice"]   # name = "Alice"
@var[copy; name]      # copy = name        (variable reference)
@var[msg; hi there]   # msg = "hi there"   (bare text → string)

@print[hello]         # print("hello")     (single word → string in display)
@print[{x}]           # print(f"{x}")      (interpolation)
@print[x = {x}]       # print(f"x = {x}")
```

See [`spec/semantics.md`](spec/semantics.md) for the full specification.

---

## Context Variables (`@ctx`)

`__ctx__` is a shared dict available throughout script execution. Plugins use
it to pass data into block bodies. Scripts can read and write it directly.

```clpy
@ctx.set["username"; "Alice"]
@ctx.set["score"; 100]

@var[u; @ctx["username"]]            # read with inline expression
@var[u; @ctx["username"; "guest"]]   # with default

@var[s; @ctx.get["score"]]
@ctx.clear[]
@ctx.delete["score"]

# Stack-based scope (for nested blocks)
@ctx.push[]
    @ctx.set["x"; "inner"]
    @print[{@ctx["x"]}]   # inner
@ctx.pop[]
@print[{@ctx["x"]}]       # outer
```

---

## Standard Libraries

### HTTP (`@http.*`)

```clpy
@var[res; @http.get["https://api.example.com/data"]]
@var[body; @http.json[res]]
@var[status; @http.status[res]]

@var[res; @http.post["https://api.example.com/items"; {"name": "test"}]]
@var[res; @http.put["https://api.example.com/items/1"; {"name": "updated"}]]
@var[res; @http.delete["https://api.example.com/items/1"]]
```

Async HTTP (requires `httpx`):

```clpy
@async[main]
    @var[res; @http.async_get["https://example.com"]]
@end
```

SSRF protection is built in — requests to private/loopback addresses are blocked.
All requests have a 30-second timeout.

### File (`@file.*`)

```clpy
@var[content; @file.read["data.txt"]]
@file.write["output.txt"; content]
@file.append["log.txt"; "new line\n"]
@var[exists; @file.exists["data.txt"]]
@file.delete["temp.txt"]
```

Path traversal outside the working directory is blocked.

### JSON (`@json.*`)

```clpy
@var[text; @json.stringify[data]]
@var[obj; @json.parse[text]]
@var[pretty; @json.pretty[data]]
@json.read["config.json"]
@json.write["output.json"; data]
```

### Math (`@math.*`)

```clpy
@var[r; @math.sqrt[16.0]]
@var[r; @math.abs[-5]]
@var[r; @math.pow[2; 10]]
@var[r; @math.floor[3.7]]
@var[r; @math.ceil[3.2]]
@var[r; @math.log[2.718]]
@var[r; @math.round[3.14159; 2]]
@var[r; @math.random[1; 100]]   # random int between 1 and 100
@var[r; @math.rand[]]           # random float 0.0–1.0
@var[pi; @math.pi[]]
```

### Time (`@time.*`)

```clpy
@var[now; @time.now[]]            # datetime string
@var[today; @time.date[]]         # date string
@var[ts; @time.timestamp[]]       # unix timestamp
@time.sleep[1]                    # sleep 1 second
@var[fmt; @time.format["%Y-%m-%d"]]
```

### Color (`@color.*`)

```clpy
@print[@color.red["Error!"]]
@print[@color.green["OK"]]
@print[@color.yellow["Warning"]]
@print[@color.blue["Info"]]
@print[@color.cyan["Hint"]]
@print[@color.bold["Title"]]
```

### Store (`@store.*`)

Persistent key-value storage backed by `.cruhon_store.json`:

```clpy
@store.set["key"; "value"]
@var[val; @store.get["key"]]
@var[val; @store.get["key"; "default"]]
@store.delete["key"]
@var[all; @store.all[]]
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

Create a plugin scaffold:

```bash
cruhon new --plugin my-plugin
```

### mod.json

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What this plugin does",
  "cruhon": ">=1.5.0"
}
```

Optional fields:

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "cruhon": ">=1.5.0",
  "author": "Your Name",
  "license": "MIT",
  "my_setting": "some_value"
}
```

Any extra field is accessible via `api.config("my_setting")` inside the plugin.

### `register(api)` — Entry Point

Every plugin must have a `register(api)` function in `__init__.py`:

```python
def register(api):
    # Everything you add here becomes part of the language
    api.command("greet", parse_greet, visit_greet)
```

---

## Plugin API Reference

### `api.command(name, parser_fn, visitor_fn)`

Register a new `@command`.

```python
from cruhon.core.ast_nodes import Node
from dataclasses import dataclass

@dataclass
class GreetNode(Node):
    target: str = ""

def parse_greet(parser):
    parser.advance()               # consume @greet token
    args = parser.parse_args()
    return GreetNode(target=args[0] if args else '"world"', line=0)

def visit_greet(transpiler, node):
    return transpiler._line(f'print("Hello, " + str({node.target}))', node.line)

def register(api):
    api.command("greet", parse_greet, visit_greet)
```

Script:

```clpy
@greet["Alice"]   # → print("Hello, " + str("Alice"))
```

---

### `api.block_command(name, visitor_fn, scoped=False)`

Register a block command — opened by `@name[args]`, closed by `@end`.

```python
def visit_section(transpiler, node):
    # node.args   — positional args from the header
    # node.kwargs — keyword args from the header
    # node.body   — list of child AST nodes
    title = node.args[0] if node.args else '"Untitled"'
    body_code = "\n".join(
        result for n in node.body
        if (result := n.accept(transpiler))
    )
    return (
        transpiler._line(f'print("=== " + {title} + " ===")') +
        "\n" + body_code
    )

def register(api):
    api.block_command("section", visit_section)
```

Script:

```clpy
@section["Introduction"]
    @print[Welcome to Cruhon.]
    @print[This is a block command.]
@end
```

**`scoped=True`** — `__ctx__` is automatically saved before the block body and
restored after. Changes inside the block don't leak out:

```python
api.block_command("isolated", visit_isolated, scoped=True)
```

---

### `api.override(command, fn)`

Override an existing command. Multiple overrides form a middleware chain —
first loaded = outermost wrapper.

```python
def timed_print(transpiler, node, next_fn):
    before = transpiler._line('__t0__ = __import__("time").monotonic()')
    result = next_fn()   # call the original (or next override)
    after  = transpiler._line('print(f"[{__import__(\"time\").monotonic()-__t0__:.3f}s]")')
    return before + "\n" + result + "\n" + after

def register(api):
    api.override("print", timed_print)
```

A 2-argument function is a terminal override (ignores the chain):

```python
def silent_print(transpiler, node):
    return ""   # suppress all @print output

api.override("print", silent_print)
```

---

### `api.inject(key, value_or_factory)`

Inject a value into the exec() globals for every script run. Scripts access
it by name directly — no `__ns__` or import needed.

If the value is a callable (no args), it is called before each exec() to get
the value. Otherwise the value is used as-is.

```python
import sqlite3

def register(api):
    # Static value
    api.inject("APP_VERSION", "2.1.0")

    # Factory: called fresh before each run
    api.inject("db", lambda: sqlite3.connect(":memory:"))

    # Object with attributes
    class Config:
        debug = True
        max_retries = 3

    api.inject("cfg", Config())
```

Script:

```clpy
@print[{APP_VERSION}]
@var[rows; db.execute("SELECT 1").fetchall()]
@if[cfg.debug]
    @print[Debug mode is on]
@end
```

---

### `api.inline_command(name, handler_fn)`

Register a command that produces an inline Python expression — usable inside
`@var`, `@print`, and any other argument context.

`handler_fn(parser) -> str`:
1. Call `parser.advance()` to consume the `@name` token
2. Optionally call `parser.parse_args()` to get arguments
3. Return a Python expression string

```python
import uuid
import datetime

def handle_uuid(parser):
    parser.advance()
    parser.parse_args()
    return "str(__import__('uuid').uuid4())"

def handle_now(parser):
    parser.advance()
    parser.parse_args()
    return "__import__('datetime').datetime.now().isoformat()"

def handle_slug(parser):
    parser.advance()
    args = parser.parse_args()
    text = args[0] if args else '""'
    return f'{text}.lower().replace(" ", "-")'

def register(api):
    api.inline_command("uuid", handle_uuid)
    api.inline_command("now",  handle_now)
    api.inline_command("slug", handle_slug)
```

Script:

```clpy
@var[id;    @uuid[]]
@var[ts;    @now[]]
@var[slug;  @slug["Hello World"]]
@print[{id} — {ts}]
```

---

### `api.eval_hook(fn)`

Hook into value evaluation at transpile-time.

`fn(value: str, context: str) -> str | None`

Return a Python expression string to override the default evaluation.
Return `None` to let the default rules handle the value.

`context` is `"expr"` (for `@var`, `@return`, etc.) or `"display"` (for `@print`).

Hooks run in registration order. First non-None return wins.

```python
def dollar_env(value, context):
    # $VAR_NAME → os.environ.get("VAR_NAME", "")
    if value.startswith("$") and value[1:].isidentifier():
        return f'__import__("os").environ.get("{value[1:]}", "")'
    return None

def register(api):
    api.eval_hook(dollar_env)
```

Script:

```clpy
@var[url;  $DATABASE_URL]
@var[port; $PORT]
@print[$GREETING]
```

---

### `api.ast_hook(node_type, fn)`

Register a parse-time AST hook. `fn(node) -> node` fires on every node of the
given type after parsing and before transpilation. Mutate the node or return a
new one.

```python
def prefix_vars(node):
    # Automatically prefix all variable names with "safe_"
    if not node.name.startswith("_"):
        node.name = "safe_" + node.name
    return node

def register(api):
    api.ast_hook("VarNode", prefix_vars)
```

---

### `api.transform(target, fn)`

Wrap another plugin's block output with additional generated code.

`fn(transpiler, node, code: str) -> str`

```python
def register(api):
    # Wrap every @route block with timing code
    api.transform("route", time_route)

def time_route(transpiler, node, code):
    path = node.args[0] if node.args else '"unknown"'
    before = transpiler._line(f'__t0__ = __import__("time").monotonic()')
    after  = transpiler._line(f'print(f"route {path} took {{__import__(\"time\").monotonic()-__t0__:.3f}}s")')
    return before + "\n" + code + "\n" + after
```

---

### `api.block_hook(event, fn)`

Register a runtime hook that fires when any plugin block starts or ends.

```python
entered = []

def on_enter(plugin_name, args):
    entered.append(plugin_name)
    print(f"Block @{plugin_name} starting")

def on_exit(plugin_name, args):
    print(f"Block @{plugin_name} ended")

def register(api):
    api.block_hook("enter", on_enter)
    api.block_hook("exit",  on_exit)
```

---

### `api.hook(event, fn)`

Hook into the full pipeline lifecycle.

| Event | Signature | When |
|---|---|---|
| `before_run` | `fn(source=str)` | Before parsing |
| `after_run` | `fn()` | After exec finishes |
| `before_parse` | `fn(source) -> source` | Lexer pre-hook — modify source text |
| `after_parse` | `fn(ast) -> ast` | Parser post-hook — modify AST |
| `before_transpile` | `fn(ast) -> ast` | Transpiler pre-hook |
| `after_transpile` | `fn(code) -> code` | Modify generated Python code |
| `on_error` | `fn(error=exc)` | When any error occurs |

```python
def register(api):
    api.hook("before_run",   lambda source: print("[run start]"))
    api.hook("after_run",    lambda: print("[run end]"))
    api.hook("on_error",     lambda error: print(f"[error] {error}"))
    api.hook("after_transpile", lambda code: code.replace("pass", "pass  # noop"))
```

---

### `api.expose(key, value)` / `api.consume(plugin, key, default?)`

Share values between plugins.

```python
# Plugin A — publishes a utility
def register(api):
    api.expose("slugify", lambda s: s.lower().replace(" ", "-"))
    api.expose("version", "2.0")
```

```python
# Plugin B — uses Plugin A's utility
def register(api):
    slugify = api.consume("plugin-a", "slugify")
    version = api.consume("plugin-a", "version", default="1.0")

    def visit_slug(transpiler, node):
        # use slugify at register-time (Python level)
        ...
```

---

### `api.namespace(name)`

Register a mod namespace for runtime dispatch.

```python
def register(api):
    ns = api.namespace("db")

    def handle_query(args):
        sql = args[0] if args else '""'
        return f'__db_conn__.execute({sql}).fetchall()'

    ns.register("query", handle_query)
    ns.hook("init",    lambda ns: print("db namespace ready"))
    ns.hook("destroy", lambda ns: print("db namespace closed"))
```

Script:

```clpy
@var[rows; @db.query["SELECT * FROM users"]]
```

---

### `api.require(dependency)`

Declare a dependency. A warning is printed at load time if not satisfied.

```python
def register(api):
    api.require("cruhon-utils")          # exact name
    api.require("cruhon-utils >= 1.2.0") # with version constraint
```

---

### `api.is_loaded(name)` / `api.config(key, default?)`

```python
def register(api):
    if api.is_loaded("cruhon-redis"):
        cache = api.consume("cruhon-redis", "cache_backend")
    else:
        cache = memory_cache

    # Read from mod.json
    prefix = api.config("command_prefix", default="my")
    debug  = api.config("debug", default=False)
```

---

### `api.alias(name, target)`

Register a command alias.

```python
def register(api):
    api.alias("say", "print")   # @say[...] → same as @print[...]
```

---

### `api.lexer_hook(fn)` / `api.token_hook(fn)` / `api.syntax(token_type)`

Low-level lexer extensions.

```python
def register(api):
    # Transform source text before tokenization
    api.lexer_hook(lambda src: src.replace("§", "@"))

    # Transform token list after tokenization
    api.token_hook(lambda tokens: [t for t in tokens if t.type != "COMMENT"])

    # Register a new token type
    api.syntax("DOLLAR")
```

---

## Complete Plugin Example

A full plugin that demonstrates the key APIs:

```python
"""
mods/cruhon-logger/__init__.py

Adds:
  @log["message"]          — structured log line
  @log.timed[...] @end     — block with elapsed time
  api.inject("logger", ...)— injects logger into all scripts
"""

import time
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


# ── @log["message"] ──────────────────────────────────────────

def parse_log(parser):
    from cruhon.core.ast_nodes import Node
    from dataclasses import dataclass

    @dataclass
    class LogNode(Node):
        msg: str = ""

    parser.advance()
    args = parser.parse_args()
    msg = args[0] if args else '""'
    return LogNode(msg=msg, line=0)


def visit_log(transpiler, node):
    return transpiler._line(f'logger.log({node.msg})', node.line)


# ── @log.timed[label] ... @end ────────────────────────────────

def visit_timed(transpiler, node):
    label = node.args[0] if node.args else '"block"'
    body = "\n".join(r for n in node.body if (r := n.accept(transpiler)))
    t = transpiler
    return "\n".join([
        t._line(f'__t0__ = __import__("time").monotonic()'),
        body or t._line("pass"),
        t._line(f'logger.log(f"{label} completed in {{__import__(\"time\").monotonic()-__t0__:.3f}}s")'),
    ])


# ── register ─────────────────────────────────────────────────

def register(api):
    api.inject("logger", lambda: _logger)
    api.command("log", parse_log, visit_log)
    api.block_command("log.timed", visit_timed)
    api.expose("get_log_lines", lambda: _logger.lines)
```

Script using this plugin:

```clpy
@log["Script started"]

@log.timed["data processing"]
    @var[data; load_data()]
    @var[result; process(data)]
    @log["Processed {len(result)} items"]
@end

@log["Done"]
```

---

## Publishing a Plugin

Pip-installable plugins are auto-discovered when their package name starts with `cruhon-`.

```
cruhon-logger/
├── pyproject.toml
└── cruhon_logger/
    ├── __init__.py   ← must contain register(api)
    └── mod.json
```

`pyproject.toml`:

```toml
[project]
name = "cruhon-logger"
version = "1.0.0"

[project.entry-points."cruhon.mods"]
cruhon-logger = "cruhon_logger:register"
```

Install and run:

```bash
pip install cruhon-logger
cruhon run script.clpy   # plugin is loaded automatically
cruhon mods              # see it in the loaded list
```

### Load Order

1. `core` (built-in, always first)
2. `stdlib` (built-in, always second)
3. pip plugins (`cruhon-*` packages, sorted alphabetically)
4. local plugins (`mods/` subfolders, sorted alphabetically)

First loaded = outermost in override chains.

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

## License

MIT — CrucibleLab
