# Cruhon Mod System

The mod system lets you extend Cruhon without touching core files.
A mod can register new commands, new library namespaces, inject runtime
objects, and hook into every stage of the pipeline.

---

## Mod Structure

```
mods/
└── my-mod/
    ├── mod.json       ← required
    └── __init__.py    ← required, must contain register(api)
```

---

## mod.json

```json
{
    "name": "my-mod",
    "version": "1.0.0",
    "author": "YourName",
    "description": "What this mod does",
    "namespace": "mymod",
    "cruhon": ">=0.1.0"
}
```

---

## __init__.py — register(api)

```python
from cruhon.core.ast_nodes import Node, register_node
from dataclasses import dataclass, field

# 1. Define a new AST Node
@dataclass
class SayNode(Node):
    message: str = ""

register_node("SayNode", SayNode)


# 2. Parser function — @say[message] → SayNode
def parse_say(parser):
    line = parser.current.line
    parser.advance()  # consume @say token
    args = parser.parse_args()
    return SayNode(message=args[0] if args else "", line=line)


# 3. Visitor — SayNode → Python code
def visit_say(transpiler, node):
    return transpiler._line(f'print(">> " + str({repr(node.message)}))')


# 4. register(api) — mod entry point
def register(api):
    # Register new command
    api.command("say", parse_say, visit_say)

    # Register new library namespace
    # api.lib("redis", "redis")
    # api.lib_call("redis", "get", lambda args: f"redis_client.get({args[0]})")

    # Override a core command
    # api.override("print", my_print_visitor)

    # Hook into lifecycle events
    # api.hook("before_run", setup_function)
    # api.hook("after_run", cleanup_function)
    # api.hook("on_error", error_handler)
```

Usage (in a .clpy file):
```
@say[Hello from my mod!]
```

---

## Hook Events

| Event              | When fired                   | Parameter         |
|--------------------|------------------------------|-------------------|
| `before_run`       | Before program starts        | `source`          |
| `after_run`        | After program finishes       | —                 |
| `before_parse`     | Before lexer                 | source string     |
| `after_parse`      | After parsing                | AST ProgramNode   |
| `before_transpile` | Before transpilation         | AST ProgramNode   |
| `after_transpile`  | After Python code is emitted | Python string     |
| `on_error`         | When an error occurs         | `error`           |

---

## Publishing as a pip Package

```
pip install cruhon-db
```

Package name must start with `cruhon-`.
`__init__.py` must contain a `register(api)` function.
Cruhon auto-discovers and loads it.

---

## Namespace Conflicts

If two mods register the same `@command` name, the last one loaded wins.
Use a namespace to avoid conflicts:

```
@mymod.command[...]
```

---

## Example Mods

- `cruhon-db` — SQLite/PostgreSQL support
- `cruhon-discord` — discord.py wrapper
- `cruhon-web` — Flask/FastAPI wrapper
- `cruhon-redis` — Redis support
- `cruhon-dotenv` — .env file support
