"""Admin API package.

Split out of the former monolithic admin.py. Every submodule registers its
endpoints on the single shared ``router`` defined in ``_base``; importing the
submodules here is what wires those routes up.
"""
from ._base import router
from . import (  # noqa: F401  (imported for side-effect: route registration)
    auth,
    conversations,
    departments,
    realtime,
    content,
    moderation,
    insights,
    bots,
    forms,
    cookies,
)

__all__ = ["router"]
