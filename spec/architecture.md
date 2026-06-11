# Cruhon Engine Architecture

**Version:** 2.0.0  
**Status:** Stable

---

## Philosophy

Cruhon is as free as Python, but easier.  
No artificial restrictions on what users can build.  
The only immutable things are the syntax contract.

---

## Engine Pipeline

Five machines. Each has one job.

```
.clpy source
    ↓
[Syntax Machine]    Lexer + SyntaxEngine + Parser
    ↓
[Semantic Machine]  _eval_value(value, context)
    ↓
[Transform Machine] Transpiler → Python source
    ↓
[Runtime Machine]   Runner → exec()
    ↑ ↓
[Extension Machine] ModLoader — hooks into pipeline
```

---

## Syntax Machine

### SyntaxEngine (introduced v0.6)

Single truth source for argument and expression parsing.  
File: `core/syntax_engine.py`

Both Lexer and Parser use this. No other code does depth-aware
argument splitting.

**Methods:**

| Method | Description |
|--------|-------------|
| `split_args(source) → list[str]` | Split a Cruhon argument string on top-level `;`. Handles depth (brackets, parens, braces) and strings. |
| `read_block(line, start) → (str, int)` | Read raw content until `]` or `;` at depth 0. Used by Lexer._read_raw. |
| `validate_arg(arg, line) → None` | Detect unbalanced parentheses; raise helpful ParseError. |

Before v0.6, `lexer.py` had `_read_raw()` (16 lines, depth-aware, no string handling)
and `parser.py` had `parse_args()` (54 lines, token-based, no depth awareness).
These produced inconsistent results for inputs like `@var[x; [1,2,3]]`.
SyntaxEngine unifies them.

### Lexer

Tokenizes `.clpy` source → token list.  
File: `core/lexer.py`  
`_read_raw()` delegates to `SyntaxEngine.read_block()`.

### Parser

Token list → AST.  
File: `core/parser.py`  
`parse_args()` delegates to `SyntaxEngine.split_args()`.

---

## Semantic Machine

Single evaluation function for all values.  
File: `core/transpiler.py` — `_eval_value(value, context)`

Two contexts:
- `"expr"` — right-hand side of `@var`, `@const`, `@return`, etc. Identifiers are variable references.
- `"display"` — `@print`, `@assert` message. Bare identifiers become string literals.

Priority order (8 rules):
1. Quoted string → string literal
2. Quoted/bare with `{var}` → f-string
3. Numeric literal → number
4. `True` / `False` / `None` → bool/None
5. Collection literal (`[`, `{`, `(`) → as-is
6. Python expression (operator/call/dot/subscript) → as-is
7. Single identifier → variable ref (expr) or string (display)
8. Bare text → string literal

See `spec/semantics.md` for full specification.

---

## Transform Machine

AST → Python source code via visitor pattern.  
File: `core/transpiler.py`

Each AST node has a `visit_*` method.  
Line map (`_line_map`) maps Python line numbers → Cruhon source lines for error messages.

---

## Runtime Machine

Runs the generated Python code.  
File: `core/runner.py`

Responsibilities:
- Resolve `@include` nodes before transpilation
- Auto-inject imports (`os`, `requests`, store helpers)
- Format `--show-python` output
- Translate Python exceptions to Cruhon line numbers

---

## Extension Machine

Deterministic plugin system.  
File: `core/mod_loader.py`

Load order (always enforced):
```
1. core       built-in (always first)
2. stdlib     built-in (always second)
3. pip mods   cruhon-* packages, sorted alphabetically
4. local mods mods/ subfolders, sorted alphabetically
```

Override chain: multiple mods overriding the same command form a middleware chain.
First loaded = outermost wrapper.

---

## Syntax Contract (immutable forever)

```
@command[arg; arg]   command format
@end                 block terminator
{var}                string interpolation
#                    comment prefix
.clpy                file extension
```

---

## Current Extension Points (v0.6)

```python
Parser.register_command(name, fn)
Parser.register_block_command(name, fn)
Lexer.add_pre_hook(fn)
Lexer.add_post_hook(fn)
Transpiler.register_visitor(node_class, fn)
Transpiler.add_pre_hook(fn)
Transpiler.add_post_hook(fn)
ModAPI.command(name, parser_fn, visitor_fn)
ModAPI.override(command, fn, warn=True)
ModAPI.hook(event, fn)
ModAPI.lib(name, python_module)
ModAPI.alias(alias_name, target)
ModAPI.namespace(ns)
```

---

## Future Roadmap (documentation only)

```
v0.7 — stdlib wrappers: @file @color @time @math @json
v0.8 — framework API and advanced extension points
v0.9 — community packages
v1.0 — spec freeze, compatibility lock
```
