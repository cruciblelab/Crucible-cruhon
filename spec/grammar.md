# Cruhon Language Specification
**Version:** 2.7.0
**Author:** CrucibleLab
**Status:** Stable

---

## 1. What is Cruhon?

Cruhon is a scripting language that compiles to Python. It is not a replacement for Python — it is a friendlier surface layer designed to make common patterns concise without hiding the output.

**Core philosophy:**
- Simple things must be simple
- Complex things must be possible
- Everything is transparent (`--show-python` always works)
- The user should never feel trapped

**Pipeline:**
```
.clpy source
  → Lexer (tokens)
  → Parser (AST)
  → Transpiler (Python source)
  → exec() (runs)
```

---

## 2. Syntax Contract

### 2.1 Command format

Every Cruhon command starts with `@`:

```
@command[arg1; arg2; arg3]
```

- `@` prefix is mandatory
- Arguments are separated by `;`
- Commands with no arguments omit the brackets: `@break`, `@pass`, `@end`
- Named (keyword) arguments use `=` inside the brackets: `@print[a; b; sep=", "]`
- Positional arguments must come before named arguments

### 2.2 Block format

Every block opens with a command and closes with `@end`:

```
@if[condition]
    ...
@elif[other]
    ...
@else
    ...
@end
```

Some blocks accept an `@else` clause (loops, match). All blocks end with exactly one `@end`.

### 2.3 String interpolation

`{variable}` inside any string value produces an f-string:

```
@print[Hello, {name}!]
→ print(f"Hello, {name}!")
```

### 2.4 Indentation

4 spaces per level. Tabs are not recommended. Indentation mirrors the generated Python exactly.

### 2.5 Comments

```
# this is a comment
```

Standard Python-style line comments. No block comment syntax.

### 2.6 File format

| Property | Value |
|----------|-------|
| Extension | `.clpy` |
| Encoding | UTF-8 |
| Line endings | LF or CRLF |
| Semicolons | Only inside `[...]` as argument separator, never at end of lines |

---

## 3. Type Annotation Syntax (v2.7)

Version 2.7 introduces first-class type annotation support. Annotations are written inline as `name: type` in the first argument position of `@var`, `@const`, and `@func` parameter slots.

### 3.1 Annotated variable

```
@var[name: type; value]  → name: type = value
@var[name: type]         → name: type          # annotation-only, no assignment
```

### 3.2 Annotated constant

```
@const[NAME: type; value]  → NAME: type = value  # const
```

### 3.3 Annotated function parameters and return

```
@func[name; param: type; return=ReturnType]
→ def name(param: type) -> ReturnType:
```

The `return=` named argument extracts a return-type annotation. It is not passed as a positional parameter.

### 3.4 Type alias

```
@type[Name; Alias]  → Name = Alias  # type alias
```

### 3.5 Dataclass (v2.7)

`@dataclass` generates a decorated class with `from dataclasses import dataclass` injected automatically. An optional parent class can be supplied as a second argument.

```
@dataclass[Name]
    @var[field: type]
    @var[field: type; default]
@end

@dataclass[Name; Parent]   # with inheritance
    ...
@end
```

Output:

```python
from dataclasses import dataclass

@dataclass
class Name:
    field: type
    field: type = default
```

---

## 4. Assignment and Variables

| Command | Syntax | Python output |
|---------|--------|---------------|
| `@var` | `@var[name; value]` | `name = value` |
| `@var` (typed) | `@var[name: type; value]` | `name: type = value` |
| `@var` (annotation only) | `@var[name: type]` | `name: type` |
| `@const` | `@const[NAME; value]` | `NAME = value  # const` |
| `@const` (typed) | `@const[NAME: type; value]` | `NAME: type = value  # const` |
| `@let` | `@let[x; v1; y; v2; ...]` | `x = v1; y = v2` |
| `@inc` | `@inc[x]` | `x += 1` |
| `@inc` (by n) | `@inc[x; n]` | `x += n` |
| `@dec` | `@dec[x]` | `x -= 1` |
| `@dec` (by n) | `@dec[x; n]` | `x -= n` |
| `@swap` | `@swap[a; b]` | `a, b = b, a` |

