# Cruhon Runtime Rules

**Version:** 2.7.0
**Status:** Stable

---

## 1. Determinism Contract

**Core rule:**
> Same source + same plugin set = always same output.

This is non-negotiable. Every decision in this document serves this rule.

---

## 2. Plugin Load Order (Deterministic)

Plugins always load in this exact order:

```
1. cruhon core         (always first, always wins base behavior)
2. cruhon stdlib       (official wrappers: @file, @http, @math, @re, @yaml, ...)
3. pip plugins         (cruhon-* packages, sorted alphabetically by name)
4. local mods/         (folders in mods/, sorted alphabetically by folder name)
```

**Why alphabetical for steps 3 and 4?**
Alphabetical order is deterministic across all machines and OS environments.
Random or discovery order is not.

The load order is fixed at startup and does not change during a run.
`cruhon mods` shows the current load order.

---

## 3. Override Resolution

When multiple plugins override the same command, the chain works like middleware:

```
@print[hello]

core print
  → plugin A override (colorize)
    → plugin B override (log)
      → final output
```

**Rules:**
- Load order determines chain order (earlier = outer wrapper)
- Last loaded plugin is closest to the original behavior
- Each override receives the previous handler as `next_fn`

```python
# Plugin A
def my_print(transpiler, node, next_fn):
    result = next_fn(transpiler, node)   # call next in chain
    return result
```

If a plugin does NOT call `next_fn`, the chain stops there.
This must be documented in the plugin's `mod.json`.

---

## 4. Conflict Rules

### 4.1 Namespace conflicts

Two plugins register the same namespace (e.g. both register `@db`):
- First loaded wins
- Second plugin gets a warning at load time and receives the existing namespace back:
  ```
  ⚠ [cruhon-db-alt] namespace 'db' already registered by [cruhon-db]. Using existing.
  ```

### 4.2 Alias conflicts

Two plugins register the same global alias (e.g. both map `@fetch`):
- Same rule: first loaded wins, second gets a warning

### 4.3 Override conflicts

Multiple plugins override the same core command:
- All overrides are chained (not conflicting) — see section 3
- No warning needed, this is expected behavior

### 4.4 Rewrite conflicts (shortcut plugins)

Two shortcut plugins registering the same source rewrite key:
- First loaded wins
- The second mapping is silently ignored
- Avoid registering rewrites that overlap with other known plugins

---

## 5. Version Compatibility

Every plugin must declare which Cruhon version it supports in `mod.json`:

```json
{
  "name": "cruhon-db",
  "cruhon": ">=1.0.0"
}
```

If a plugin requires a version newer than the installed Cruhon:
```
✗ [cruhon-db] requires cruhon >= 2.0.0, current is 1.5.0. Skipping.
```

Plugins can also declare inter-plugin dependencies:
```json
{
  "requires": ["cruhon-auth >= 1.0.0"]
}
```

---

## 6. AST Stability Contract

AST node field names are stable after they are defined.
Adding new fields to a node is allowed (with defaults).
Removing or renaming fields is a breaking change — requires a major version bump.

```python
# OK — backward compatible
@dataclass
class PrintNode(Node):
    value: Any = None
    color: str = ""   # new field, has default

# NOT OK — breaking change
@dataclass
class PrintNode(Node):
    content: Any = None  # renamed from 'value' — BREAKING
```

All custom nodes registered by plugins via `register_node()` must also follow this rule.

---

## 7. Lifecycle Hook Order (Guaranteed)

```
1. before_parse     (source string) → token pre-hooks
2. after_parse      (AST)           → AST post-hooks
3. before_transpile (AST)           → ast_hooks
4. after_transpile  (Python string)
5. before_exec      (Python string)
6. after_run        (source, python_code)
```

On error:
```
on_error (exception)
```

Hooks at the same event fire in plugin load order (deterministic — see section 2).
Multiple hooks registered for the same event by the same plugin fire in registration order.

---

## 8. Namespace Isolation Rules (v0.9)

Mod namespace objects (`api.namespace(name)`) follow these access rules:

| Method | Description |
|--------|-------------|
| `access_state(key)` | Read state from own namespace |
| `write_state(key, val)` | Write state to own namespace |
| `allow_peer(other_ns)` | Grant read access to another namespace |

A namespace cannot read another namespace's state without `allow_peer`.
Violating this raises a `NamespaceAccessError` at runtime.

---

## 9. Module System Rules (v1.6)

### 9.1 Encapsulation

Inside `@module[name]...@end`, all defined names are private by default.
Only names listed in `@export[...]` are accessible from outside.

```clpy
@module[math_utils]
    @func[_helper]    # private
        ...
    @end
    @func[square; x]  # public (exported below)
        @return[x * x]
    @end
    @export[square]
@end
```

### 9.2 Loading

`@use[path]` loads a `.clpy` file and makes its exports available under the file's
basename as an alias (or a custom alias with `@use[path as alias]`).

`@from[module; name1; name2 as alias]` imports specific names directly into scope.

### 9.3 Circular dependency detection

The parser detects circular `@use`/`@include` chains at parse time and raises
a `ParseError` rather than entering an infinite loop.

---

## 10. Context Variable Rules (v1.0)

`__ctx__` is a dict available in all exec globals:

```python
__ctx__["key"] = value   # set
__ctx__.get("key")       # read
```

In Cruhon source:
```clpy
@ctx.set[key; value]
@ctx[key]
```

`__ctx_stack__` is a list used by scoped block commands (`api.block_command(scoped=True)`)
to push/pop context per block entry/exit.

---

## 11. Plugin API Stability Contract

The following `ModAPI` methods are **frozen** (never renamed or removed):

```
command()      block_command()    override()     hook()
lib()          lib_call()         namespace()    alias()
inject()       expose()           consume()      require()
config()       is_loaded()
```

New methods may be added in minor versions.
Existing method signatures will not change — new parameters are always keyword-optional
with defaults.

---

## 12. What Never Changes (Frozen Forever)

These are frozen at v1.0 and will never change:

- `@command[args]` syntax
- `@end` as block terminator
- `;` as argument separator
- `{var}` as interpolation syntax
- `#` as comment prefix
- `.clpy` as file extension
- Core command names (see grammar.md section 3)
- AST base class interface (`Node.accept`, `Node.line`)
- `ModAPI` public method signatures listed in section 11

---

## 13. Semantic Freeze (from v0.5)

No change to value evaluation rules may be made without:

1. `_eval_value()` passing 100% of regression tests
2. `;` ambiguity fully resolved and documented
3. `display` vs `expr` context stable and tested
4. `semantics.md` updated and reviewed
5. All tests passing with zero warnings

Feature additions must be **additive only** — they cannot change how existing values
are evaluated. Any PR that modifies `_eval_value()`, `parse_args()`, or the context
rules requires new tests in `tests/test_semantics.clpy`.
