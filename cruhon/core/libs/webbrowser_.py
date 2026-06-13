"""
cruhon/core/libs/webbrowser_.py
===============================
Open URLs in the user's browser for Cruhon — @webbrowser.*

━━━ OPEN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @webbrowser.open[url]           → open url in the default browser
  @webbrowser.open_new[url]       → open in a new window if possible
  @webbrowser.open_tab[url]       → open in a new tab if possible

━━━ BROWSERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @webbrowser.get[]               → the default browser controller
  @webbrowser.get[name]           → a named browser controller ("firefox" …)
"""
from ..registry import register_lib, register_lib_call

_WB = "__import__('webbrowser')"


def register():
    register_lib("webbrowser", None)

    register_lib_call("webbrowser", "open",
        lambda a: f"{_WB}.open({a[0]})")
    register_lib_call("webbrowser", "open_new",
        lambda a: f"{_WB}.open_new({a[0]})")
    register_lib_call("webbrowser", "open_tab",
        lambda a: f"{_WB}.open_new_tab({a[0]})")
    register_lib_call("webbrowser", "get",
        lambda a: f"{_WB}.get({a[0]})" if a else f"{_WB}.get()")