**Examples:**

```
@var[count; 0]
→ count = 0

@var[score: int; 100]
→ score: int = 100

@var[items: list[int]]
→ items: list[int]

@const[MAX_RETRIES; 3]
→ MAX_RETRIES = 3  # const

@const[LIMIT: int; 500]
→ LIMIT: int = 500  # const

@let[x; 1; y; 2; z; 3]
→ x = 1; y = 2; z = 3

@inc[counter]
→ counter += 1

@inc[counter; 5]
→ counter += 5

@swap[a; b]
→ a, b = b, a
```

---

## 5. Type System

| Command | Syntax | Python output |
|---------|--------|---------------|
| `@type` | `@type[Name; Alias]` | `Name = Alias  # type alias` |
| `@dataclass` | `@dataclass[Name]` / `@end` | `@dataclass class Name:` |
| `@dataclass` (with parent) | `@dataclass[Name; Parent]` / `@end` | `@dataclass class Name(Parent):` |

**Type alias example:**

```
@type[Vector; list[float]]
→ Vector = list[float]  # type alias
```

**Dataclass example:**

```
@dataclass[Point]
    @var[x: float]
    @var[y: float]
    @var[label: str; ""]
@end

→ from dataclasses import dataclass

  @dataclass
  class Point:
      x: float
      y: float
      label: str = ""
```

---

## 6. Control Flow

### 6.1 Conditionals

| Command | Syntax | Python output |
|---------|--------|---------------|
| `@if` | `@if[condition]` | `if condition:` |
| `@elif` | `@elif[condition]` | `elif condition:` |
| `@else` | `@else` | `else:` |
| `@end` | `@end` | closes block |

```
@if[x > 0]
    @print[positive]
@elif[x < 0]
    @print[negative]
@else
    @print[zero]
@end
```

### 6.2 For loop

```
@for[var; iterable]
    ...
@else
    ...
@end
→ for var in iterable: / else:
```

### 6.3 While loop

```
@while[condition]
    ...
@else
    ...
@end
→ while condition: / else:
```

### 6.4 Repeat loop

Runs the body exactly `n` times with no loop variable exposed.

```
@repeat[n]
    ...
@end
→ for _cruhon_i in range(n):
      ...
```

### 6.5 Foreach (auto-index)

Provides an automatic index variable alongside the element variable. An optional `start` argument sets the starting index (default `0`).

```
@foreach[index; var; iterable]
    ...
@end
→ for index, var in enumerate(iterable):

@foreach[index; var; iterable; start]
    ...
@end
→ for index, var in enumerate(iterable, start):
```

### 6.6 Loop control

| Command | Python output |
|---------|---------------|
| `@break` | `break` |
| `@continue` | `continue` |
| `@pass` | `pass` |

---

## 7. Functions and Classes

### 7.1 Functions

```
@func[name; p1; p2]
    ...
@end
→ def name(p1, p2):
```

With type annotations and return type (v2.7):

```
@func[name; p1: int; p2: str; return=bool]
    ...
@end
→ def name(p1: int, p2: str) -> bool:
```

The `return=` named argument is consumed by the transpiler and becomes the `->` return annotation. It is never passed as a positional parameter.

### 7.2 Async functions

```
@async[name; p1]
    ...
@end
→ async def name(p1):
```

Same annotation syntax as `@func` applies, including `return=`.

### 7.3 Classes

```
@class[Name]
    ...
@end
→ class Name:

@class[Name; Parent]
    ...
@end
→ class Name(Parent):
```

### 7.4 Decorators

There are two decorator commands:

**`@decorator[expr]`** — a block-level command that accumulates one or more decorators and applies them to the immediately following `@func` or `@class`. Multiple decorator expressions can be supplied as additional arguments.

```
@decorator[staticmethod]
@func[helper; x]
    @return[x * 2]
@end
→ @staticmethod
  def helper(x):
      return x * 2
```

