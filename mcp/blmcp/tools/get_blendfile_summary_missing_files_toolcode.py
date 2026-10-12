# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for reporting missing external file references.
"""

__all__ = (
    "Result",
    "main",
)

import glob
import os
from collections.abc import Callable
from typing import NamedTuple


class Result(NamedTuple):
    status: str
    missing_files: list[dict[str, str]]
    total_checked: int


def _file_path_foreach_legacy(visit: Callable[[object, str, object], None]) -> None:
    """
    Blender < 5.0 has no ``BlendData.file_path_foreach``: list paths with ``blend_paths``,
    matching owners from data-blocks that have a ``filepath``.
    """
    import bpy  # pylint: disable=import-error,no-name-in-module

    def _key(path: str) -> str:
        return os.path.normcase(os.path.normpath(path))

    owners: dict[str, object] = {}
    for attr in dir(bpy.data):
        collection = getattr(bpy.data, attr, None)
        if not isinstance(collection, bpy.types.bpy_prop_collection):
            continue
        for id_data in collection:
            filepath = getattr(id_data, "filepath", None)
            if isinstance(filepath, str) and filepath:
                owners.setdefault(_key(bpy.path.abspath(filepath, library=id_data.library)), id_data)

    for path in bpy.utils.blend_paths(absolute=True, packed=True):
        owner = owners.get(_key(path))
        # Resolve UDIM tokens like `RESOLVE_TOKEN` does, an unmatched pattern is reported as-is.
        tiles: list[str] = []
        for token in ("<UDIM>", "<UVTILE>"):
            if token in path:
                tiles = sorted(glob.glob(glob.escape(path).replace(glob.escape(token), "*")))
                break
        for tile_path in tiles or [path]:
            visit(owner, tile_path, None)


def main(params: None) -> Result:
    del params
    import bpy  # pylint: disable=import-error,no-name-in-module

    missing: list[dict[str, str]] = []
    checked = 0

    def _visit(id_data: object, path: str, _placeholder: object) -> None:
        nonlocal checked
        checked += 1
        filepath = bpy.path.abspath(path)
        if not os.path.exists(filepath):
            missing.append({
                "id_type": type(id_data).__name__ if id_data is not None else "",
                "id_name": getattr(id_data, "name", ""),
                "path": filepath,
            })

    if hasattr(bpy.data, "file_path_foreach"):
        bpy.data.file_path_foreach(
            _visit,
            flags={"SKIP_PACKED", "SKIP_WEAK_REFERENCES", "RESOLVE_TOKEN"},
        )
    else:
        _file_path_foreach_legacy(_visit)

    return Result(status="ok", missing_files=missing, total_checked=checked)
