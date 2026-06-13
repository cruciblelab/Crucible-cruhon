"""
cruhon/core/libs/pickle_.py
===========================
Pickle wrappers for Cruhon — @pickle.*

  @pickle.dumps[obj]          → bytes  (serialize to bytes)
  @pickle.loads[data]         → object (deserialize from bytes)
  @pickle.save[path; obj]     — write serialized object to file
  @pickle.load[path]          → object (read from file)
  @pickle.copy[obj]           → deep copy via pickle round-trip
  @pickle.dumps_proto[obj; n] → bytes  (with explicit protocol n)
"""
from ..registry import register_lib, register_lib_call


def register():
    register_lib("pickle", None)

    register_lib_call("pickle", "dumps",
        lambda a: f"__import__('pickle').dumps({a[0]})")

    register_lib_call("pickle", "loads",
        lambda a: f"__import__('pickle').loads({a[0]})")

    register_lib_call("pickle", "save",
        lambda a: (
            f"(lambda _p, _o: open(_p, 'wb').write(__import__('pickle').dumps(_o)))({a[0]}, {a[1]})"
        ))

    register_lib_call("pickle", "load",
        lambda a: f"__import__('pickle').loads(open({a[0]}, 'rb').read())")

    register_lib_call("pickle", "copy",
        lambda a: f"__import__('pickle').loads(__import__('pickle').dumps({a[0]}))")

    register_lib_call("pickle", "dumps_proto",
        lambda a: f"__import__('pickle').dumps({a[0]}, protocol=int({a[1]}))")
