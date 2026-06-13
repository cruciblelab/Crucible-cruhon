# Cruhon

**A modern, extensible scripting language built on Python.**  
By [CrucibleLab](https://github.com/cruciblelab) · `.clpy` files · MIT License · v2.6.0

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
| `cruhon run file.clpy --watch` | Re-run automatically when `.clpy` files change |
| `cruhon run file.clpy --log cruhon.log [--log-level DEBUG]` | Write Cruhon's diagnostics to a log file |
| `cruhon repl` | Start an interactive session (`:help`, `:vars`, `:clear`, `:quit`) |
| `cruhon docs` | List plugins that ship a command reference |
| `cruhon docs discord` | Show a plugin's full command reference |
| `cruhon fmt file.clpy` | Normalize indentation (writes the file) |
| `cruhon fmt file.clpy --check` | Exit non-zero if not formatted (CI-friendly) |
| `cruhon fmt file.clpy --stdout` | Print formatted result without writing |
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

## Errors & Diagnostics

When something goes wrong, Cruhon shows **more** than Python — not a flat
traceback, but the exact line, a caret under the problem, a plain-language
hint, and a spelling suggestion:

```
✗ NameError  greet.clpy:3

  name 'price' is not defined

     1 │ @var[name; "World"]
     2 │ @print[Hello]
   → 3 │ @var[total; price + tax]

  Hint: 'price' is not defined as a variable.
        If you meant text, wrap it in quotes: "price".
```

`cruhon check file.clpy` shows the same rich excerpt for syntax errors,
without running the script. Color auto-disables for pipes, files, and when
`NO_COLOR` is set.

### Logging Cruhon's diagnostics to a file (no code changes)

Any user can route Cruhon's own diagnostics to a log file — purely via
environment variables or a CLI flag, no script edits required:

```bash
# Environment variables
CRUHON_LOG=cruhon.log cruhon run app.clpy          # write to cruhon.log
CRUHON_LOG=1 cruhon run app.clpy                    # write to ./cruhon.log
CRUHON_LOG_LEVEL=DEBUG CRUHON_LOG=cruhon.log cruhon run app.clpy

# Or with CLI flags
cruhon run app.clpy --log cruhon.log --log-level DEBUG
```

Levels: `ERROR`, `WARNING`, `INFO` (default), `DEBUG`. At `DEBUG` the log also
captures the source, the generated Python, run timings, and the full
diagnostic plus Python traceback for every run.

> This is Cruhon's **engine** diagnostics. For your **script's own**
> application logging (to any file you choose), use the `@log.*` library —
> e.g. `@log.setup["DEBUG"; "app.log"]`.

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

## Standard Libraries (52 namespaces, 1100+ commands)

See [`library.md`](library.md) for the complete reference.

### HTTP (`@http.*`) — GET, POST, upload, auth

```clpy
@var[res; @http.get["https://api.example.com/data"]]
@var[body; @http.json[res]]
@var[status; @http.status[res]]

@var[res; @http.post["https://api.example.com/items"; {"name": "test"}]]
@var[res; @http.auth_post["https://api.example.com"; data; "user"; "pass"]]
@http.upload["https://example.com/upload"; "file"; "document.pdf"]
@var[elapsed; @http.elapsed[res]]

@async[main]
    @var[res; @http.async_get["https://example.com"]]
@end
```

### File (`@file.*`) — read, write, copy, touch, symlink, stat

```clpy
@var[content; @file.read["data.txt"]]
@file.write["output.txt"; content]
@file.append["log.txt"; "new line\n"]
@file.touch["newfile.txt"]
@file.symlink["target.txt"; "link.txt"]
@file.copy["a.txt"; "b.txt"]
@var[stats; @file.stat["data.txt"]]
@var[files; @file.glob["*.txt"]]
```

### Date (`@date.*`) — format, parse, arithmetic, timezone, calendar

```clpy
@var[now; @date.now[]]
@var[formatted; @date.format[@date.now[]; "%Y-%m-%d %H:%M"]]
@var[parsed; @date.parse["2024-01-15"; "%Y-%m-%d"]]
@var[future; @date.add[@date.now[]; days=7; hours=2]]
@var[gap; @date.diff_days[future; @date.now[]]]
@var[tz_time; @date.to_timezone[@date.utcnow[]; "US/Eastern"]]
@var[week; @date.isoweek[@date.today[]]]
```

### Text (`@text.*`) — regex, encode, case, split, partition, slug

```clpy
@var[upper; @text.upper["hello"]]
@var[parts; @text.split["a,b,c"; ","]]
@var[before; @text.partition["foo-bar"; "-"]]
@var[slug; @text.slug["Hello World!"]]
@var[replaced; @text.sub["pattern"; "replacement"; "text"]]
@var[encoded; @text.encode["hello"]]
@var[is_digit; @text.is_numeric["123"]]
```

### Crypto (`@crypto.*`) — hash, hmac, pbkdf2, scrypt, token, UUID, base64

```clpy
@var[digest; @crypto.sha256["password"]]
@var[token; @crypto.token[32]]
@var[derived; @crypto.pbkdf2["password"; "salt"; 100000]]
@var[hashed; @crypto.scrypt["password"; "salt"]]
@var[id; @crypto.uuid[]]
@var[encoded; @crypto.b64_encode["data"]]
```

### Log (`@log.*`) — structured logging with file handlers, levels, formatters

This is for **your script's own** application logging:

```clpy
@log.setup["INFO"]
@log.info["Application started"]
@log.warning["Warning message"]
@log.error["Error occurred"]
@log.to_file["app.log"]
@var[logger; @log.get["myapp"]]
logger.debug("detail")
```

To write your application log straight to a file with one line:

```clpy
@log.setup["DEBUG"; "app.log"]     # level + file in one call
@log.info["written to app.log"]
```

### Config (`@config.*`) — JSON, TOML, INI, env

```clpy
@var[data; @config.load["config.json"]]
@var[value; @config.get["config.json"; "database"; "host"]]
@config.set["config.json"; "debug"; True]
@var[env_var; @config.env["DATABASE_URL"]]
@config.dotenv[".env"]
```

### Shell (`@shell.*`) — run commands, control processes, manage environment

```clpy
@var[result; @shell.run["ls -la"]]
@var[output; @shell.output["echo hello"]]
@var[lines; @shell.lines["ls"]]
@var[proc; @shell.bg["sleep 10"]]
@shell.kill[proc]
@shell.wait[proc]
@var[username; @shell.username[]]
@var[cpu_count; @shell.cpu_count[]]
```

### Archive (`@archive.*`) — zip, tar, gzip, bzip2, lzma

```clpy
@archive.zip["data/"; "data.zip"]
@archive.unzip["data.zip"; "extracted/"]
@archive.tar["data/"; "data.tar.gz"]
@archive.bzip2["file.txt"; "file.bz2"]
@archive.lzma["file.txt"; "file.xz"]
@var[names; @archive.zip_list["data.zip"]]
```

### Mail (`@mail.*`) — send/receive SMTP/IMAP

```clpy
@mail.send["user@example.com"; "Subject"; "Body"]
@mail.send_html["user@example.com"; "Subject"; "<h1>HTML</h1>"]
@var[imap; @mail.imap_connect["imap.gmail.com"; "user@gmail.com"; "password"]]
@var[folders; @mail.imap_list[imap]]
@var[ids; @mail.imap_search[imap; "UNSEEN"]]
@var[msg; @mail.imap_fetch[imap; id]]
@mail.imap_close[imap]
```

### More: JSON, Math, Time, Color, Store, CSV

```clpy
@var[text; @json.stringify[data]]
@var[r; @math.sqrt[16.0]]
@time.sleep[2]
@print[@color.green["Success!"]]
@store.set["key"; "value"]
@var[rows; @csv.read["data.csv"]]
```

### Python stdlib wrappers (20 namespaces, new in v2.1)

Direct, one-line access to the most-used Python standard libraries:

```clpy
# Randomness & sampling
@var[n; @random.randint[1; 100]]
@var[pick; @random.choice[items]]
@random.shuffle[deck]

# Collections & iterators
@var[counts; @collections.Counter["aabbc"]]
@var[q; @collections.deque[[1, 2, 3]]]
@var[combos; @itertools.combinations[items; 2]]
@var[flat; @itertools.flatten[nested]]

# Functional tools
@var[total; @functools.reduce[lambda a, b: a + b; nums]]
@var[add2; @functools.partial[add; 2]]

# Statistics
@var[avg; @statistics.mean[data]]
@var[mid; @statistics.median[data]]
@var[sd; @statistics.stdev[data]]

# Encoding & URLs
@var[enc; @base64.encode["hello"]]
@var[safe; @url.quote["a b c"]]
@var[qs; @url.encode[{"q": "cats"}]]

# Heaps, bisect, operator
@heapq.heapify[lst]
@var[lo; @bisect.bisect_left[sorted_lst; 5]]
@var[by_age; @operator.itemgetter[1]]

# System, IO, copy, pretty-print
@var[args; @sys.argv[]]
@var[buf; @io.StringIO[]]
@var[clone; @copy.deepcopy[obj]]
@var[pretty; @pprint.format[data]]
```

Full set: `@random` `@collections` `@itertools` `@functools` `@sys` `@io`
`@copy` `@base64` `@url` `@statistics` `@contextlib` `@enum` `@dataclasses`
`@typing` `@threading` `@queue` `@heapq` `@bisect` `@operator` `@pprint`.

### More stdlib wrappers (5 namespaces, new in v2.2)

```clpy
# Strings & templates
@var[chars; @string.ascii_letters[]]
@var[msg; @string.substitute["Hi $name"; {"name": "Bob"}]]
@var[id; @string.random[12]]

# Binary packing
@var[data; @struct.pack[">I"; 42]]
@var[vals; @struct.unpack[">I"; data]]

# Compression & checksums
@var[c; @zlib.compress[big_text]]
@var[sum; @zlib.crc32_hex["abc"]]

# Calendar math
@var[leap; @calendar.is_leap[2024]]
@var[days; @calendar.days_in_month[2024; 2]]

# Email messages
@var[m; @email.make["Hi"; "a@b.com"; "c@d.com"; "Hello!"]]
@var[ok; @email.valid_address["x@y.com"]]
```

New set: `@string` `@struct` `@zlib` `@calendar` `@email`.

### Data & format wrappers (10 namespaces, new in v2.4)

```clpy
# XML
@var[root; @xml.from_string["<a><b>hi</b></a>"]]
@var[txt; @xml.find_text[root; "b"]]

# TOML (read)
@var[cfg; @toml.loads["port = 8080"]]

# Fuzzy matching & diffs
@var[score; @diff.ratio["color"; "colour"]]
@var[best; @diff.best_match["colur"; ["color", "flavor"]]]

# Exact arithmetic (no float error)
@var[total; @decimal.add["0.1"; "0.2"]]   # → 0.3 exactly
@var[third; @fraction.make[1; 3]]          # → 1/3

# Networking, platform, text
@var[priv; @ip.is_private["10.0.0.1"]]     # → True
@var[os; @platform.system[]]
@var[clean; @unicode.strip_accents["café"]]  # → "cafe"
@var[args; @shlex.split["echo hello world"]]
```

New set: `@xml` `@toml` `@diff` `@decimal` `@fraction` `@ip` `@platform`
`@unicode` `@binascii` `@shlex`.

### Media & regex wrappers (4 namespaces, new in v2.5)

```clpy
# Regex (re module — no @import needed)
@var[m; @re.search["(\d+)"; "price: 42"]]
@var[n; @re.group1[m]]                         # "42"
@var[all; @re.findall["\w+"; "hello world"]]   # ["hello", "world"]
@var[out; @re.sub["[aeiou]"; "*"; "hello"]]    # "h*ll*"

# YAML (PyYAML)
@var[data; @yaml.loads["name: Alice\nage: 30"]]
@var[name; @yaml.get[data; "name"]]            # "Alice"
@var[text; @yaml.dumps[data]]

# Image (Pillow)
@var[img; @image.open["photo.png"]]
@var[w; @image.width[img]]
@var[resized; @image.resize[img; 800; 600]]
@image.save[resized; "resized.png"]

# PDF (pdfplumber)
@var[doc; @pdf.open["report.pdf"]]
@var[pages; @pdf.page_count[doc]]
@var[text; @pdf.text[doc]]                     # all text
@var[pg1; @pdf.text_of[doc; 0]]               # page 0 only
```

New set: `@re` `@yaml` `@image` `@pdf`.

### Shortcut plugins — shorter syntax for everything

Four configurable shortcut plugins let you drop the namespace prefix on common
operations and add hundreds of extra convenience methods. All four load
together without conflicts:

```clpy
# cruhon-shortcuts (base — every namespace)
@var[text; @read["notes.txt"]]            # @read → @file.read
@var[stamp; @now[]]                        # @now → @date.now
@var[id; @uuid[]]                          # @uuid → @crypto.uuid

# cruhon-shortcuts-pro (math / lists / dicts / text / logic)
@var[x; @clamp[value; 0; 100]]             # @clamp → @math.clamp
@var[slug; @snake_case["Hello World"]]     # @snake_case → @text.snake_case
@var[g; @group_by[items; key_fn]]          # @group_by → @collections.group_by

# cruhon-shortcuts-data (xml / toml / diff / decimal / fraction / ip / …)
@var[cfg; @toml_load["port = 8080"]]       # @toml_load → @toml.loads
@var[amt; @money["3.14159"]]               # @money → @decimal.money (2 dp)
@var[ok; @is_private_ip["10.0.0.1"]]       # @is_private_ip → @ip.is_private
# cruhon-shortcuts-data also covers @re, @yaml, @image, @pdf (v2.5 namespaces)
```

Each plugin is fully configurable in its `mod.json` — pick groups, toggle
global vs. method aliases, disable specific shortcuts, or add your own.

See [`library.md`](library.md) for the full reference on all 1100+ commands.

---

## v2.6 Language Commands — Templates, Pipelines, Spread/Unpack

### Templates

```clpy
@template[greeting]
    Hello, {name}! You have {count} messages.
@end

@var[msg; @render[greeting; name="Alice"; count=5]]
@print[{msg}]   # Hello, Alice! You have 5 messages.
```

### Pipelines

```clpy
@pipeline[normalize; str.strip; str.lower]
@var[result; @apply[normalize; "  Hello  "]]   # "hello"
```

### Multi-variable assignment

```clpy
@let[x; 10; y; 20; z; 30]   # x = 10, y = 20, z = 30
```

### Spread / unpack

```clpy
@var[n; @spread[max; [3, 1, 4, 1, 5]]]     # max(*[3,1,4,1,5]) → 5
@var[r; @unpack[dict; {"a": 1, "b": 2}]]   # dict(**{"a":1,"b":2})
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

If the value is a callable (no args), it is called **before each exec()** to
get the value. Otherwise the value is used as-is.

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

### `api.inject_once(key, factory)`

Like `api.inject()` with a factory, but the factory runs **once at
registration time** and the resulting object is shared across all script
runs. Use this for connection pools, singletons, or any expensive resource
that must persist between runs.

```python
def register(api):
    # One pool, reused by every run (NOT re-created each time)
    api.inject_once("pool", lambda: ConnectionPool(max_connections=10))
```

---

### Cleanup: `api.unregister_command` / `remove_hook` / `remove_inject` / `remove_eval_hook`

Every registration can be undone — useful for tests, conditional loading, or
plugins that reconfigure themselves at runtime.

```python
def register(api):
    api.override("print", my_print)
    api.hook("before_run", warm_cache)
    api.inject("db_pool", make_pool())
    api.eval_hook(dollar_env)

def teardown(api):
    api.unregister_command("print")     # restore default visitor
    api.remove_hook("before_run", warm_cache)
    api.remove_inject("db_pool")
    api.remove_eval_hook(dollar_env)
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
| `after_run` | `fn(source=str, python_code=str)` | After exec finishes (success) |
| `before_parse` | `fn(source) -> source` | Lexer pre-hook — modify source text |
| `after_parse` | `fn(ast) -> ast` | Parser post-hook — modify AST |
| `before_transpile` | `fn(ast) -> ast` | Transpiler pre-hook |
| `after_transpile` | `fn(code) -> code` | Modify generated Python code |
| `on_error` | `fn(error=exc)` | On **any** error — including `ParseError` and `RunError` |

```python
def register(api):
    api.hook("before_run",   lambda source: print("[run start]"))
    api.hook("after_run",    lambda source, python_code: print("[run end]"))
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

## Contact

- **Discord:** [discord.gg/SPf5VZ6QPG](https://discord.gg/SPf5VZ6QPG)
- **Email:** [cruciblelab@hotmail.com](mailto:cruciblelab@hotmail.com)
- **GitHub:** [github.com/cruciblelab](https://github.com/cruciblelab)

---

## License

MIT — CrucibleLab
