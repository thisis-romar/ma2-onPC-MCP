# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
Import/Export Function Keywords for grandMA2 Command Builder

Handles export of show objects to disk and import from disk into the show.

Live-validated on grandMA2 onPC 3.9.60.65. Key findings:
- /path= is omitted intentionally: Windows paths with spaces in "MA Lighting
  Technologies" break MA2 command parsing, and the MA2 internal path
  (/data/ma/actual/gma2/...) fails for imports. Default routing is reliable.
- Import requires a destination (At ObjectType N); omitting it gives Error #28.
- MA2 routes files to type-specific subfolders automatically:
    macros/, effects/, plugins/, matricks/, masks/, colors/ (gel), fixtures/ (fixture)
    — or importexport/ (default for all other types)

Fixture type import (EditSetup/FixtureTypes context):
- Key format: "manufacturer@fixture@mode"  e.g. "Martin@Mac700Profile_Extended@Extended"
- Must be sent while in EditSetup/FixtureTypes context (via ChangeDest navigation)

Fixture layer import (EditSetup/Layers context):
- File must exist in importexport/ directory
- Must be sent while in EditSetup/Layers context (via ChangeDest navigation)

Included functions:
- export_object: Build an Export command
- import_object: Build an Import command
- import_fixture_type_cmd: Build Import command for a library fixture type (EditSetup/FixtureTypes context)
- import_layer_cmd: Build Import command for a fixture layer XML file (EditSetup/Layers context)
"""

# Object types that can be exported (validated live on MA2 3.9.60.65 via probe_export_types.py)
# Original 20 types confirmed OK; new types added after live export probe 2026-05-20.
# Types marked EMPTY_SLOT: command accepted by MA2 but no objects existed in show during probe.
EXPORT_OBJECT_TYPES = {
    # Cue / playback
    "group", "preset", "macro", "effect", "sequence",
    # Show structure
    "view", "page", "camera", "layout", "form",
    # Utility / special
    "plugin", "matricks", "mask", "image",
    "executor", "timecode", "userprofile", "channel", "screen", "filter",
    # Fixture / patch data (probe EXPORT_OK 2026-05-20)
    "fixture",          # routes to fixtures/ subfolder
    "gel",              # routes to colors/ subfolder; exports entire GelPool
    # World / filter pool (probe EXPORT_OK 2026-05-20)
    "world",
    # Timing / dynamics (probe EXPORT_OK 2026-05-20)
    "fadepath",
    # DMX control (probe EXPORT_OK 2026-05-20)
    "profile",          # DMX_Profile dimmer curve
    # 3D visualizer objects (probe EXPORT_OK 2026-05-20)
    "item3d", "surface", "model",
    # User accounts (probe EXPORT_OK 2026-05-20)
    "user",
    # Special masters container (probe EXPORT_OK 2026-05-20; exports all 11 master slots together)
    "specialmaster",
    # Scheduling / capture (probe EXPORT_EMPTY_SLOT 2026-05-20: command accepted, pool was empty)
    "agenda", "dmxsnapshot", "flightrecording",
}

# Object types that can be imported (Screen excluded — Error #16 RESIZE FORBIDDEN)
# Note: newly probed EXPORT_OK types are NOT added here until import viability is separately probed.
IMPORT_OBJECT_TYPES = {
    "group", "preset", "macro", "effect", "sequence", "view", "page",
    "camera", "layout", "form", "plugin", "matricks", "mask", "image",
    "executor", "timecode", "userprofile", "filter",
}

# Type-specific subfolders (informational, used in docstrings/tool descriptions)
# MA2 routes automatically — these are shown in MA2 feedback messages
IMPORT_EXPORT_SUBFOLDERS = {
    "macro": "macros/",
    "effect": "effects/",
    "plugin": "plugins/",
    "matricks": "matricks/",
    "mask": "masks/",
    "gel": "colors/",       # probe confirmed: Gel routes to colors/ not importexport/
    "fixture": "fixtures/", # probe confirmed: Fixture routes to fixtures/ not importexport/
    # all others → importexport/
}


def export_object(
    object_type: str,
    object_id: str | int | None = None,
    filename: str | None = None,
    *,
    overwrite: bool = False,
    noconfirm: bool = False,
    style: str | None = None,
) -> str:
    """
    Construct an Export command.

    MA2 syntax: Export [ObjectType] [ID] ["filename"] [/flags]

    Args:
        object_type: Object type keyword (e.g. "Group", "Preset", "Macro")
        object_id: ID, range ("1 thru 5"), preset ref ("1.3"), or None for all
        filename: Output filename without extension or path
        overwrite: Add /overwrite flag
        noconfirm: Add /noconfirm flag
        style: "csv" or "html" (default: xml)

    Returns:
        str: MA2 export command string

    Examples:
        >>> export_object("Group", 1, "mygroups")
        'export Group 1 "mygroups"'
        >>> export_object("Macro", "1 thru 5", "macros", overwrite=True)
        'export Macro 1 thru 5 "macros" /overwrite'
        >>> export_object("Preset", "1.3", "dimmer3", noconfirm=True)
        'export Preset 1.3 "dimmer3" /noconfirm'
        >>> export_object("Sequence", 2, "seq2", style="csv")
        'export Sequence 2 "seq2" /style=csv'
    """
    parts = ["export", object_type]
    if object_id is not None:
        parts.append(str(object_id))
    if filename is not None:
        parts.append(f'"{filename}"')

    options = []
    if overwrite:
        options.append("/overwrite")
    if noconfirm:
        options.append("/noconfirm")
    if style is not None:
        options.append(f"/style={style}")
    if options:
        parts.extend(options)

    return " ".join(parts)


def import_object(
    filename: str,
    destination_type: str,
    destination_id: str | int | None = None,
    *,
    noconfirm: bool = False,
    quiet: bool = False,
) -> str:
    """
    Construct an Import command.

    MA2 syntax: Import "filename" At ObjectType [N] [/flags]

    Destination is required — MA2 returns Error #28 (NO CUE SOURCE GIVEN)
    without it. MA2 routes the file lookup to the correct type-specific
    subfolder automatically.

    Args:
        filename: Source filename without extension or path
        destination_type: Object type keyword (e.g. "Group", "Macro")
        destination_id: Slot number or preset ref ("T.N"). None = next free slot
        noconfirm: Add /noconfirm flag
        quiet: Add /quiet flag (suppress output messages)

    Returns:
        str: MA2 import command string

    Examples:
        >>> import_object("mygroups", "Group", 5)
        'import "mygroups" at Group 5'
        >>> import_object("macros", "Macro")
        'import "macros" at Macro'
        >>> import_object("preset_dimmer", "Preset", "1.99", noconfirm=True)
        'import "preset_dimmer" at Preset 1.99 /noconfirm'
        >>> import_object("show_backup", "Group", 10, quiet=True)
        'import "show_backup" at Group 10 /quiet'
    """
    parts = ["import", f'"{filename}"', "at", destination_type]
    if destination_id is not None:
        parts.append(str(destination_id))

    options = []
    if noconfirm:
        options.append("/noconfirm")
    if quiet:
        options.append("/quiet")
    if options:
        parts.extend(options)

    return " ".join(parts)


def import_fixture_type_cmd(manufacturer: str, fixture: str, mode: str) -> str:
    """
    Build the Import command for a library fixture type.

    Must be sent while in EditSetup/FixtureTypes context (via ChangeDest navigation).
    MA2 key format: 'manufacturer@fixture@mode'

    Args:
        manufacturer: Manufacturer name as it appears in MA2 library (e.g. "Martin")
        fixture: Fixture model name (e.g. "Mac700Profile_Extended")
        mode: Mode string (e.g. "Extended", "Standard")

    Returns:
        str: MA2 import command string for the fixture type

    Examples:
        >>> import_fixture_type_cmd("Martin", "Mac700Profile_Extended", "Extended")
        'Import "Martin@Mac700Profile_Extended@Extended"'
        >>> import_fixture_type_cmd("Generic", "Dimmer", "Mode 1")
        'Import "Generic@Dimmer@Mode 1"'
    """
    return f'Import "{manufacturer}@{fixture}@{mode}"'


def import_layer_cmd(filename: str, layer_index: int | None = None) -> str:
    """
    Build the Import command for a fixture layer XML file.

    Must be sent while in EditSetup/Layers context (via ChangeDest navigation).
    The file must exist in the MA2 importexport directory.

    Args:
        filename: Layer XML filename without extension or path
        layer_index: Target layer slot. None = MA2 picks next free slot

    Returns:
        str: MA2 import command string for the layer file

    Examples:
        >>> import_layer_cmd("dimmers")
        'Import "dimmers"'
        >>> import_layer_cmd("mac700s", 2)
        'Import "mac700s" At 2'
        >>> import_layer_cmd("my_fixtures", 1)
        'Import "my_fixtures" At 1'
    """
    parts = ["Import", f'"{filename}"']
    if layer_index is not None:
        parts.extend(["At", str(layer_index)])
    return " ".join(parts)
