# Cruhon Language Specification
**Version:** 0.9  
**Author:** CrucibleLab  
**Status:** Stable

---

## 1. What is Cruhon?

Cruhon is a scripting language that compiles to Python.
It is NOT a replacement for Python — it is a friendlier surface layer.

**Core philosophy:**
- Simple things must be simple
- Complex things must be possible
- Everything is transparent (--show-python always works)
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

## 2. Syntax Contract (FROZEN after v1.0)

### 2.1 Command format
Every Cruhon command starts with `@`:
```
@command[arg1; arg2; arg3]
```
- `@` prefix is mandatory
- Arguments separated by `;`
- No arguments: `@break` (no brackets needed)

### 2.2 Block format
Every block opens with a command and closes with `@end`:
```
@if[condition]
    ...
@end

@func[name; param1; param2]
    ...
@end
```

### 2.3 String interpolation
`{variable}` inside any string value:
```
@print[Hello, {name}!]
→ print(f"Hello, {name}!")
```

### 2.4 Indentation
Python-style — 4 spaces per level. Tabs not recommended.

---

## 3. Core Commands (IMMUTABLE — never removed or renamed)

These commands are the foundation. Plugins CANNOT remove or rename them.

| Command | Syntax | Python output |
|---------|--------|---------------|
| `@var` | `@var[name; value]` | `name = value` |
| `@const` | `@const[NAME; value]` | `NAME = value  # const` |
| `@print` | `@print[value]` | `print(value)` |
| `@input` | `@input[prompt]` | `input(prompt)` |
| `@if` | `@if[condition]` | `if condition:` |
| `@elif` | `@elif[condition]` | `elif condition:` |
| `@else` | `@else` | `else:` |
| `@for` | `@for[var; iterable]` | `for var in iterable:` |
| `@while` | `@while[condition]` | `while condition:` |
| `@func` | `@func[name; p1; p2]` | `def name(p1, p2):` |
| `@async` | `@async[name; p1]` | `async def name(p1):` |
| `@return` | `@return[value]` | `return value` |
| `@class` | `@class[name; parent]` | `class name(parent):` |
| `@try` | `@try` | `try:` |
| `@catch` | `@catch[e]` | `except Exception as e:` |
| `@finally` | `@finally` | `finally:` |
| `@import` | `@import[lib]` | `import lib` |
| `@break` | `@break` | `break` |
| `@continue` | `@continue` | `continue` |
| `@assert` | `@assert[cond; msg]` | `assert cond, "msg"` |
| `@env` | `@env[KEY; default]` | `os.environ.get(KEY, default)` |
| `@include` | `@include[file.clpy]` | inline source merge |
| `@await` | `@await[expr]` | `await expr` |
| `@end` | `@end` | closes block |

---

## 4. Expression Rules

Inside `[...]`, expressions are passed through as raw Python:
```
@if[x > 5]          → if x > 5:
@var[y; a + b * c]  → y = a + b * c
@for[i; range(10)]  → for i in range(10):
```

This is intentional — Cruhon does not reimplement Python's expression engine.

---

## 5. Plugin Contract

### 5.1 What plugins CAN do
- Add new namespaced commands: `@http.get`, `@db.query`
- Add aliases: `@fetch` → `@http.get`
- Add library wrappers: `register_lib("redis", "redis")`
- Hook into lifecycle events
- Override core commands (with warning)

### 5.2 What plugins CANNOT do
- Remove core commands
- Rename core commands
- Change `@end` block syntax
- Change `[arg; arg]` argument syntax
- Change `{var}` interpolation syntax

### 5.3 Override rules
Plugins may override core commands only explicitly:
```python
api.override("print", my_fn, warn=True)
# ⚠ [plugin-name] overrides @print
```
Override order is deterministic — see rules.md.

---

## 6. File Format

- Extension: `.clpy`
- Encoding: UTF-8
- Comments: `# this is a comment`
- No semicolons at end of lines
