"""
Safety net: every registered @namespace.method handler must produce a
syntactically valid Python expression string.

This guards against handler bugs (e.g. a handler that accidentally returns a
lambda instead of a string, or generates unbalanced/!invalid code) for any
call shape from 0 to 4 arguments.
"""
import pytest

# Importing the registry triggers _register_stdlib(), populating _LIB_CALLS.
from cruhon.core import registry
from cruhon.core.registry import _LIB_CALLS

# Dummy arguments are valid Python identifiers so f-string substitution always
# yields a syntactically valid expression. Up to 6 covers every handler's arity.
_DUMMY = [f"_a{i}" for i in range(6)]


def _handler_cases():
    for (namespace, method), handler in sorted(_LIB_CALLS.items()):
        yield namespace, method, handler


@pytest.mark.parametrize("namespace,method,handler", list(_handler_cases()),
                         ids=lambda v: v if isinstance(v, str) else "")
def test_handler_produces_valid_expression(namespace, method, handler):
    # A handler must, for at least one supported arg count, return a code
    # *string* that compiles as a Python expression. Any non-string return is
    # always a bug (e.g. a handler accidentally returning a lambda).
    produced_any = False
    last_error = None
    for n in range(len(_DUMMY) + 1):
        args = _DUMMY[:n]
        try:
            code = handler(args)
        except IndexError:
            # Handler needs more args than n — fine, try a larger n.
            continue
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue
        # A successful call must always hand back a code string.
        assert isinstance(code, str), (
            f"@{namespace}.{method} returned {type(code).__name__}, not a code string"
        )
        try:
            compile(code, f"<{namespace}.{method}>", "eval")
            produced_any = True
        except SyntaxError as exc:
            # Some handlers emit `await ...`, valid only inside an async
            # function — verify those by wrapping in one before giving up.
            try:
                compile(f"async def _f():\n    return {code}",
                        f"<{namespace}.{method}>", "exec")
                produced_any = True
            except SyntaxError:
                last_error = exc
    assert produced_any, (
        f"@{namespace}.{method} produced no valid expression for any arg count "
        f"(last error: {last_error!r})"
    )


def test_handler_count_is_substantial():
    # Sanity check that the registry actually loaded a large surface area.
    assert len(_LIB_CALLS) > 1800
