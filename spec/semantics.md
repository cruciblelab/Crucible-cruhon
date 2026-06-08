# Cruhon Semantics Specification

**Version:** 0.5  
**Status:** Stable  
**Frozen:** Yes — changes require a new minor version and test coverage

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
`@if` condition, `@for` iterable, `@while` condition, `@assert` condition.

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
@print[x]          → print("x")          (Rule 7b: identifier → string)
@print[{x}]        → print(f"{x}")       (Rule 2b: {var} → f-string)
@print[hello]      → print("hello")      (Rule 7b: identifier → string)
@print[Hello]      → print("Hello")      (Rule 7b: identifier → string)
@print[42]         → print(42)           (Rule 3: number)
@print[Hello {x}]  → print(f"Hello {x}") (Rule 2b: {var} in text)
```

**Summary:** In `@print`, bare words always print as strings.
Use `{varname}` to interpolate a variable's value.

---

### 1.4 Dict Literal vs Interpolation

A value starting with `{` followed by a `:` is treated as a dict literal (Rule 5).
A value starting with `{identifier}` without `:` is treated as f-string (Rule 2b).

```
@var[d; {"key": val}]    → dict literal (Rule 5)
@print[{x} found]        → f-string     (Rule 2b)
```

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

`;` separates `@command` arguments at the **top level** only.

```
@var[name; value]           ← ; separates name from value
@func[add; a; b]            ← ; separates func name from params
@if[x > 5]                  ← single arg, no ;
```

Inside argument values, use **Python's `,`** for function calls:

```
@var[r; add(3, 4)]           ✓  comma inside call
@var[r; add(3; 4)]           ✗  ParseError: unbalanced parentheses
```

Inside **quoted** string values, `;` is just a character:

```
@var[msg; "hello; world"]   ✓  fine — ; inside quotes is literal
```

The parser validates each argument for unbalanced parentheses after splitting on `;`.
An unbalanced `(` count signals that `;` was used inside a call by mistake.

---

## 4. Scope Rules

Cruhon has **no block scope**. All variables are function-scope (same as Python).
Variables declared inside `@if`, `@for`, `@while`, `@repeat` are visible
after the block ends.

```
@if[True]
    @var[x; 5]
@end
@print[{x}]    ← works — x is visible here
```

This matches Python's scoping rules exactly, since Cruhon transpiles to Python.

---

## 5. Core Command Immutability

The following commands are **frozen** and will never be renamed or removed:

```
@var       @const     @print     @if        @elif      @else
@for       @while     @func      @async     @return    @class
@try       @catch     @finally   @import    @break     @continue
@assert    @env       @include   @await     @end       @list
@dict      @repeat    @fetch
```

Library wrappers (`@http.*`, `@store.*`) are stable but may gain new methods.

---

## 6. Expression Passthrough

Conditions, iterables, and expressions inside `@command[...]` are passed
to Python **as-is**. Cruhon does not parse Python expressions — Python does.

```
@if[x > 5 and y < 10]         ← Python evaluates this
@for[i; range(0, 10, 2)]      ← Python evaluates this
@while[len(items) > 0]        ← Python evaluates this
@assert[result == expected]   ← Python evaluates this
```

Python syntax rules apply inside `[...]` for conditions and iterables.
Operators (`>`, `<`, `==`, `and`, `or`, etc.) are passed through unchanged.

---

## 7. Inline Command Resolution

Certain commands can be used as **inline expressions** inside `@var` values:

| Inline command | Resolves to |
|----------------|-------------|
| `@env[KEY]` | `os.environ.get("KEY")` |
| `@env[KEY; default]` | `os.environ.get("KEY", default)` |
| `@list[a; b; c]` | `[a, b, c]` |
| `@dict[k; v; ...]` | `{"k": v, ...}` |
| `@fetch[url]` | `requests.get(url)` |
| `@store.get[key]` | `__cruhon_store_get(key)` |
| `@http.get[url]` | `requests.get(url)` |

Required imports (`os`, `requests`, store helpers) are **auto-injected** when used.

---

## 8. Error Message Format

When a Cruhon program raises a runtime error, the message includes
the original Cruhon source line number:

```
NameError: name 'x' is not defined
  → at line 3 in main.clpy
```

The line number comes from a source map built during transpilation
(`_line_map: dict[python_line → cruhon_line]`).

---

*This specification is the authoritative reference for Cruhon v0.5+.*  
*Any change to evaluation rules requires updating this document and adding tests.*