**`@decorate[expr]`** — a standalone statement that emits `@expr` at the current location (useful for applying decorators in contexts where the block form is not needed).

### 7.5 Return, yield, await

| Command | Syntax | Python output |
|---------|--------|---------------|
| `@return` | `@return[value]` | `return value` |
| `@yield` | `@yield[value]` | `yield value` |
| `@yield` | `@yield` | `yield` |
| `@yield.from` | `@yield.from[expr]` | `yield from expr` |
| `@await` | `@await[expr]` | `await expr` |

### 7.6 Scope declarations

| Command | Syntax | Python output |
|---------|--------|---------------|
| `@global` | `@global[x; y]` | `global x, y` |
| `@nonlocal` | `@nonlocal[x; y]` | `nonlocal x, y` |

---

## 8. Macros, Templates, and Pipelines

### 8.1 Macros

A macro is a named, reusable block that is inlined at call sites. It is not a Python function.

```
@macro[name; p1; p2]
    ...
@end

@call[name; arg1; arg2]
```

At each `@call` site, the macro body is expanded with arguments substituted inline. `@call` can also appear as an inline expression inside another command's argument list.

### 8.2 Templates

A template is a named string with `{key}` placeholders.

```
@template[greeting]
    Hello, {name}! You have {count} messages.
@end

@render[greeting; name=Alice; count=3]
→ "Hello, Alice! You have 3 messages."
```

`@render` can appear as a statement or inline as an expression inside another command.

### 8.3 Pipelines

A pipeline defines a named sequence of function compositions.

```
@pipeline[process; strip; lower; encode]

@apply[process; raw_input]
→ encode(lower(strip(raw_input)))
```

`@apply` can appear as a statement or inline as an expression.

### 8.4 Spread and unpack

| Command | Syntax | Python output |
|---------|--------|---------------|
| `@spread` | `@spread[fn; iter]` | `fn(*iter)` |
| `@unpack` | `@unpack[fn; dict]` | `fn(**dict)` |

---

## 9. Exceptions

### 9.1 Try / catch / finally

```
@try
    ...
@catch[ExcType; e]
    ...
@catch[OtherType; e]
    ...
@finally
    ...
@end
→ try:
  except ExcType as e:
  except OtherType as e:
  finally:
```

Multiple `@catch` clauses are supported. `@finally` is optional.

### 9.2 Raise

| Command | Syntax | Python output |
|---------|--------|---------------|
| `@raise` | `@raise` | `raise` (bare re-raise) |
| `@raise` | `@raise[ExcType; msg]` | `raise ExcType(msg)` |
| `@raise` (chained) | `@raise[ExcType; msg; from=cause]` | `raise ExcType(msg) from cause` |

### 9.3 Retry

Retries the body up to `n` times before re-raising.

```
@retry[3]
    ...
@end

@retry[3; ConnectionError]
    ...
@end
```

An optional exception type argument restricts which exception triggers a retry. All other exceptions propagate immediately.

### 9.4 Timeout

Runs the body with a wall-clock deadline in seconds.

```
@timeout[5.0]
    ...
@end
```

---

## 10. Context Managers

```
@with[expr as var]
    ...
@end
→ with expr as var:

@with[expr1 as var1; expr2 as var2]
    ...
@end
→ with expr1 as var1, expr2 as var2:
```

Multiple context expressions are separated by `;`.

---

## 11. Async Extensions

| Command | Syntax | Python output |
|---------|--------|---------------|
| `@async.for` | `@async.for[var; iterable]` / `@end` | `async for var in iterable:` |
| `@async.with` | `@async.with[expr as var]` / `@end` | `async with expr as var:` |

---

## 12. Pattern Matching

```
@match[value]
    @case[pattern]
        ...
    @case[n if n > 0]
        ...
    @default
        ...
@end
→ match value:
      case pattern:
      case n if n > 0:
      case _:
```

- `@case[pattern]` maps to `case pattern:`
- Guards are written inline: `@case[n if n > 0]`
- `@default` maps to `case _:`
- `@match` / `@end` wraps the block

