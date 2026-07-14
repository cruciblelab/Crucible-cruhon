"""
cruhon/core/libs/store_.py
==========================
Simple key/value file storage wrapper for Cruhon.

Uses stdlib json only — no external dependencies.
Storage file: .cruhon_store.json in current working directory.

Supported:
  @store.set[key; value]
  @store.get[key]
  @store.get[key; default]
  @store.delete[key]
  @store.all
  @store.clear[]
"""


def _handler_set(args):
    key = args[0] if args else '""'
    value = args[1] if len(args) > 1 else "None"
    return f"__cruhon_store_set({key}, {value})"


def _handler_get(args):
    key = args[0] if args else '""'
    if len(args) > 1:
        return f"__cruhon_store_get({key}, {args[1]})"
    return f"__cruhon_store_get({key})"


def _handler_delete(args):
    key = args[0] if args else '""'
    return f"__cruhon_store_delete({key})"


def _handler_all(_args):
    return "__cruhon_store_load()"


def _handler_clear(_args):
    return "__cruhon_store_clear()"


STORE_HANDLERS = {
    "set":    _handler_set,
    "get":    _handler_get,
    "delete": _handler_delete,
    "all":    _handler_all,
    "clear":  _handler_clear,
}
