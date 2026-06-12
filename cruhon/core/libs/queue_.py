"""Queue stdlib wrappers for Cruhon — @queue.*"""
from ..registry import register_lib, register_lib_call

_Q = "__import__('queue')"


def register():
    register_lib("queue", "queue")

    register_lib_call("queue", "Queue",
        lambda a: f"{_Q}.Queue({a[0] if a else 0})")

    register_lib_call("queue", "LifoQueue",
        lambda a: f"{_Q}.LifoQueue({a[0] if a else 0})")

    register_lib_call("queue", "PriorityQueue",
        lambda a: f"{_Q}.PriorityQueue({a[0] if a else 0})")

    register_lib_call("queue", "SimpleQueue",
        lambda a: f"{_Q}.SimpleQueue()")

    register_lib_call("queue", "put",
        lambda a: f"{a[0]}.put({a[1]}{',' + a[2] if len(a)>2 else ''})" if len(a) > 1 else f"{a[0]}.put(None)")

    register_lib_call("queue", "put_nowait",
        lambda a: f"{a[0]}.put_nowait({a[1]})" if len(a) > 1 else f"{a[0]}.put_nowait(None)")

    register_lib_call("queue", "get",
        lambda a: f"{a[0]}.get({a[1] if len(a)>1 else ''})")

    register_lib_call("queue", "get_nowait",
        lambda a: f"{a[0]}.get_nowait()")

    register_lib_call("queue", "empty",
        lambda a: f"{a[0]}.empty()")

    register_lib_call("queue", "full",
        lambda a: f"{a[0]}.full()")

    register_lib_call("queue", "qsize",
        lambda a: f"{a[0]}.qsize()")

    register_lib_call("queue", "task_done",
        lambda a: f"{a[0]}.task_done()")

    register_lib_call("queue", "join",
        lambda a: f"{a[0]}.join()")