---

## 13. I/O

| Command | Syntax | Python output |
|---------|--------|---------------|
| `@print` | `@print[value]` | `print(value)` |
| `@print` (multi) | `@print[a; b; sep=", "; end=""]` | `print(a, b, sep=", ", end="")` |
| `@input` | `@input[prompt]` | `input(prompt)` (inline or statement) |

`sep=` and `end=` are keyword arguments passed directly to `print()`.

---

## 14. Miscellaneous Statements

| Command | Syntax | Python output |
|---------|--------|---------------|
| `@del` | `@del[var1; var2]` | `del var1, var2` |
| `@assert` | `@assert[condition]` | `assert condition` |
| `@assert` (msg) | `@assert[condition; msg]` | `assert condition, msg` |
| `@env` | `@env[KEY]` | `os.environ.get("KEY")` |
| `@env` (default) | `@env[KEY; default]` | `os.environ.get("KEY", default)` |
| `@import` | `@import[lib]` | `import lib` |
| `@import` (alias) | `@import[lib as alias]` | `import lib as alias` |
| `@include` | `@include[file.clpy]` | inline source merge at parse time |
| `@raw` / `@end` | pass-through block | emits content verbatim as Python |

**Raw block:**

```
@raw
x = {"key": "value"}  # arbitrary Python
@end
```

Everything between `@raw` and `@end` is emitted verbatim into the output without parsing.

---

## 15. Module System

### 15.1 Define a module

```
@module[name]
    ...
@end
```

Groups definitions into a named module scope.

### 15.2 Export names

```
@export[name1; name2]
```

Marks `name1` and `name2` as part of the module's public API (`__all__`).

### 15.3 Load a module

```
@use[path]
@use[path as alias]
```

Loads a `.clpy` module from `path`. If no alias is given, the alias is derived from the last path segment (extension stripped, hyphens and dots converted to underscores).

### 15.4 Selective import

```
@from[module; name1; name2 as alias]
→ from module import name1, name2 as alias
```

---

## 16. Inline Expression Commands

These commands are usable inside `[...]` wherever a Python expression is expected (e.g., as the value argument to `@var`).

| Command | Syntax | Python output |
|---------|--------|---------------|
| `@list` | `@list[a; b; c]` | `[a, b, c]` |
| `@dict` | `@dict[k1; v1; k2; v2]` | `{k1: v1, k2: v2}` |
| `@set` | `@set[a; b; c]` | `{a, b, c}` |
| `@set` (empty) | `@set[]` | `set()` |
| `@tuple` | `@tuple[a; b]` | `(a, b)` |
| `@tuple` (single) | `@tuple[a]` | `(a,)` |
| `@tuple` (empty) | `@tuple[]` | `()` |
| `@comp` | `@comp[expr; var; iterable]` | `[expr for var in iterable]` |
| `@comp` (conditional) | `@comp[expr; var; iterable; cond]` | `[expr for var in iterable if cond]` |
| `@comp` (typed) | `@comp[expr; var; iterable; type=dict\|set\|gen]` | typed comprehension |
| `@dictcomp` | `@dictcomp[key; value; var; iterable]` | `{key: value for var in iterable}` |
| `@dictcomp` (cond) | `@dictcomp[key; value; var; iterable; cond]` | with `if cond` filter |
| `@setcomp` | `@setcomp[expr; var; iterable]` | `{expr for var in iterable}` |
| `@setcomp` (cond) | `@setcomp[expr; var; iterable; cond]` | with `if cond` filter |
| `@gencomp` | `@gencomp[expr; var; iterable]` | `(expr for var in iterable)` |
| `@gencomp` (cond) | `@gencomp[expr; var; iterable; cond]` | with `if cond` filter |
| `@pipe` | `@pipe[value; fn1; fn2]` | `fn2(fn1(value))` |
| `@when` | `@when[cond; if_true; if_false]` | `(if_true if cond else if_false)` |
| `@default` | `@default[value; fallback]` | `(value if value is not None else fallback)` |
| `@lambda` | `@lambda[params; body]` | `(lambda params: body)` |
| `@lambda` (no params) | `@lambda[body]` | `(lambda: body)` |
| `@fetch` | `@fetch[url]` | `requests.get(url)` |
| `@env` | `@env[KEY]` | `os.environ.get("KEY")` |
| `@env` (default) | `@env[KEY; default]` | `os.environ.get("KEY", default)` |
| `@ctx` | `@ctx[key]` | `__ctx__.get(key, None)` |
| `@ctx` (default) | `@ctx[key; default]` | `__ctx__.get(key, default)` |
| `@input` | `@input[prompt]` | `input("prompt")` |
| `@call` | `@call[name; arg1; ...]` | invoke macro inline |
| `@render` | `@render[name; key=val]` | rendered template string |
| `@apply` | `@apply[name; value]` | pipeline result |
| `@spread` | `@spread[fn; iter]` | `fn(*iter)` |
| `@unpack` | `@unpack[fn; dict]` | `fn(**dict)` |

