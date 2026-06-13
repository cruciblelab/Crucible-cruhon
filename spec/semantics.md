# Cruhon Semantics Specification

**Version:** 2.7.0
**Status:** Stable
**Frozen:** Yes — changes to evaluation rules require a new minor version and full test coverage

---

## 1. Value Evaluation Model

Every value in Cruhon is evaluated according to a context.
There are two contexts: `expr` and `display`.

The evaluation is performed by a single function — `_eval_value(value, context)` —
which applies the following rules in strict priority order.

---

### 1.1 Evaluation Priority (both contexts)

| Priority | Condition | Result |
|----------|-----------|--------|
| 1 | Quoted string, no `{}` inside | String literal as-is |
| 2a | Quoted string with `{var}` | f-string |
| 2b | Unquoted with `{var}` (not a dict literal) | f-string |
| 3 | Numeric literal (integer or float) | Number as-is |
| 4 | `True`, `False`, or `None` | Python bool/None as-is |
| 5 | Collection literal (starts with `[`, `{`, `(`) | Python collection as-is |
| 6 | Python expression (operator, call, dot, subscript) | Expression as-is |
| 7a | [expr context] Single identifier | Python identifier (variable reference) |
| 7b | [display context] Single identifier | String literal `"ident"` |
| 8 | Anything else | String literal `"text"` |

---

### 1.2 Expr Context

Used in: `@var` value, `@const` value, `@return` value, `@fetch` url,
`@if` condition, `@for` iterable, `@while` condition, `@assert` condition,
`@yield` value, `@raise` arguments.

In expr context, Rule 7 preserves identifiers as Python variable references:

```
@var[name; "Alice"]    → name = "Alice"         (Rule 1: quoted string)
@var[x; 42]            → x = 42                 (Rule 3: number)
@var[ok; True]         → ok = True              (Rule 4: bool)
@var[copy; name]       → copy = name            (Rule 7a: identifier → variable)
@var[result; add(3,4)] → result = add(3, 4)     (Rule 6: function call)
@var[msg; hello world] → msg = "hello world"    (Rule 8: bare text)
```

---

### 1.3 Display Context

Used in: `@print` value, `@assert` message.

Display context is identical to expr context **except** for Rule 7:
a single identifier is treated as a string literal, NOT a variable reference.

To print a variable in display context, use `{var}` interpolation:

```
@print[x]          → print("x")           (Rule 7b: identifier → string)
@print[{x}]        → print(f"{x}")        (Rule 2b: {var} → f-string)
@print[42]         → print(42)            (Rule 3: number)
@print[Hello {x}]  → print(f"Hello {x}") (Rule 2b: {var} in text)
```

**Summary:** In `@print`, bare words always print as strings.
Use `{varname}` to interpolate a variable's value.

---

### 1.4 Dict Literal vs Interpolation

A value starting with `{` followed by a `:` is treated as a dict literal (Rule 5).
A value starting with `{identifier}` without `:` is treated as an f-string (Rule 2b).

```
@var[d; {"key": val}]    → dict literal (Rule 5)
@print[{x} found]        → f-string     (Rule 2b)
```

This detection is implemented by `_is_python_expression()` and
`_is_fstring_template()` helpers in the transpiler.

---

## 2. String Interpolation

`{varname}` inside any string value (quoted or bare) triggers f-string generation.
This works in both `expr` and `display` contexts.

```
@var[msg; "Hello, {name}!"]  → msg = f"Hello, {name}!"
@print[Hello, {name}!]       → print(f"Hello, {name}!")
@var[x; "value is {n}"]      → x = f"value is {n}"
```

Curly braces in dict literals are NOT interpolation:

```
@var[d; {"key": val}]        → d = {"key": val}   (no f-string)
```

---

## 3. Argument Separator Rule

`;` separates `@command` arguments at the **top level only**.
Depth tracking (brackets, parentheses, braces, quotes) ensures nested `;` are not split.

```
@var[name; value]              ← ; separates name from value
@func[add; a; b]               ← ; separates func name from params
@if[x > 5]                     ← single arg, no ;
@var[pairs; {"a": 1; "b": 2}]  ← ; inside braces is NOT a separator
```

Inside **quoted** strings, `;` is just a character:

```
@var[msg; "hello; world"]   ✓  fine — ; inside quotes is literal
```

The `SyntaxEngine` handles all depth-aware splitting. Unbalanced parentheses
trigger a `ParseError` with a helpful hint.

---

## 4. Named Parameters

Some commands support `key=value` syntax for keyword arguments:

```
@print[a; b; sep=", "; end=""]    → print(a, b, sep=", ", end="")
@render[tmpl; name="Alice"]       → render with key=value substitutions
@func[add; a; b; return=int]      → def add(a, b) -> int:
```

