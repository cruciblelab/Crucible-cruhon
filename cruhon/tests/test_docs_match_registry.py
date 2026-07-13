"""
Guards against documentation drift: every method name listed in
library.md's `| @ns.* | wraps | method, method, ... |` tables must be a
REAL, registered handler.

This class of bug was found live on a real device: library.md/README
documented dozens of namespaces (@math.*, @os.*, @sys.*, @signal.*,
@resource.*, @store.*, @color.*, and 60+ others) with method lists that
were partly or entirely aspirational — up to 456 individual method names
across 75+ namespaces did not exist in the registry at all. Calling any
of them raised NameError (silent fallback to a generic, unimported
"namespace.method(args)" code string) or, for @httpx.*/@pathlib.*, were
100% fabricated (zero real handlers under either namespace).

Fixed by regenerating every method-list cell in library.md directly from
the registry, implementing the highest-value real gaps (34 @math.*
methods, @store.clear, @color.dim), and removing the two fully-fake
namespaces from the docs (with a pointer to the real equivalents:
@file.* for path ops, @http.async_* for httpx-backed async calls).

This test parses library.md's tables the same way and fails loudly the
moment a future doc edit reintroduces a method name that isn't real —
so this class of bug can never silently regress again.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core import registry as _registry  # noqa: F401  (populates _LIB_CALLS)
from cruhon.core.registry import _LIB_CALLS

_LIBRARY_MD = Path(__file__).parent.parent.parent / "library.md"

# Namespaces documented in library.md that are PLUGIN-provided (cruhon-db,
# cruhon-panel, cruhon-discord, cruhon-data, cruhon-schedule) — not part of
# the core registry unless that plugin is explicitly loaded, so they're
# out of scope for this core-registry consistency check.
_PLUGIN_NAMESPACES = {"db", "panel", "discord", "data", "schedule"}

_ROW_RE = re.compile(
    r'^\|\s*`@([a-zA-Z_][a-zA-Z0-9_]*)\.\*`\s*\|[^|]*\|\s*([^|]+)\|\s*$',
    re.MULTILINE,
)


def _actual_methods_by_namespace() -> dict[str, set[str]]:
    actual: dict[str, set[str]] = {}
    for (ns, method) in _LIB_CALLS:
        actual.setdefault(ns, set()).add(method)
    return actual


def _documented_rows():
    """Yield (namespace, [method_names]) for every `@ns.*` row in library.md."""
    content = _LIBRARY_MD.read_text(encoding="utf-8")
    for m in _ROW_RE.finditer(content):
        ns = m.group(1)
        methods_raw = m.group(2)
        methods = [x.strip() for x in methods_raw.split(",") if x.strip()]
        # Only keep tokens that look like real identifiers — filters out
        # any stray ellipsis/prose fragments in the wraps/highlights cells.
        methods = [m2 for m2 in methods if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', m2)]
        yield ns, methods


def _cases():
    actual = _actual_methods_by_namespace()
    for ns, methods in _documented_rows():
        if ns in _PLUGIN_NAMESPACES:
            continue
        for method in methods:
            yield ns, method, actual


@pytest.mark.parametrize(
    "ns,method,actual", list(_cases()),
    ids=lambda v: v if isinstance(v, str) else "",
)
def test_documented_method_is_registered(ns, method, actual):
    assert ns in actual, (
        f"library.md documents @{ns}.* but no handler for that namespace "
        f"is registered in the core registry at all."
    )
    assert method in actual[ns], (
        f"library.md documents @{ns}.{method}[...] but '{method}' is not "
        f"a registered handler for @{ns}.* — either implement it for real "
        f"or remove it from library.md. Real methods: {sorted(actual[ns])}"
    )


def test_documented_namespace_count_is_substantial():
    """Sanity check the parser itself is finding rows, not silently no-op'ing."""
    rows = list(_documented_rows())
    assert len(rows) > 100, f"Only parsed {len(rows)} rows from library.md — parser regression?"
