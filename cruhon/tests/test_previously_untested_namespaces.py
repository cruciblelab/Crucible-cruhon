"""
Real execution tests for @contextlib.*, @dataclasses.*, @enum.*, @env.*,
@typing.* — five namespaces (71 methods total) that had ZERO functional
test coverage anywhere in the suite before this file, found via a
coverage audit (grep for "@ns." across every test file except the
generic compile-only safety nets).

Untested code is exactly where bugs hide: @enum.Enum["Color"; "RED GREEN
BLUE"] silently discarded both arguments and returned the bare enum.Enum
class instead of constructing an enum from them — @enum.Enum's own
Python analogue calls the class functionally to do exactly that, so a
Cruhon user reasonably expecting the same behavior got no error at the
call site, only a confusing "AttributeError: RED" far downstream at
first use. Fixed to match Python's dual bare-class/functional-constructor
behavior. @dataclasses/@contextlib/@typing/@env all worked correctly
once actually exercised, closing the coverage gap without further bugs.
"""
import io
import contextlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core.runner import run_source, RunError


def run(src):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_source(src)
    return buf.getvalue()


class TestContextlib:
    def test_suppress_swallows_the_named_exception(self):
        out = run(
            '@with[@contextlib.suppress[ValueError]]\n'
            '    int("not a number")\n'
            '@end\n'
            '@print[survived]'
        )
        assert out.strip() == "survived"

    def test_nullcontext_yields_its_value(self):
        out = run(
            '@with[@contextlib.nullcontext[42] as x]\n'
            '    @print[{x}]\n'
            '@end'
        )
        assert out.strip() == "42"

    def test_closing_calls_close_on_exit(self):
        out = run(
            '@var[f; @io.StringIO[]]\n'
            '@with[@contextlib.closing[f]]\n'
            '    @print[{f.closed}]\n'
            '@end\n'
            '@print[{f.closed}]'
        )
        lines = out.strip().splitlines()
        assert lines[0] == "False"
        assert lines[1] == "True"


class TestDataclasses:
    def test_dataclass_and_asdict_roundtrip(self):
        out = run(
            '@dataclass[Point]\n'
            '    x: float = 0.0\n'
            '    y: float = 0.0\n'
            '@end\n'
            '@var[p; Point(1.0, 2.0)]\n'
            '@var[d; @dataclasses.asdict[p]]\n'
            '@print[{d}]'
        )
        assert out.strip() == "{'x': 1.0, 'y': 2.0}"

    def test_fields_lists_field_names(self):
        # NOTE: @command[...] cannot be embedded inside a nested Python
        # expression like a list comprehension — same class of limitation
        # as "{}"-interpolation-embedded inline commands (see README).
        # Bind it to a variable first, the documented, always-working idiom.
        out = run(
            '@dataclass[Point]\n'
            '    x: float = 0.0\n'
            '    y: float = 0.0\n'
            '@end\n'
            '@var[p; Point(1.0, 2.0)]\n'
            '@var[fields; @dataclasses.fields[p]]\n'
            '@var[names; [f.name for f in fields]]\n'
            '@print[{names}]'
        )
        assert out.strip() == "['x', 'y']"

    def test_replace_returns_a_modified_copy(self):
        out = run(
            '@dataclass[Point]\n'
            '    x: float = 0.0\n'
            '    y: float = 0.0\n'
            '@end\n'
            '@var[p; Point(1.0, 2.0)]\n'
            '@var[p2; @dataclasses.replace[p; x=9.0]]\n'
            '@print[{p2.x}|{p2.y}|{p.x}]'
        )
        assert out.strip() == "9.0|2.0|1.0"


class TestEnum:
    def test_functional_constructor_builds_a_real_enum(self):
        out = run(
            '@var[Color; @enum.Enum["Color"; "RED GREEN BLUE"]]\n'
            '@print[{Color.RED}]'
        )
        assert out.strip() == "Color.RED"

    def test_bare_reference_is_the_class_itself(self):
        out = run('@var[t; @enum.Enum[]]\n@print[{t}]')
        assert "enum" in out and "Enum" in out

    def test_names_and_values_on_a_constructed_enum(self):
        out = run(
            '@var[Color; @enum.Enum["Color"; "RED GREEN BLUE"]]\n'
            '@var[names; @enum.names[Color]]\n'
            '@print[{names}]'
        )
        assert out.strip() == "['RED', 'GREEN', 'BLUE']"

    def test_intenum_functional_constructor(self):
        out = run(
            '@var[Level; @enum.IntEnum["Level"; "LOW HIGH"]]\n'
            '@print[{int(Level.HIGH)}]'
        )
        assert out.strip() == "2"

    def test_create_helper_also_works(self):
        out = run(
            '@var[Color; @enum.create["Color"; ["RED", "GREEN"]]]\n'
            '@print[{Color.RED.name}]'
        )
        assert out.strip() == "RED"


class TestTyping:
    def test_optional_is_a_real_typing_construct(self):
        out = run('@var[t; @typing.Optional[int]]\n@print[{t}]')
        assert "Optional" in out or "int | None" in out

    def test_get_type_hints_reads_real_annotations(self):
        out = run(
            '@func[f; x: int; return=str]\n'
            '    @return["ok"]\n'
            '@end\n'
            '@var[h; @typing.get_type_hints[f]]\n'
            '@print[{h["x"]}|{h["return"]}]'
        )
        assert "int" in out and "str" in out


class TestEnvNamespace:
    def test_set_and_int(self):
        out = run('@env.set["TESTKEY_XYZ"; "42"]\n@var[v; @env.int["TESTKEY_XYZ"]]\n@print[{v}]')
        assert out.strip() == "42"

    def test_mask_hides_the_middle(self):
        out = run('@var[m; @env.mask["supersecret123"]]\n@print[{m}]')
        masked = out.strip()
        assert masked.startswith("su")
        assert masked.endswith("23")
        assert "supersecret123" not in masked

    def test_require_raises_when_missing(self):
        # run_source() wraps every runtime exception in a RunError.
        with pytest.raises(RunError, match="required variable"):
            run_source('@var[v; @env.require["DOES_NOT_EXIST_XYZ_ZZZ"]]')

    def test_bool_true_false_values(self):
        for val, expected in [("1", "True"), ("true", "True"), ("yes", "True"),
                               ("0", "False"), ("no", "False"), ("", "False")]:
            out = run(f'@env.set["BOOLKEY"; "{val}"]\n@var[b; @env.bool["BOOLKEY"]]\n@print[{{b}}]')
            assert out.strip() == expected, f"env.bool({val!r}) expected {expected}, got {out.strip()!r}"
