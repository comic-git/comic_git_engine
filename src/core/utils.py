"""Compatibility imports for integrations that still reference the former combined module.

New engine code must import :mod:`core.stdlib_utils` or :mod:`core.rendering_utils`
directly. This module deliberately resolves attributes dynamically so callers that
inspect renderer state continue to observe the renderer's current state.
"""

from core import rendering_utils, stdlib_utils


def __getattr__(name: str):
    for module in (stdlib_utils, rendering_utils):
        try:
            return getattr(module, name)
        except AttributeError:
            continue
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
