# Cruhon

**A modern, extensible scripting language built on Python.**  
By [CrucibleLab](https://github.com/cruciblelab) · `.clpy` files · MIT License · v0.9.2

---

## What is Cruhon?

Cruhon is a scripting language that compiles to Python. It replaces Python's
indented block syntax with a uniform `@command[args]` syntax, making scripts
easier to read and write — especially for automation, tooling, and data tasks.

Every Cruhon program is valid Python under the hood. You can always inspect
what Python gets generated with `cruhon run --show-python`.

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
|---------|-------------|
| `cruhon run file.clpy` | Run a script |
| `cruhon run file.clpy --show-python` | Show generated Python before running |
| `cruhon build file.clpy` | Compile `.clpy` → `.py` |
| `cruhon build file.clpy -o out.py` | Compile to a specific output file |
| `cruhon check file.clpy` | Check for syntax errors without running |
| `cruhon new myproject` | Create a new project scaffold |
| `cruhon libs` | List all supported libraries |
| `cruhon mods` | Show loaded mods, load order, and override chains |
| `cruhon --version` | Show version |

---

## Syntax Reference

### Variables and Constants

```clpy
@var[x; 42]              # x = 42
@var[name; "Alice"]      # name = "Alice"
@var[msg; Hello world]   # msg = "Hello world"  (bare text → string)
@var[copy; name]         # copy = name          (identifier → variable reference)
@const[MAX; 100]         # MAX = 100  # const
```

### Output and Input

```clpy
@print[Hello, World!]       # prints the string
@print[Value: {x}]          # f-string interpolation
@input[Enter your name: ]   # blocking input prompt
@var[name; @input[Name: ]]  # NOT supported — @input is a statement, not inline
```

### String Interpolation

Use `{varname}` inside any value for f-string interpolation:

```clpy
@var[name; "Alice"]
@print[Hello, {name}!]        # → print(f"Hello, {name}!")
@var[msg; "Hi, {name}!"]      # → msg = f"Hi, {name}!"
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

### Functions

```clpy
@func[greet; name]
    @print[Hello, {name}!]
    @return[name]
@end

greet("Bob")           # call with Python syntax
```

Async functions:

```clpy
@async[main]
    @await[asyncio.sleep(1)]
    @print[Done!]
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
        @print[Woof!]
    @end
@end
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
```

### Loops — break and continue

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

### Assertions

```clpy
@assert[x > 0; "x must be positive"]
```

### Environment Variables

```clpy
@env[HOME]                   # prints the value
@var[home; @env[HOME]]       # capture into variable
@var[port; @env[PORT; 8080]] # with default
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

Circular includes (direct and indirect) are detected and raise a runtime error.

### Raw Python Blocks

Use `@raw` to embed arbitrary Python code:

```clpy
@raw
    import sys
    print(sys.version)
    x = [i**2 for i in range(10)]
@end
```

---

## Standard Libraries

Cruhon wraps common Python libraries with the `@namespace.method[args]` syntax.

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
@var[r; @math.random[1; 100]]
@var[r; @math.rand[]]
@var[pi; @math.pi[]]
```

### Time (`@time.*`)

```clpy
@var[now; @time.now[]]
@var[today; @time.date[]]
@var[ts; @time.timestamp[]]
@time.sleep[1]
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

Key-value file storage backed by `.cruhon_store.json`:

```clpy
@store.set["key"; "value"]
@var[val; @store.get["key"]]
@var[val; @store.get["key"; "default"]]
@store.delete["key"]
@var[all; @store.all[]]
```

### Inline Commands

These can be used inside `@var` values:

```clpy
@var[lst; @list[1; 2; 3]]
@var[d; @dict["name"; "Alice"; "age"; 30]]
@var[home; @env[HOME]]
@var[port; @env[PORT; 8080]]
```

---

## Value Semantics

Cruhon has two evaluation contexts:

**`expr` context** (`@var`, `@const`, `@return`, etc.):
- Quoted string → string literal
- Number → number
- `True`/`False`/`None` → Python literal
- Collection literal `[...]` `{...}` `(...)` → as-is
- Python expression (has operator/call/dot) → as-is
- Single identifier → Python variable reference
- Bare text (multi-word) → string literal

**`display` context** (`@print`, `@assert` message):
- Same as above, except single identifiers become string literals
- Use `{varname}` to interpolate a variable

Examples:

```clpy
@var[x; 42]           # x = 42
@var[name; "Alice"]   # name = "Alice"
@var[copy; name]      # copy = name        (references variable `name`)
@var[msg; hi there]   # msg = "hi there"   (bare text → string)

@print[hello]         # print("hello")     (single word → string in display)
@print[{x}]           # print(f"{x}")      (interpolation)
@print[x = {x}]       # print(f"x = {x}")  (f-string)
```

See [`spec/semantics.md`](spec/semantics.md) for the full specification.

---

## Mod System

Cruhon's mod system is inspired by Minecraft — mods can extend or override anything.

### Project Structure

```
myproject/
├── src/
│   └── main.clpy
└── mods/
    └── my-mod/
        ├── mod.json
        └── __init__.py
```

### mod.json

```json
{
  "name": "my-mod",
  "version": "1.0.0",
  "cruhon": ">=0.9.0",
  "namespace": "mymod",
  "author": "You"
}
```

### __init__.py

```python
def register(api):
    # Add a new command
    api.command("say", parse_say, visit_say)

    # Override an existing command (middleware chain)
    api.override("print", my_print_middleware)

    # Register a namespace
    ns = api.namespace("mymod")
    ns.register("hello", lambda args: print("Hello from mymod!"))
    ns.hook("init", lambda ns: print("mymod initialized"))

    # Add a library
    api.lib("redis", "redis")
    api.lib_call("redis", "get", lambda args: f"redis.get({args[0]})")

    # Lifecycle hooks
    api.hook("before_run", setup)
    api.hook("after_run", teardown)
    api.hook("on_error", handle_error)
```

### Publishing a Mod

```bash
# Package name must start with cruhon-
pip install cruhon-mymod
# Auto-discovered and loaded by Cruhon
```

### Load Order

1. `core` (built-in, always first)
2. `stdlib` (built-in, always second)
3. pip mods (`cruhon-*` packages, sorted alphabetically)
4. local mods (`mods/` subfolders, sorted alphabetically)

---

## Creating a New Project

```bash
cruhon new myproject
cd myproject
cruhon run src/main.clpy
```

---

## Contributing

```bash
git clone https://github.com/cruciblelab/cruhon
cd cruhon
pip install -e .
python -m pytest cruhon/tests/test_core.py
cruhon run cruhon/examples/hello.clpy
```

---

## License

MIT — CrucibleLab