**`@comp` type values:**

| `type=` value | Output form |
|---------------|-------------|
| *(omitted)* | `[expr for var in iterable]` (list) |
| `dict` | `{expr for var in iterable}` |
| `set` | `{expr for var in iterable}` |
| `gen` or `generator` | `(expr for var in iterable)` |

**Namespace method calls:**

Any plugin-registered or stdlib namespace can be called inline:

```
@ns.method[args]
```

For example, `@http.get[url]`, `@db.query[sql]`, `@math.sqrt[16]`.

---

## 17. Named Parameters

Named parameters use `key=value` syntax inside `[...]` and must always be placed after positional arguments.

**Rules:**
- `return=` in `@func` / `@async` is consumed as a return-type annotation; it never becomes a positional parameter
- `sep=` and `end=` in `@print` are passed as keyword arguments to `print()`
- `key=value` pairs in `@render` populate template placeholders
- `from=` in `@raise` specifies the exception cause (`raise X from cause`)
- Any unrecognised `key=value` pair in a user-facing command is forwarded as a Python keyword argument

**Examples:**

```
@func[add; a: int; b: int; return=int]
→ def add(a: int, b: int) -> int:

@print[x; y; sep=" | "; end="\n\n"]
→ print(x, y, sep=" | ", end="\n\n")

@render[email_tmpl; name=Alice; subject=Hello]
→ (rendered string)

@raise[ValueError; bad input; from=original_exc]
→ raise ValueError("bad input") from original_exc
```

---

## 18. Complete Command Reference

### 18.1 Assignment and variables

| Command | Arguments | Python output |
|---------|-----------|---------------|
| `@var` | `name; value` | `name = value` |
| `@var` | `name: type; value` | `name: type = value` |
| `@var` | `name: type` | `name: type` |
| `@const` | `NAME; value` | `NAME = value  # const` |
| `@const` | `NAME: type; value` | `NAME: type = value  # const` |
| `@let` | `x; v1; y; v2; ...` | `x = v1; y = v2` |
| `@inc` | `x` | `x += 1` |
| `@inc` | `x; n` | `x += n` |
| `@dec` | `x` | `x -= 1` |
| `@dec` | `x; n` | `x -= n` |
| `@swap` | `a; b` | `a, b = b, a` |

### 18.2 Type system

| Command | Arguments | Python output |
|---------|-----------|---------------|
| `@type` | `Name; Alias` | `Name = Alias  # type alias` |
| `@dataclass` | `Name` (block) | `@dataclass class Name:` |
| `@dataclass` | `Name; Parent` (block) | `@dataclass class Name(Parent):` |

### 18.3 Control flow

| Command | Arguments | Python output |
|---------|-----------|---------------|
| `@if` | `condition` (block) | `if condition:` |
| `@elif` | `condition` | `elif condition:` |
| `@else` | — | `else:` |
| `@for` | `var; iterable` (block) | `for var in iterable:` |
| `@while` | `condition` (block) | `while condition:` |
| `@repeat` | `n` (block) | `for _cruhon_i in range(n):` |
| `@foreach` | `index; var; iterable` (block) | `for index, var in enumerate(iterable):` |
| `@foreach` | `index; var; iterable; start` (block) | `for index, var in enumerate(iterable, start):` |
| `@break` | — | `break` |
| `@continue` | — | `continue` |
| `@pass` | — | `pass` |
| `@end` | — | closes block |

