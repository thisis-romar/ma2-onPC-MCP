"""
Import/Export Function Keywords for grandMA2 Command Builder

Handles export of show objects to disk and import from disk into the show.

Live-validated on grandMA2 onPC 3.9.60.65. Key findings:
- /path= is omitted intentionally: Windows paths with spaces in "MA Lighting
  Technologies" break MA2 command parsing, and the MA2 internal path
  (/data/ma/actual/gma2/...) fails for imports. Default routing is reliable.
- Import requires a destination (At ObjectType N); omitting it gives Error #28.
- MA2 routes files to type-specific subfolders automatically:
    macros/, effects/, plugins/, matricks/, masks/ — or importexport/ (default)

Included functions:
- export_object: Build an Export command
- import_object: Build an Import command
"""

# Object types that can be exported (validated live on MA2 3.9.60.65)
EXPORT_OBJECT_TYPES = {
    "group", "preset", "macro", "effect", "sequence", "view", "page",
    "camera", "layout", "form", "plugin", "matricks", "mask", "image",
    "executor", "timecode", "userprofile", "channel", "screen",
}

# Object types that can be imported (Screen excluded — Error #16 RESIZE FORBIDDEN)
IMPORT_OBJECT_TYPES = {
    "group", "preset", "macro", "effect", "sequence", "view", "page",
    "camera", "layout", "form", "plugin", "matricks", "mask", "image",
    "executor", "timecode", "userprofile",
}

# Type-specific subfolders (informational, used in docstrings/tool descriptions)
# MA2 routes automatically — these are shown in MA2 feedback messages
IMPORT_EXPORT_SUBFOLDERS = {
    "macro": "macros/",
    "effect": "effects/",
    "plugin": "plugins/",
    "matricks": "matricks/",
    "mask": "masks/",
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
