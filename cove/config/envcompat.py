"""Backwards compatibility for the project rename.

Settings are read from COVE_* environment variables. Before the project was renamed they were called VISION_*;
those old names are still accepted as aliases so existing .env files, scripts and compose files keep working.
A COVE_* value always wins over its legacy twin.
"""
import os

_LEGACY_PREFIX = "VISION_"
_PREFIX = "COVE_"


def apply_legacy_env_aliases() -> None:
    for key, value in list(os.environ.items()):
        if key.startswith(_LEGACY_PREFIX):
            os.environ.setdefault(_PREFIX + key[len(_LEGACY_PREFIX):], value)