### 18.4 Functions and classes

| Command | Arguments | Python output |
|---------|-----------|---------------|
| `@func` | `name; p1; ...; return=T` (block) | `def name(p1, ...) -> T:` |
| `@async` | `name; p1; ...; return=T` (block) | `async def name(p1, ...) -> T:` |
| `@class` | `Name` or `Name; Parent` (block) | `class Name:` / `class Name(Parent):` |
| `@decorator` | `expr` (block) | `@expr` applied to next definition |
| `@decorate` | `expr` | `@expr` statement |
| `@return` | `value` | `return value` |
| `@yield` | `value` or — | `yield value` / `yield` |
| `@yield.from` | `expr` | `yield from expr` |
| `@await` | `expr` | `await expr` |
| `@global` | `x; y` | `global x, y` |
| `@nonlocal` | `x; y` | `nonlocal x, y` |

### 18.5 Macros, templates, pipelines

| Command | Arguments | Description |
|---------|-----------|-------------|
| `@macro` | `name; p1; ...` (block) | define named macro |
| `@call` | `name; arg1; ...` | invoke macro (statement or inline) |
| `@template` | `name` (block) | define string template |
| `@render` | `name; key=val; ...` | render template (statement or inline) |
| `@pipeline` | `name; fn1; fn2; ...` | define function pipeline |
| `@apply` | `name; value` | apply pipeline (statement or inline) |
| `@spread` | `fn; iter` | `fn(*iter)` |
| `@unpack` | `fn; dict` | `fn(**dict)` |

### 18.6 Exceptions

| Command | Arguments | Python output |
|---------|-----------|---------------|
| `@try` | — (block) | `try:` |
| `@catch` | `ExcType; e` | `except ExcType as e:` |
| `@finally` | — | `finally:` |
| `@raise` | — | `raise` (bare re-raise) |
| `@raise` | `ExcType; msg` | `raise ExcType(msg)` |
| `@raise` | `ExcType; msg; from=cause` | `raise ExcType(msg) from cause` |
| `@retry` | `n` or `n; ExcType` (block) | retry body up to n times |
| `@timeout` | `seconds` (block) | wall-clock deadline |

### 18.7 Context managers

| Command | Arguments | Python output |
|---------|-----------|---------------|
| `@with` | `expr as var; ...` (block) | `with expr as var, ...:` |
| `@async.with` | `expr as var` (block) | `async with expr as var:` |

### 18.8 Async

| Command | Arguments | Python output |
|---------|-----------|---------------|
| `@async` | `name; p1` (block) | `async def name(p1):` |
| `@async.for` | `var; iterable` (block) | `async for var in iterable:` |
| `@async.with` | `expr as var` (block) | `async with expr as var:` |
| `@await` | `expr` | `await expr` |

### 18.9 Pattern matching

| Command | Arguments | Python output |
|---------|-----------|---------------|
| `@match` | `value` (block) | `match value:` |
| `@case` | `pattern` or `pattern if guard` | `case pattern:` |
| `@default` | — | `case _:` |

### 18.10 I/O

| Command | Arguments | Python output |
|---------|-----------|---------------|
| `@print` | `value` or `a; b; sep=...; end=...` | `print(...)` |
| `@input` | `prompt` | `input(prompt)` |

### 18.11 Miscellaneous

| Command | Arguments | Python output |
|---------|-----------|---------------|
| `@del` | `var1; var2` | `del var1, var2` |
| `@assert` | `condition` or `condition; msg` | `assert condition[, msg]` |
| `@env` | `KEY` or `KEY; default` | `os.environ.get(...)` |
| `@import` | `lib` or `lib as alias` | `import lib` |
| `@include` | `file.clpy` | inline source merge |
| `@raw` / `@end` | — | verbatim Python pass-through |

