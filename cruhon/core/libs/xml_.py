"""
XML parsing & inspection for Cruhon — @xml.*

Wraps Python's `xml.etree.ElementTree`: parse XML from a string or file,
navigate the element tree, read tags/attributes/text, and convert to a
plain dict. No `@import` needed.

━━━ PARSE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @xml.parse[path]           → root Element parsed from a file
  @xml.from_string[text]     → root Element parsed from a string
  @xml.to_string[element]    → serialize an Element back to an XML string

━━━ NAVIGATE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @xml.find[element; path]   → first matching child (ElementPath syntax)
  @xml.find_all[element; pth]→ list of matching children
  @xml.children[element]     → direct child elements as a list
  @xml.iter[element; tag]    → all descendants with the given tag
  @xml.count[element; path]  → number of elements matching a path

━━━ READ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @xml.tag[element]          → element tag name
  @xml.text[element]         → element text content (stripped)
  @xml.attrib[element]       → dict of all attributes
  @xml.get[element; name]    → a single attribute value
  @xml.find_text[el; path]   → text of the first match ('' if none)

━━━ CONVERT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @xml.to_dict[element]      → nested {tag, attrib, text, children} dict
"""
from ..registry import register_lib, register_lib_call

_ET = "__import__('xml.etree.ElementTree', fromlist=['ElementTree'])"


def register():
    register_lib("xml", "xml")

    # ── PARSE ─────────────────────────────────────────────────
    register_lib_call("xml", "parse",
        lambda a: f"{_ET}.parse({a[0]}).getroot()" if a else f"{_ET}.Element('root')")

    register_lib_call("xml", "from_string",
        lambda a: f"{_ET}.fromstring({a[0]})" if a else f"{_ET}.Element('root')")

    register_lib_call("xml", "to_string",
        lambda a: f"{_ET}.tostring({a[0]}, encoding='unicode')" if a else "''")

    # ── NAVIGATE ──────────────────────────────────────────────
    register_lib_call("xml", "find",
        lambda a: f"{a[0]}.find({a[1]})" if len(a) > 1 else "None")

    register_lib_call("xml", "find_all",
        lambda a: f"{a[0]}.findall({a[1]})" if len(a) > 1 else f"list({a[0]})" if a else "[]")

    register_lib_call("xml", "children",
        lambda a: f"list({a[0]})" if a else "[]")

    register_lib_call("xml", "iter",
        lambda a: f"list({a[0]}.iter({a[1]}))" if len(a) > 1 else f"list({a[0]}.iter())" if a else "[]")

    register_lib_call("xml", "count",
        lambda a: f"len({a[0]}.findall({a[1]}))" if len(a) > 1 else "0")

    # ── READ ──────────────────────────────────────────────────
    register_lib_call("xml", "tag",
        lambda a: f"{a[0]}.tag" if a else "''")

    register_lib_call("xml", "text",
        lambda a: f"({a[0]}.text or '').strip()" if a else "''")

    register_lib_call("xml", "attrib",
        lambda a: f"dict({a[0]}.attrib)" if a else "{}")

    register_lib_call("xml", "get",
        lambda a: f"{a[0]}.get({a[1]})" if len(a) > 1 else "None")

    register_lib_call("xml", "find_text",
        lambda a: (
            f"(lambda _m: (_m.text or '').strip() if _m is not None else '')({a[0]}.find({a[1]}))"
            if len(a) > 1 else "''"
        ))

    # ── CONVERT ───────────────────────────────────────────────
    register_lib_call("xml", "to_dict",
        lambda a: (
            f"(lambda _f: _f(_f, {a[0]}))("
            f"lambda _f, _e: {{'tag': _e.tag, 'attrib': dict(_e.attrib), "
            f"'text': (_e.text or '').strip(), "
            f"'children': [_f(_f, _c) for _c in _e]}})"
            if a else "{}"
        ))
