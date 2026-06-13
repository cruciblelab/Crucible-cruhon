"""
cruhon/core/libs/gettext_.py
============================
Message translation for Cruhon — @gettext.*

Internationalize text via the gettext catalog system. With no catalog
installed, messages pass through unchanged.

━━━ TRANSLATE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @gettext.t[msg]                 → translated message (or msg itself)
  @gettext.plural[single; plural; n] → singular/plural-aware translation

━━━ CATALOGS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @gettext.translation[domain; localedir]      → a translations object
  @gettext.install[domain; localedir]          → install _() globally
  @gettext.find[domain; localedir]             → path to a .mo file, or None
"""
from ..registry import register_lib, register_lib_call

_GT = "__import__('gettext')"


def register():
    register_lib("gettext", None)

    # ── Translate ─────────────────────────────────────────────
    register_lib_call("gettext", "t",
        lambda a: f"{_GT}.gettext({a[0]})")
    register_lib_call("gettext", "plural",
        lambda a: f"{_GT}.ngettext({a[0]}, {a[1]}, {a[2]})")

    # ── Catalogs ──────────────────────────────────────────────
    register_lib_call("gettext", "translation",
        lambda a: f"{_GT}.translation({a[0]}, {a[1]})")
    register_lib_call("gettext", "install",
        lambda a: f"{_GT}.install({a[0]}, {a[1]})")
    register_lib_call("gettext", "find",
        lambda a: f"{_GT}.find({a[0]}, {a[1]})")
