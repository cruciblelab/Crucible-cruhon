"""Threading stdlib wrappers for Cruhon — @threading.*"""
from ..registry import register_lib, register_lib_call

_TH = "__import__('threading')"


def register():
    register_lib("threading", "threading")

    register_lib_call("threading", "Thread",
        lambda a: (
            f"{_TH}.Thread(target={a[0]}, args={a[1] if len(a)>1 else '()'}, kwargs={a[2] if len(a)>2 else '{}'})"
        ))

    register_lib_call("threading", "start",
        lambda a: f"{a[0]}.start()")

    register_lib_call("threading", "join",
        lambda a: f"{a[0]}.join({a[1] if len(a)>1 else ''})")

    register_lib_call("threading", "is_alive",
        lambda a: f"{a[0]}.is_alive()")

    register_lib_call("threading", "daemon",
        lambda a: f"{a[0]}.daemon")

    register_lib_call("threading", "Lock",
        lambda a: f"{_TH}.Lock()")

    register_lib_call("threading", "RLock",
        lambda a: f"{_TH}.RLock()")

    register_lib_call("threading", "acquire",
        lambda a: f"{a[0]}.acquire({a[1] if len(a)>1 else ''})")

    register_lib_call("threading", "release",
        lambda a: f"{a[0]}.release()")

    register_lib_call("threading", "Event",
        lambda a: f"{_TH}.Event()")

    register_lib_call("threading", "event_set",
        lambda a: f"{a[0]}.set()")

    register_lib_call("threading", "event_clear",
        lambda a: f"{a[0]}.clear()")

    register_lib_call("threading", "event_wait",
        lambda a: f"{a[0]}.wait({a[1] if len(a)>1 else ''})")

    register_lib_call("threading", "event_is_set",
        lambda a: f"{a[0]}.is_set()")

    register_lib_call("threading", "Semaphore",
        lambda a: f"{_TH}.Semaphore({a[0] if a else 1})")

    register_lib_call("threading", "BoundedSemaphore",
        lambda a: f"{_TH}.BoundedSemaphore({a[0] if a else 1})")

    register_lib_call("threading", "Condition",
        lambda a: f"{_TH}.Condition({a[0] if a else ''})")

    register_lib_call("threading", "Barrier",
        lambda a: f"{_TH}.Barrier({a[0]})")

    register_lib_call("threading", "Timer",
        lambda a: f"{_TH}.Timer({a[0]}, {a[1]}{', args=' + a[2] if len(a)>2 else ''})")

    register_lib_call("threading", "current_thread",
        lambda a: f"{_TH}.current_thread()")

    register_lib_call("threading", "main_thread",
        lambda a: f"{_TH}.main_thread()")

    register_lib_call("threading", "active_count",
        lambda a: f"{_TH}.active_count()")

    register_lib_call("threading", "enumerate",
        lambda a: f"{_TH}.enumerate()")

    register_lib_call("threading", "get_ident",
        lambda a: f"{_TH}.get_ident()")

    register_lib_call("threading", "settrace",
        lambda a: f"{_TH}.settrace({a[0]})")

    register_lib_call("threading", "local",
        lambda a: f"{_TH}.local()")
