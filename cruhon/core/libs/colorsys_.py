"""
cruhon/core/libs/colorsys_.py
=============================
Color system conversions for Cruhon — @colorsys.*

Convert colors between RGB, HLS, HSV, and YIQ representations. All
RGB/HLS/HSV values are floats in [0.0, 1.0].

━━━ RGB ↔ HSV ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @colorsys.to_hsv[r; g; b]       → (h, s, v) tuple
  @colorsys.from_hsv[h; s; v]     → (r, g, b) tuple

━━━ RGB ↔ HLS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @colorsys.to_hls[r; g; b]       → (h, l, s) tuple
  @colorsys.from_hls[h; l; s]     → (r, g, b) tuple

━━━ RGB ↔ YIQ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @colorsys.to_yiq[r; g; b]       → (y, i, q) tuple
  @colorsys.from_yiq[y; i; q]     → (r, g, b) tuple

━━━ HEX HELPERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @colorsys.hex_to_rgb[hex]       → (r, g, b) as floats in [0, 1]
  @colorsys.rgb_to_hex[r; g; b]   → "#rrggbb" hex string
  @colorsys.hex_to_hsv[hex]       → (h, s, v) from hex color
  @colorsys.hex_to_hls[hex]       → (h, l, s) from hex color
  @colorsys.luminance[r; g; b]    → perceptual luminance (0.0–1.0)
  @colorsys.blend[c1; c2; t]      → linear interpolation between two RGB tuples
"""
from ..registry import register_lib, register_lib_call

_CS = "__import__('colorsys')"


def register():
    register_lib("colorsys", None)

    # ── RGB ↔ HSV ─────────────────────────────────────────────
    register_lib_call("colorsys", "to_hsv",
        lambda a: f"{_CS}.rgb_to_hsv({a[0]}, {a[1]}, {a[2]})")
    register_lib_call("colorsys", "from_hsv",
        lambda a: f"{_CS}.hsv_to_rgb({a[0]}, {a[1]}, {a[2]})")

    # ── RGB ↔ HLS ─────────────────────────────────────────────
    register_lib_call("colorsys", "to_hls",
        lambda a: f"{_CS}.rgb_to_hls({a[0]}, {a[1]}, {a[2]})")
    register_lib_call("colorsys", "from_hls",
        lambda a: f"{_CS}.hls_to_rgb({a[0]}, {a[1]}, {a[2]})")

    # ── RGB ↔ YIQ ─────────────────────────────────────────────
    register_lib_call("colorsys", "to_yiq",
        lambda a: f"{_CS}.rgb_to_yiq({a[0]}, {a[1]}, {a[2]})")
    register_lib_call("colorsys", "from_yiq",
        lambda a: f"{_CS}.yiq_to_rgb({a[0]}, {a[1]}, {a[2]})")

    # ── Hex helpers ───────────────────────────────────────────
    register_lib_call("colorsys", "hex_to_rgb",
        lambda a: (
            f"(lambda _h: (int(_h[1:3],16)/255, int(_h[3:5],16)/255, int(_h[5:7],16)/255))({a[0]})"
        ))
    register_lib_call("colorsys", "rgb_to_hex",
        lambda a: (
            f"'#%02x%02x%02x' % (int({a[0]}*255), int({a[1]}*255), int({a[2]}*255))"
        ))
    register_lib_call("colorsys", "hex_to_hsv",
        lambda a: (
            f"(lambda _h: {_CS}.rgb_to_hsv(int(_h[1:3],16)/255, int(_h[3:5],16)/255, int(_h[5:7],16)/255))({a[0]})"
        ))
    register_lib_call("colorsys", "hex_to_hls",
        lambda a: (
            f"(lambda _h: {_CS}.rgb_to_hls(int(_h[1:3],16)/255, int(_h[3:5],16)/255, int(_h[5:7],16)/255))({a[0]})"
        ))
    register_lib_call("colorsys", "luminance",
        lambda a: f"0.2126*{a[0]} + 0.7152*{a[1]} + 0.0722*{a[2]}")
    register_lib_call("colorsys", "blend",
        lambda a: (
            f"(lambda _c1, _c2, _t: tuple(_c1[_i]*(1-_t)+_c2[_i]*_t for _i in range(3)))"
            f"({a[0]}, {a[1]}, {a[2]})"
        ))
