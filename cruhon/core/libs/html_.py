"""
cruhon/core/libs/html_.py
=========================
HTML escaping & light scraping for Cruhon — @html.*

Escape/unescape entities and pull text, links and tags out of HTML
without a heavy parser.

━━━ ESCAPE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @html.escape[s]                 → escape &, <, >, " and '
  @html.escape[s; quote]          → escape, with quote handling on/off
  @html.unescape[s]               → turn entities back into characters

━━━ SCRAPE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @html.strip_tags[s]             → remove all <...> tags
  @html.text[s]                   → visible text (tags stripped + unescaped)
  @html.links[s]                  → list of href="..." URLs
  @html.images[s]                 → list of src="..." URLs
  @html.tags[s]                   → list of tag names that appear
"""
from ..registry import register_lib, register_lib_call

_HT = "__import__('html')"
_RE = "__import__('re')"


def register():
    register_lib("html", None)

    # ── Escape ────────────────────────────────────────────────
    register_lib_call("html", "escape",
        lambda a: (
            f"{_HT}.escape({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_HT}.escape({a[0]})"
        ))
    register_lib_call("html", "unescape",
        lambda a: f"{_HT}.unescape({a[0]})")

    # ── Scrape ────────────────────────────────────────────────
    register_lib_call("html", "strip_tags",
        lambda a: f"{_RE}.sub(r'<[^>]+>', '', {a[0]})")
    register_lib_call("html", "text",
        lambda a: (
            f"{_HT}.unescape({_RE}.sub(r'\\s+', ' ', {_RE}.sub(r'<[^>]+>', ' ', {a[0]}))).strip()"
        ))
    # The quote class is built with chr(34)/chr(39) so the generated code
    # contains no backslash-escaped quotes (which the arg validator mishandles).
    register_lib_call("html", "links",
        lambda a: f"{_RE}.findall('href=[' + chr(34) + chr(39) + ']([^' + chr(34) + chr(39) + ']+)', {a[0]})")
    register_lib_call("html", "images",
        lambda a: f"{_RE}.findall('src=[' + chr(34) + chr(39) + ']([^' + chr(34) + chr(39) + ']+)', {a[0]})")
    register_lib_call("html", "tags",
        lambda a: f"{_RE}.findall(r'<\\s*([a-zA-Z][a-zA-Z0-9]*)', {a[0]})")