### 18.12 Module system

| Command | Arguments | Description |
|---------|-----------|-------------|
| `@module` | `name` (block) | define module scope |
| `@export` | `name1; name2` | set `__all__` entries |
| `@use` | `path` or `path as alias` | load `.clpy` module |
| `@from` | `module; name1; name2 as alias` | selective import |

### 18.13 Inline expressions

| Command | Arguments | Python output |
|---------|-----------|---------------|
| `@list` | `a; b; c` | `[a, b, c]` |
| `@dict` | `k1; v1; k2; v2` | `{k1: v1, k2: v2}` |
| `@set` | `a; b; c` | `{a, b, c}` |
| `@tuple` | `a; b` | `(a, b)` |
| `@comp` | `expr; var; iterable[; cond][; type=...]` | comprehension |
| `@dictcomp` | `key; value; var; iterable[; cond]` | dict comprehension |
| `@setcomp` | `expr; var; iterable[; cond]` | set comprehension |
| `@gencomp` | `expr; var; iterable[; cond]` | generator expression |
| `@pipe` | `value; fn1; fn2` | `fn2(fn1(value))` |
| `@when` | `cond; if_true; if_false` | ternary expression |
| `@default` | `value; fallback` | `value` if not None, else `fallback` |
| `@lambda` | `[params;] body` | `(lambda params: body)` |
| `@fetch` | `url` | `requests.get(url)` |
| `@env` | `KEY[; default]` | `os.environ.get(...)` |
| `@ctx` | `key[; default]` | `__ctx__.get(key, ...)` |
| `@input` | `prompt` | `input("prompt")` |
| `@call` | `name; arg1; ...` | macro invocation |
| `@render` | `name; key=val` | rendered template |
| `@apply` | `name; value` | pipeline result |
| `@spread` | `fn; iter` | `fn(*iter)` |
| `@unpack` | `fn; dict` | `fn(**dict)` |

---

## 19. Example Programs

### 19.1 Typed function with annotations

```
@func[greet; name: str; times: int; return=str]
    @var[msg; "Hello, {name}!"]
    @return[@pipe[msg; str.strip] * times]
@end
```

Output:

```python
def greet(name: str, times: int) -> str:
    msg = f"Hello, {name}!"
    return str.strip(msg) * times
```

### 19.2 Dataclass

```
@dataclass[User]
    @var[id: int]
    @var[name: str]
    @var[active: bool; True]
@end
```

Output:

```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    active: bool = True
```

### 19.3 Pattern matching with guard

```
@match[status]
    @case[200]
        @print[OK]
    @case[n if n >= 400]
        @print[Error: {n}]
    @default
        @print[Unknown]
@end
```

### 19.4 Retry with exception type

```
@retry[3; TimeoutError]
    @var[result; @fetch[https://api.example.com/data]]
@end
```

### 19.5 Pipeline and template

```
@pipeline[normalise; str.strip; str.lower]

@template[welcome]
    Welcome, {name}. Your plan is {plan}.
@end

@var[raw; "  Alice  "]
@var[name; @apply[normalise; raw]]
@print[@render[welcome; name=name; plan=pro]]
```

### 19.6 Foreach with start index

```
@foreach[i; item; items; 1]
    @print[{i}. {item}]
@end
→ for i, item in enumerate(items, 1):
      print(f"{i}. {item}")
```

### 19.7 Comprehensions

```
# list comprehension
@var[squares; @comp[x*x; x; range(10)]]
→ squares = [x*x for x in range(10)]

# filtered list comprehension
@var[evens; @comp[x; x; range(20); x % 2 == 0]]
→ evens = [x for x in range(20) if x % 2 == 0]

# dict comprehension (dedicated command)
@var[sq_map; @dictcomp[x; x*x; x; range(5)]]
→ sq_map = {x: x*x for x in range(5)}

# generator expression
@var[gen; @comp[x*2; x; data; type=gen]]
→ gen = (x*2 for x in data)
```

