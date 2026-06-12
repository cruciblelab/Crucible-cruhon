"""Collections stdlib wrappers for Cruhon — @collections.*"""
from ..registry import register_lib, register_lib_call

_C = "__import__('collections')"


def register():
    register_lib("collections", "collections")

    # Counter
    register_lib_call("collections", "Counter",
        lambda a: f"{_C}.Counter({a[0] if a else ''})")

    register_lib_call("collections", "counter_most_common",
        lambda a: f"{a[0]}.most_common({a[1] if len(a)>1 else ''})")

    register_lib_call("collections", "counter_update",
        lambda a: f"{a[0]}.update({a[1]})")

    register_lib_call("collections", "counter_subtract",
        lambda a: f"{a[0]}.subtract({a[1]})")

    # defaultdict
    register_lib_call("collections", "defaultdict",
        lambda a: f"{_C}.defaultdict({a[0] if a else 'list'})")

    # deque
    register_lib_call("collections", "deque",
        lambda a: (
            f"{_C}.deque({a[0]}, maxlen={a[1]})" if len(a) > 1 else
            f"{_C}.deque({a[0]})" if a else
            f"{_C}.deque()"
        ))

    register_lib_call("collections", "deque_append",
        lambda a: f"{a[0]}.append({a[1]})")

    register_lib_call("collections", "deque_appendleft",
        lambda a: f"{a[0]}.appendleft({a[1]})")

    register_lib_call("collections", "deque_pop",
        lambda a: f"{a[0]}.pop()")

    register_lib_call("collections", "deque_popleft",
        lambda a: f"{a[0]}.popleft()")

    register_lib_call("collections", "deque_rotate",
        lambda a: f"{a[0]}.rotate({a[1] if len(a)>1 else 1})")

    register_lib_call("collections", "deque_extend",
        lambda a: f"{a[0]}.extend({a[1]})")

    # namedtuple
    register_lib_call("collections", "namedtuple",
        lambda a: f"{_C}.namedtuple({a[0]}, {a[1]})" if len(a) > 1 else f"{_C}.namedtuple({a[0]}, [])")

    # OrderedDict
    register_lib_call("collections", "OrderedDict",
        lambda a: f"{_C}.OrderedDict({a[0] if a else ''})")

    register_lib_call("collections", "ordered_move_to_end",
        lambda a: f"{a[0]}.move_to_end({a[1]}{', last=' + a[2] if len(a)>2 else ''})")

    # ChainMap
    register_lib_call("collections", "ChainMap",
        lambda a: f"{_C}.ChainMap({', '.join(a)})")

    register_lib_call("collections", "chainmap_new_child",
        lambda a: f"{a[0]}.new_child({a[1] if len(a)>1 else ''})")

    # UserDict / UserList / UserString
    register_lib_call("collections", "UserDict",
        lambda a: f"{_C}.UserDict({a[0] if a else ''})")

    register_lib_call("collections", "UserList",
        lambda a: f"{_C}.UserList({a[0] if a else ''})")

    register_lib_call("collections", "UserString",
        lambda a: f"{_C}.UserString({a[0]})" if a else f"{_C}.UserString('')")
