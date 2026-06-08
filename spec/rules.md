# Cruhon Runtime Rules
**Version:** 0.9  
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
2. cruhon stdlib       (official wrappers: requests, sqlite, etc.)
3. pip plugins         (cruhon-* packages, sorted alphabetically by name)
4. local mods/         (folders in mods/, sorted alphabetically by folder name)
```

**Why alphabetical for steps 3 and 4?**  
Alphabetical order is deterministic across all machines and OS environments.
Random or discovery order is not.

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
    # do something before
    result = next_fn(transpiler, node)  # call next in chain
    # do something after
    return result
```

If a plugin does NOT call `next_fn`, the chain stops there.
This must be documented in the plugin's mod.json.

---

## 4. Conflict Rules

### 4.1 Namespace conflicts
Two plugins register the same namespace (e.g. both register `@db`):
- First loaded wins
- Second plugin gets a warning at load time:
  ```
  ⚠ [cruhon-db-alt] namespace 'db' already registered by [cruhon-db]. Skipping.
  ```

### 4.2 Alias conflicts
Two plugins register the same alias (e.g. both register `@fetch`):
- Same rule: first loaded wins, second gets warning

### 4.3 Override conflicts
Multiple plugins override the same core command:
- All overrides are chained (not conflicting) — see section 3
- No warning needed, this is expected behavior

---

## 5. Version Compatibility

Every plugin must declare which Cruhon version it supports:

```json
{
  "name": "cruhon-db",
  "cruhon": ">=0.2.0"
}
```

If a plugin requires a version newer than the installed Cruhon:
```
✗ [cruhon-db] requires cruhon >= 0.3.0, current is 0.2.0. Skipping.
```

---

## 6. AST Stability Contract

AST node field names are stable after they are defined.
Adding new fields to a node is allowed (with defaults).
Removing or renaming fields is a breaking change — requires major version bump.

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

---

## 7. Lifecycle Hooks (Guaranteed Order)

```
1. before_parse    (source string)
2. after_parse     (AST)
3. before_transpile (AST)
4. after_transpile  (Python string)
5. before_exec      (Python string)
6. after_run        ()
```

On error:
```
on_error (exception)
```

Hooks at the same event fire in plugin load order (deterministic — see section 2).

---

## 8. What Never Changes (Frozen Forever)

These are frozen at v1.0 and never change:

- `@command[args]` syntax
- `@end` as block terminator  
- `;` as argument separator
- `{var}` as interpolation syntax
- `#` as comment prefix
- `.clpy` as file extension
- Core command names (see grammar.md section 3)
- AST base class interface (`Node.accept`, `Node.line`)
- `ModAPI` public method signatures

---

## 9. Semantic Freeze (from v0.5)

No new syntax may be added until ALL of the following are true:

1. `_eval_value()` passes 100% of regression tests
2. `;` ambiguity is fully resolved and documented
3. `display` vs `expr` context is stable and tested
4. `semantics.md` is complete and reviewed
5. All `tests/` pass with zero warnings

This rule exists to prevent the "add features on broken foundation" failure mode.
Feature additions after v0.5 must be **additive only** — they cannot change how
existing values are evaluated.

Any PR that modifies `_eval_value()`, `parse_args()`, or the context rules
requires a new test in `tests/test_semantics.clpy`.
