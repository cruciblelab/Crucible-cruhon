"""Image (@image.*) PIL/Pillow wrappers for Cruhon. Requires: pip install pillow"""
from ..registry import register_lib, register_lib_call

_BUILTIN = "__builtin__"
_PIL = "__import__('PIL.Image', fromlist=['Image'])"
_PILF = "__import__('PIL.ImageFilter', fromlist=['ImageFilter'])"
_PILD = "__import__('PIL.ImageDraw', fromlist=['ImageDraw'])"


def register():
    register_lib("image", _BUILTIN)

    register_lib_call("image", "open",
        lambda args: f"{_PIL}.open({args[0]})" if args else f"{_PIL}.open('')")

    register_lib_call("image", "new",
        lambda args: (
            f"{_PIL}.new({args[0]}, ({args[1]}, {args[2]}))" if len(args) >= 3
            else f"{_PIL}.new('RGB', (100, 100))"
        ))

    register_lib_call("image", "save",
        lambda args: (
            f"(lambda __img: __img.save({args[1]}))({args[0]})" if len(args) >= 2
            else "None"
        ))

    register_lib_call("image", "resize",
        lambda args: (
            f"{args[0]}.resize(({args[1]}, {args[2]}))" if len(args) >= 3
            else f"{args[0]}.resize((100, 100))" if args else "None"
        ))

    register_lib_call("image", "rotate",
        lambda args: (
            f"{args[0]}.rotate({args[1]})" if len(args) >= 2
            else f"{args[0]}.rotate(0)" if args else "None"
        ))

    register_lib_call("image", "crop",
        lambda args: (
            f"{args[0]}.crop(({args[1]}, {args[2]}, {args[3]}, {args[4]}))"
            if len(args) >= 5 else "None"
        ))

    register_lib_call("image", "convert",
        lambda args: (
            f"{args[0]}.convert({args[1]})" if len(args) >= 2
            else f"{args[0]}.convert('RGB')" if args else "None"
        ))

    register_lib_call("image", "size",
        lambda args: f"{args[0]}.size" if args else "(0, 0)")

    register_lib_call("image", "width",
        lambda args: f"{args[0]}.width" if args else "0")

    register_lib_call("image", "height",
        lambda args: f"{args[0]}.height" if args else "0")

    register_lib_call("image", "mode",
        lambda args: f"{args[0]}.mode" if args else "''")

    register_lib_call("image", "thumbnail",
        lambda args: (
            f"(lambda __img: (__img.thumbnail(({args[1]}, {args[2]})), __img)[1])({args[0]})"
            if len(args) >= 3 else "None"
        ))

    register_lib_call("image", "flip_h",
        lambda args: (
            f"{_PIL}.FLIP_LEFT_RIGHT and {args[0]}.transpose({_PIL}.FLIP_LEFT_RIGHT)"
            if args else "None"
        ))

    register_lib_call("image", "flip_v",
        lambda args: (
            f"{args[0]}.transpose({_PIL}.FLIP_TOP_BOTTOM)" if args else "None"
        ))

    register_lib_call("image", "grayscale",
        lambda args: f"{args[0]}.convert('L')" if args else "None")

    register_lib_call("image", "show",
        lambda args: f"(lambda __img: (__img.show(), __img)[1])({args[0]})" if args else "None")

    register_lib_call("image", "format",
        lambda args: f"{args[0]}.format" if args else "None")

    register_lib_call("image", "to_bytes",
        lambda args: (
            f"(lambda __io, __img: (__img.save(__io, format={args[1]}), __io.getvalue())[1])"
            f"(__import__('io').BytesIO(), {args[0]})"
            if len(args) >= 2
            else f"(lambda __io, __img: (__img.save(__io, format='PNG'), __io.getvalue())[1])"
            f"(__import__('io').BytesIO(), {args[0]})"
            if args else "b''"
        ))

    register_lib_call("image", "paste",
        lambda args: (
            f"(lambda __dst: (__dst.paste({args[1]}, ({args[2]}, {args[3]})), __dst)[1])({args[0]})"
            if len(args) >= 4 else "None"
        ))