Named args are extracted from the positional arg list by `SyntaxEngine.split_named_args()`.
They do NOT affect the argument count for positional matching.

---

## 5. Type Annotation Context (v2.7)

`@var` and `@const` support type annotations by embedding `: type` in the name argument:

```
@var[x: int; 42]              → x: int = 42
@var[x: int]                  → x: int          (annotation-only, no value)
@const[MAX: int; 100]         → MAX: int = 100  # const
@var[items: list[int]]        → items: list[int]
@var[val: int | None; None]   → val: int | None = None
```

The parser splits `"x: int"` into `name="x"` and `type_hint="int"` on the first `: ` (space required).
The type string is passed through as-is to the Python output — Cruhon does not validate types.

`@func` params also pass through type annotations:

```
@func[add; a: int; b: int; return=int]  → def add(a: int, b: int) -> int:
```

---

## 6. Scope Rules

Cruhon has **no block scope**. All variables are function-scope (same as Python).
Variables declared inside `@if`, `@for`, `@while`, `@repeat` are visible after the block.

```
@if[True]
    @var[x; 5]
@end
@print[{x}]    ← works — x is visible here
```

Module scope (`@module[name]...@end`) creates an isolated encapsulation layer.
Symbols inside a module are not accessible outside unless exported with `@export`.

---

## 7. Core Command Immutability

The following commands are **frozen** and will never be renamed or removed:

```
@var       @const     @print     @if        @elif      @else
@for       @while     @func      @async     @return    @class
@try       @catch     @finally   @import    @break     @continue
@assert    @env       @include   @await     @end       @list
@dict      @repeat    @fetch     @pass      @del       @raise
@global    @nonlocal  @yield     @with      @match
```

Commands added after v1.0 are stable but not in the frozen set:
`@let`, `@macro`, `@call`, `@template`, `@render`, `@pipeline`, `@apply`,
`@spread`, `@unpack`, `@retry`, `@timeout`, `@module`, `@export`, `@use`,
`@from`, `@foreach`, `@inc`, `@dec`, `@swap`, `@decorate`, `@raw`,
`@type`, `@dataclass`.

Library wrappers (`@http.*`, `@file.*`, etc.) are stable but may gain new methods.

---

## 8. Expression Passthrough

Conditions, iterables, and expressions inside `@command[...]` are passed
to Python **as-is**. Cruhon does not parse Python expressions — Python does.

```
@if[x > 5 and y < 10]        ← Python evaluates this
@for[i; range(0, 10, 2)]     ← Python evaluates this
@while[len(items) > 0]       ← Python evaluates this
@assert[result == expected]  ← Python evaluates this
```

Python syntax rules apply inside `[...]` for conditions and iterables.

---

## 9. Inline Command Resolution

Certain commands can be used as **inline expressions** inside argument values:

| Inline command | Resolves to |
|----------------|-------------|
| `@env[KEY]` | `os.environ.get("KEY")` |
| `@env[KEY; default]` | `os.environ.get("KEY", default)` |
| `@list[a; b; c]` | `[a, b, c]` |
| `@dict[k; v; ...]` | `{"k": v, ...}` |
| `@set[a; b]` | `{a, b}` |
| `@tuple[a; b]` | `(a, b)` |
| `@fetch[url]` | `requests.get(url)` |
| `@input[prompt]` | `input(prompt)` |
| `@render[tmpl; k=v]` | template render expression |
| `@apply[pipe; val]` | pipeline apply expression |
| `@spread[fn; iter]` | `fn(*iter)` |
| `@unpack[fn; dict]` | `fn(**dict)` |
| `@comp[expr; var; iter]` | list/dict/set/gen comprehension |
| `@pipe[v; fn1; fn2]` | chained function calls |
| `@when[cond; a; b]` | `(a if cond else b)` |
| `@lambda[params; body]` | `(lambda params: body)` |
| `@ns.method[args]` | stdlib or mod namespace call |

Required imports (`os`, `requests`, store helpers) are **auto-injected** when used.

---

## 10. Error Attribution

When a Cruhon program raises a runtime error, the message includes
the original Cruhon source line number:

```
NameError: name 'x' is not defined
  → at line 3 in main.clpy
```

The line number comes from a source map built during transpilation
(`_line_map: dict[python_line → cruhon_line]`).

The Diagnostics Machine enriches errors further with a source excerpt,
caret pointer, plain-language hint, and spelling suggestions.

---

*This specification is the authoritative reference for Cruhon value evaluation.*
*Any change to evaluation rules requires updating this document and adding regression tests.*