### 19.8 Async with context manager

```
@async[fetch_all; urls: list]
    @async.with[aiohttp.ClientSession() as session]
        @async.for[url; urls]
            @var[resp; @await[session.get(url)]]
            @print[@await[resp.text()]]
        @end
    @end
@end
```

### 19.9 Module and export

```
@module[utils]
    @func[clamp; val; lo; hi; return=float]
        @return[max(lo, min(val, hi))]
    @end

    @export[clamp]
@end
```

### 19.10 Exception chaining and bare re-raise

```
@try
    @var[data; risky_operation()]
@catch[ValueError; e]
    @raise[RuntimeError; failed to process; from=e]
@end

# bare re-raise
@try
    @var[x; int(raw)]
@catch[ValueError; e]
    @print[converting: {raw}]
    @raise
@end
```

---

## 20. Plugin Contract

### 20.1 What plugins can do

- Add new namespaced commands: `@http.get`, `@db.query`
- Add aliases: `@fetch` → `@http.get`
- Add library wrappers: `register_lib("redis", "redis")`
- Hook into lifecycle events (pre/post hooks on lexer, parser, AST)
- Override core commands (with explicit warning)
- Register new inline expression commands via `register_inline_command()`
- Register new block commands via `register_block_command()`

### 20.2 What plugins cannot do

- Remove core commands
- Rename core commands
- Change `@end` block syntax
- Change `[arg; arg]` argument syntax
- Change `{var}` interpolation syntax

### 20.3 Override rules

Plugins may override core commands only explicitly:

```python
api.override("print", my_fn, warn=True)
# [plugin-name] overrides @print
```

Override order is deterministic — see `rules.md`.

---

## 21. Changelog: v0.9 → v2.7.0

| Area | Change |
|------|--------|
| `@var` / `@const` | Added `name: type` annotation syntax |
| `@var` | Added annotation-only form (no value) |
| `@func` / `@async` | Added `return=type` named argument for return annotation |
| `@func` params | `param: type` passed through as Python annotation |
| `@type` | New — type alias command |
| `@dataclass` | New — generates `@dataclass` class with field annotations; optional parent argument |
| `@repeat` | New — fixed-count loop with no loop variable |
| `@foreach` | New — enumerate loop with automatic index; optional start argument |
| `@match` / `@case` / `@default` | New — structural pattern matching |
| `@retry` | New — retry-on-exception block |
| `@timeout` | New — wall-clock deadline block |
| `@macro` / `@call` | New — inline macro definition and invocation |
| `@template` / `@render` | New — named string templates |
| `@pipeline` / `@apply` | New — function composition pipelines |
| `@async.for` / `@async.with` | New — async loop and context manager |
| `@yield.from` | New — `yield from` |
| `@raise` | Added bare re-raise form; added `from=cause` for exception chaining |
| `@catch` | Multi-catch: multiple `@catch` clauses per `@try` |
| `@with` | Multi-context: multiple `expr as var` separated by `;` |
| `@let` | New — multi-assignment |
| `@inc` / `@dec` | Added optional step argument |
| `@swap` | New |
| `@del` | New |
| `@global` / `@nonlocal` | New |
| `@decorator` | New — accumulates decorators for the next `@func` / `@class` |
| `@decorate` | New — standalone decorator statement |
| `@module` / `@export` / `@use` / `@from` | New — module system |
| `@list` / `@dict` / `@set` / `@tuple` | New inline constructors |
| `@comp` | New — comprehension with optional filter condition and `type=` selector |
| `@dictcomp` / `@setcomp` / `@gencomp` | New — dedicated comprehension commands with optional filter |
| `@pipe` / `@when` / `@lambda` | New inline expression commands |
| `@default` | New inline — `value if value is not None else fallback` |
| `@ctx` | New inline — context dict lookup |
| `@spread` / `@unpack` | New |
| `@raw` | New — verbatim Python pass-through block |
| `@import` | Added `as alias` form |
| `@catch` syntax | Now `@catch[ExcType; e]` instead of `@catch[e]` |
