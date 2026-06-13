"""
Tests for v2.7.0 language features:
  - Type annotations on @var and @const
  - Typed @func parameters and return type
  - @type alias command
  - @dataclass block
"""
import pytest
from cruhon.core import parse, transpile


def _src(code: str) -> str:
    return transpile(parse(code)).strip()


# ── @var type annotations ────────────────────────────────────────────────────

class TestVarTypeAnnotations:
    def test_plain_var_unchanged(self):
        assert _src("@var[x; 42]") == "x = 42"

    def test_var_with_type_and_value(self):
        assert _src("@var[x: int; 42]") == "x: int = 42"

    def test_var_with_type_only(self):
        assert _src("@var[x: int]") == "x: int"

    def test_var_string_type(self):
        assert _src('@var[name: str; "alice"]') == 'name: str = "alice"'

    def test_var_complex_type(self):
        result = _src("@var[items: list[int]; []]")
        assert "items: list[int] =" in result

    def test_var_optional_type(self):
        assert _src("@var[val: int | None; None]") == "val: int | None = None"

    def test_var_tuple_unpack_unchanged(self):
        # Tuple unpack path must not break
        assert _src("@var[a, b; some_tuple]") == "a, b = some_tuple"


# ── @const type annotations ──────────────────────────────────────────────────

class TestConstTypeAnnotations:
    def test_plain_const_unchanged(self):
        result = _src("@const[MAX; 100]")
        assert result == "MAX = 100  # const"

    def test_const_with_type_and_value(self):
        result = _src("@const[MAX: int; 100]")
        assert result == "MAX: int = 100  # const"

    def test_const_string_type(self):
        result = _src('@const[NAME: str; "app"]')
        assert result == 'NAME: str = "app"  # const'

    def test_const_complex_type(self):
        result = _src("@const[PRIMES: list[int]; @list[2; 3; 5; 7]]")
        assert "PRIMES: list[int] = [2, 3, 5, 7]  # const" in result


# ── @func type annotations ───────────────────────────────────────────────────

class TestFuncTypeAnnotations:
    def test_plain_func_unchanged(self):
        result = _src("@func[greet; name]\n    @return[name]\n@end")
        assert "def greet(name):" in result

    def test_typed_params(self):
        result = _src("@func[add; a: int; b: int]\n    @return[a + b]\n@end")
        assert "def add(a: int, b: int):" in result

    def test_return_type_named_arg(self):
        result = _src("@func[add; a: int; b: int; return=int]\n    @return[a + b]\n@end")
        assert "def add(a: int, b: int) -> int:" in result

    def test_return_type_complex(self):
        result = _src("@func[items; return=list[str]]\n    @return[[]]\n@end")
        assert "def items() -> list[str]:" in result

    def test_return_type_optional(self):
        result = _src("@func[find; x: int; return=int | None]\n    @return[None]\n@end")
        assert "def find(x: int) -> int | None:" in result

    def test_legacy_arrow_syntax_still_works(self):
        result = _src("@func[add; a; b; -> int]\n    @return[a + b]\n@end")
        assert "def add(a, b) -> int:" in result

    def test_typed_async_func(self):
        result = _src("@async[fetch; url: str; return=str]\n    @return[url]\n@end")
        assert "async def fetch(url: str) -> str:" in result


# ── @type alias ───────────────────────────────────────────────────────────────

class TestTypeAlias:
    def test_simple_alias(self):
        result = _src("@type[Vector; list[float]]")
        assert "Vector = list[float]" in result
        assert "# type alias" in result

    def test_alias_with_union(self):
        result = _src("@type[MaybeStr; str | None]")
        assert "MaybeStr = str | None" in result

    def test_alias_complex(self):
        result = _src("@type[Callback; Callable[...; str]]")
        assert "Callback = Callable[...; str]" in result
        assert "# type alias" in result

    def test_parse_error_missing_alias(self):
        with pytest.raises(Exception):
            _src("@type[Vector]")


# ── @dataclass block ──────────────────────────────────────────────────────────

class TestDataclass:
    def test_basic_dataclass(self):
        src = "@dataclass[Point]\n    @var[x: float]\n    @var[y: float]\n@end"
        result = _src(src)
        assert "from dataclasses import dataclass" in result
        assert "@dataclass" in result
        assert "class Point:" in result
        assert "x: float" in result
        assert "y: float" in result

    def test_dataclass_with_defaults(self):
        src = "@dataclass[Config]\n    @var[debug: bool; False]\n    @var[port: int; 8080]\n@end"
        result = _src(src)
        assert "class Config:" in result
        assert "debug: bool = False" in result
        assert "port: int = 8080" in result

    def test_dataclass_with_parent(self):
        src = "@dataclass[Child; Parent]\n    @var[extra: str]\n@end"
        result = _src(src)
        assert "class Child(Parent):" in result

    def test_dataclass_parse_error_no_name(self):
        with pytest.raises(Exception):
            _src("@dataclass[]\n    @var[x: int]\n@end")

    def test_dataclass_imports_deduplicated(self):
        src = "@dataclass[A]\n    @var[x: int]\n@end\n@dataclass[B]\n    @var[y: int]\n@end"
        result = _src(src)
        # Both classes should appear
        assert "class A:" in result
        assert "class B:" in result


# ── Backwards compatibility ────────────────────────────────────────────────────

class TestBackwardsCompat:
    def test_var_no_regression(self):
        assert _src("@var[x; 1 + 2]") == "x = 1 + 2"

    def test_const_no_regression(self):
        assert _src("@const[PI; 3.14]") == "PI = 3.14  # const"

    def test_func_no_regression(self):
        result = _src("@func[hello]\n    @print[\"hi\"]\n@end")
        assert "def hello():" in result
        assert 'print("hi")' in result

    def test_class_no_regression(self):
        result = _src("@class[Dog; Animal]\n    @pass\n@end")
        assert "class Dog(Animal):" in result
