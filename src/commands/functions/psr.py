# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
PSR (Partial Show Read) Function Keywords for grandMA2 Command Builder

PSR allows selective import of objects from one show file into another
without loading the entire show. The workflow is:

1. PSRPrepare "source_show" — lock the source show file for reading
2. PSRList "source_show"  — enumerate available objects in the source show
3. PSR "source_show" ObjectType [ID] [/merge] — read objects into current show

Included functions:
- psr_prepare: Lock source show for PSR reading
- psr_list: List objects available in a source show
- psr: Read (import) objects from a source show into the current show
"""


def psr_prepare(source_show: str) -> str:
    """
    Construct a PSRPrepare command to lock a source show for PSR reading.

    PSRPrepare must be called before PSRList or PSR to make the source
    show available for partial read operations.

    Args:
        source_show: Name of the source show file (without .show extension).

    Returns:
        str: MA command string

    Examples:
        >>> psr_prepare("my_show")
        'PSRPrepare "my_show"'
        >>> psr_prepare("venue_2024")
        'PSRPrepare "venue_2024"'
    """
    return f'PSRPrepare "{source_show}"'


def psr_list(source_show: str) -> str:
    """
    Construct a PSRList command to enumerate available objects in a source show.

    Returns a list of object types and IDs that can be imported via PSR.
    Run PSRPrepare first to lock the source show.

    Args:
        source_show: Name of the source show file (without .show extension).

    Returns:
        str: MA command string

    Examples:
        >>> psr_list("my_show")
        'PSRList "my_show"'
    """
    return f'PSRList "{source_show}"'


def psr(
    source_show: str,
    object_type: str,
    object_id: str | int | None = None,
    *,
    merge: bool = False,
) -> str:
    """
    Construct a PSR command to import objects from a source show.

    Reads one or more objects of the given type from the source show into
    the current show. The destination slot must be free or the /merge flag
    used to merge into an existing object.

    Args:
        source_show: Name of the source show file (without .show extension).
        object_type: MA2 object type keyword, e.g. "Cue", "Sequence", "Group",
                     "Preset", "Macro", "Effect", "Timecode".
        object_id: Optional object ID or range string (e.g. 1, "1 Thru 5", "1.1").
                   Omit to import all objects of the given type.
        merge: If True, appends /merge flag to merge into existing objects
               rather than replacing them.

    Returns:
        str: MA command string

    Examples:
        >>> psr("my_show", "Cue", "1", merge=False)
        'PSR "my_show" Cue 1'
        >>> psr("my_show", "Sequence", 1, merge=True)
        'PSR "my_show" Sequence 1 /merge'
        >>> psr("my_show", "Group")
        'PSR "my_show" Group'
        >>> psr("my_show", "Preset", "1 Thru 5")
        'PSR "my_show" Preset 1 Thru 5'
    """
    cmd = f'PSR "{source_show}" {object_type}'
    if object_id is not None:
        cmd += f" {object_id}"
    if merge:
        cmd += " /merge"
    return cmd
