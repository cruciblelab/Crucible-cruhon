"""
cruhon-shortcuts — types group
================================
Shortcuts for @typing.*, @dataclasses.*, and @enum.*.

Global aliases (source rewrites)
─────────────────────────────────
@dc[cls]                → @dataclasses.dataclass[cls]
@asdict[obj]            → @dataclasses.asdict[obj]
@astuple[obj]           → @dataclasses.astuple[obj]
@dc_fields[obj]         → @dataclasses.fields[obj]
@dc_replace[obj; ...]   → @dataclasses.replace[obj; ...]
@is_dc[obj]             → @dataclasses.is_dataclass[obj]
@make_dc[name; fields]  → @dataclasses.make_dataclass[name; fields]
@dc_field[...]          → @dataclasses.field[...]
@make_enum[name; vals]  → @enum.create[name; vals]
@list_enum[cls]         → @enum.list[cls]
@enum_names[cls]        → @enum.names[cls]
@enum_values[cls]       → @enum.values[cls]
@enum_members[cls]      → @enum.members[cls]
@ty_cast[typ; val]      → @typing.cast[typ; val]
@ty_hints[obj]          → @typing.get_type_hints[obj]
@named_tuple[name; flds]→ @typing.NamedTuple[name; flds]
@ty_overload[fn]        → @typing.overload[fn]
@ty_protocol[cls]       → @typing.runtime_checkable[cls]

Namespace method aliases
─────────────────────────
@dataclasses.dict[obj]  → @dataclasses.asdict[obj]
@dataclasses.tup[obj]   → @dataclasses.astuple[obj]
@dataclasses.is_dc[obj] → @dataclasses.is_dataclass[obj]
@dataclasses.flds[obj]  → @dataclasses.fields[obj]
@dataclasses.mk[n; f]   → @dataclasses.make_dataclass[n; f]
@enum.list_names[cls]   → @enum.names[cls]
@enum.list_values[cls]  → @enum.values[cls]
@typing.opt[T]          → @typing.Optional[T]
@typing.union2[A; B]    → @typing.Union[A; B]
@typing.lit[*vals]      → @typing.Literal[*vals]
@typing.lst[T]          → @typing.List[T]
@typing.dct[K; V]       → @typing.Dict[K; V]
@typing.tup2[*Ts]       → @typing.Tuple[*Ts]

New methods (via api.lib_call)
───────────────────────────────
@dataclasses.to_json[obj]       → JSON string of dataclass
@dataclasses.from_dict[cls; d]  → populate dataclass from dict
@dataclasses.clone[obj]         → shallow copy of dataclass
@dataclasses.evolve[obj; ...]   → alias for replace (dataclasses.replace)
@dataclasses.field_names[obj]   → list of field names
@dataclasses.field_types[obj]   → dict of field name → type annotation
@dataclasses.field_defaults[obj]→ dict of field name → default value
@enum.from_value[cls; v]        → enum member from value
@enum.from_name[cls; n]         → enum member from name
@enum.has_value[cls; v]         → True if value exists in enum
@enum.has_name[cls; n]          → True if name exists in enum
@enum.to_dict[cls]              → {name: value} dict for all members
@typing.is_optional[t]          → True if type is Optional[X]
@typing.get_args[t]             → typing.get_args(t)
@typing.get_origin[t]           → typing.get_origin(t)
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@dc[":             "@dataclasses.dataclass[",
    "@asdict[":         "@dataclasses.asdict[",
    "@astuple[":        "@dataclasses.astuple[",
    "@dc_fields[":      "@dataclasses.fields[",
    "@dc_replace[":     "@dataclasses.replace[",
    "@is_dc[":          "@dataclasses.is_dataclass[",
    "@make_dc[":        "@dataclasses.make_dataclass[",
    "@dc_field[":       "@dataclasses.field[",
    "@make_enum[":      "@enum.create[",
    "@list_enum[":      "@enum.list[",
    "@enum_names[":     "@enum.names[",
    "@enum_values[":    "@enum.values[",
    "@enum_members[":   "@enum.members[",
    "@ty_cast[":        "@typing.cast[",
    "@ty_hints[":       "@typing.get_type_hints[",
    "@named_tuple[":    "@typing.NamedTuple[",
    "@ty_overload[":    "@typing.overload[",
    "@ty_protocol[":    "@typing.runtime_checkable[",
}

METHOD_ALIASES: dict[str, str] = {
    "@dataclasses.dict[":    "@dataclasses.asdict[",
    "@dataclasses.tup[":     "@dataclasses.astuple[",
    "@dataclasses.is_dc[":   "@dataclasses.is_dataclass[",
    "@dataclasses.flds[":    "@dataclasses.fields[",
    "@dataclasses.mk[":      "@dataclasses.make_dataclass[",
    "@enum.list_names[":     "@enum.names[",
    "@enum.list_values[":    "@enum.values[",
    "@typing.opt[":          "@typing.Optional[",
    "@typing.union2[":       "@typing.Union[",
    "@typing.lit[":          "@typing.Literal[",
    "@typing.lst[":          "@typing.List[",
    "@typing.dct[":          "@typing.Dict[",
    "@typing.tup2[":         "@typing.Tuple[",
}

_DC  = "__import__('dataclasses')"
_EN  = "__import__('enum')"
_TY  = "__import__('typing')"
_JSON = "__import__('json')"


def _new_lib_calls(api) -> None:

    api.lib_call("dataclasses", "to_json", lambda a: (
        f"{_JSON}.dumps({_DC}.asdict({a[0]}))"
        if a else
        f"'null'"
    ))

    api.lib_call("dataclasses", "from_dict", lambda a: (
        f"{a[0]}(**{a[1]})"
        if len(a) > 1 else
        f"None"
    ))

    api.lib_call("dataclasses", "clone", lambda a: (
        f"{_DC}.replace({a[0]})"
        if a else
        f"None"
    ))

    api.lib_call("dataclasses", "evolve", lambda a: (
        f"{_DC}.replace({', '.join(a)})"
        if a else
        f"None"
    ))

    api.lib_call("dataclasses", "field_names", lambda a: (
        f"[_f.name for _f in {_DC}.fields({a[0]})]"
        if a else
        f"[]"
    ))

    api.lib_call("dataclasses", "field_types", lambda a: (
        f"{{_f.name: _f.type for _f in {_DC}.fields({a[0]})}}"
        if a else
        f"{{}}"
    ))

    api.lib_call("dataclasses", "field_defaults", lambda a: (
        f"{{_f.name: _f.default "
        f"for _f in {_DC}.fields({a[0]}) "
        f"if _f.default is not {_DC}.MISSING}}"
        if a else
        f"{{}}"
    ))

    api.lib_call("enum", "from_value", lambda a: (
        f"{a[0]}({a[1]})"
        if len(a) > 1 else
        f"None"
    ))

    api.lib_call("enum", "from_name", lambda a: (
        f"{a[0]}[str({a[1]})]"
        if len(a) > 1 else
        f"None"
    ))

    api.lib_call("enum", "has_value", lambda a: (
        f"({a[1]} in [_m.value for _m in {a[0]}])"
        if len(a) > 1 else
        f"False"
    ))

    api.lib_call("enum", "has_name", lambda a: (
        f"(str({a[1]}) in {a[0]}.__members__)"
        if len(a) > 1 else
        f"False"
    ))

    api.lib_call("enum", "to_dict", lambda a: (
        f"{{_m.name: _m.value for _m in {a[0]}}}"
        if a else
        f"{{}}"
    ))

    api.lib_call("typing", "is_optional", lambda a: (
        f"(getattr({a[0]}, '__origin__', None) is {_TY}.Union "
        f"and type(None) in {a[0]}.__args__)"
        if a else
        f"False"
    ))

    api.lib_call("typing", "get_args", lambda a: (
        f"{_TY}.get_args({a[0]})"
        if a else
        f"()"
    ))

    api.lib_call("typing", "get_origin", lambda a: (
        f"{_TY}.get_origin({a[0]})"
        if a else
        f"None"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
