"""
cruhon/core/libs/mimetypes_.py
==============================
Guess MIME types from file names for Cruhon — @mimetypes.*

Map between file extensions and MIME types.

━━━ GUESS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @mimetypes.guess[path]          → MIME type ("text/html") or None
  @mimetypes.full[path]           → (type, encoding) tuple
  @mimetypes.is_text[path]        → bool: does it look like text
  @mimetypes.is_image[path]       → bool: does it look like an image

━━━ EXTENSIONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @mimetypes.extension[mime]      → a preferred extension (".html")
  @mimetypes.extensions[mime]     → all known extensions for a MIME type

━━━ REGISTRY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @mimetypes.add[mime; ext]       → register a custom type → extension map
  @mimetypes.types[]              → the full extension → type mapping
"""
from ..registry import register_lib, register_lib_call

_MT = "__import__('mimetypes')"


def register():
    register_lib("mimetypes", None)

    # ── Guess ─────────────────────────────────────────────────
    register_lib_call("mimetypes", "guess",
        lambda a: f"{_MT}.guess_type({a[0]})[0]")
    register_lib_call("mimetypes", "full",
        lambda a: f"{_MT}.guess_type({a[0]})")
    register_lib_call("mimetypes", "is_text",
        lambda a: f"(lambda _t: bool(_t) and _t.startswith('text/'))({_MT}.guess_type({a[0]})[0])")
    register_lib_call("mimetypes", "is_image",
        lambda a: f"(lambda _t: bool(_t) and _t.startswith('image/'))({_MT}.guess_type({a[0]})[0])")

    # ── Extensions ────────────────────────────────────────────
    register_lib_call("mimetypes", "extension",
        lambda a: f"{_MT}.guess_extension({a[0]})")
    register_lib_call("mimetypes", "extensions",
        lambda a: f"{_MT}.guess_all_extensions({a[0]})")

    # ── Registry ──────────────────────────────────────────────
    register_lib_call("mimetypes", "add",
        lambda a: f"{_MT}.add_type({a[0]}, {a[1]})")
    register_lib_call("mimetypes", "types",
        lambda a: f"(lambda: ({_MT}.init(), {_MT}.types_map)[1])()")
