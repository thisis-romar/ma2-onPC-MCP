"""
Selection & Clear Function Keywords for grandMA2 Command Builder

This module contains functions related to fixture selection and programmer clearing.

Included functions:
- select_fixture (SelFix): Select fixtures
- clear: Clear (sequentially executes selection -> active -> all)
- clear_selection: Deselect all fixtures
- clear_active: Deactivate all active values
- clear_all: Empty entire programmer
- if_active: Filter selection to fixtures with active output
- if_output: Filter selection to fixtures with any output value
- if_prog: Filter selection to fixtures with programmer values
- end_if: Close a macro conditional block
- full_highlight: FullHighlight combined mode toggle
- blind_edit: Enter blind edit mode (MA+Edit shortcut)
- shuffle_selection: Randomise fixture selection order
- shuffle_values: Randomise programmer values across selection
"""


# ============================================================================
# SELFIX FUNCTION KEYWORD
# ============================================================================


def select_fixture(
    ids: int | list[int] | None = None,
    end: int | None = None,
    *,
    start: int | None = None,
    thru_all: bool = False,
    select_all: bool = False,
) -> str:
    """
    Construct an MA command to select fixtures.

    Args:
        ids: Fixture number(s), single int or list
        end: Ending number (for range selection)
        start: Starting number (for keyword argument form)
        thru_all: If True, select from start to the end
        select_all: If True, select all fixtures

    Returns:
        str: MA command string

    Examples:
        >>> select_fixture(1)
        'selfix fixture 1'
        >>> select_fixture([1, 3, 5])
        'selfix fixture 1 + 3 + 5'
        >>> select_fixture(1, 10)
        'selfix fixture 1 thru 10'
    """
    if select_all:
        return "selfix fixture thru"

    if ids is None and start is None and end is not None:
        return f"selfix fixture thru {end}"

    if thru_all and start is not None:
        return f"selfix fixture {start} thru"

    actual_start: int | None = None

    if ids is not None:
        if isinstance(ids, list):
            if len(ids) == 1:
                return f"selfix fixture {ids[0]}"
            fixtures_str = " + ".join(str(id) for id in ids)
            return f"selfix fixture {fixtures_str}"
        else:
            actual_start = ids
    elif start is not None:
        actual_start = start

    if actual_start is not None and end is not None:
        if actual_start == end:
            return f"selfix fixture {actual_start}"
        return f"selfix fixture {actual_start} thru {end}"

    if actual_start is not None:
        return f"selfix fixture {actual_start}"

    raise ValueError("Must provide at least one selection parameter")


# ============================================================================
# HIGHLIGHT FUNCTION KEYWORD
# ============================================================================


def highlight(
    on: bool = True,
    object_type: str | None = None,
    object_id: int | str | None = None,
) -> str:
    """
    Toggle highlight mode, optionally scoped to an object.

    Highlight is universal — accepted by all 16 object types (live-verified).
    When called with an object it highlights that specific object.
    When called bare it toggles highlight on/off for the current selection.

    Args:
        on: True to enable, False to disable highlight (only used when no object given)
        object_type: Object type (optional — scopes highlight to an object)
        object_id: Object ID

    Returns:
        str: MA command to toggle highlight

    Examples:
        >>> highlight()
        'highlight on'
        >>> highlight(False)
        'highlight off'
        >>> highlight(object_type="executor", object_id=3)
        'highlight executor 3'
        >>> highlight(object_type="group", object_id=5)
        'highlight group 5'
    """
    if object_type is not None and object_id is not None:
        return f"highlight {object_type} {object_id}"
    if object_type is not None:
        return f"highlight {object_type}"
    return f"highlight {'on' if on else 'off'}"


# ============================================================================
# CLEAR FUNCTION KEYWORD
# ============================================================================


def clear() -> str:
    """
    Construct a Clear command.

    The Clear command has three sequential functions depending on programmer status:
    1. Clear selection (deselects all fixtures)
    2. Clear active values (deactivates all values)
    3. Clear all (empties programmer)

    Returns:
        str: MA command to clear
    """
    return "clear"


def clear_selection() -> str:
    """
    Construct a ClearSelection command to deselect all fixtures.

    Returns:
        str: MA command to clear selection
    """
    return "clearselection"


def clear_active() -> str:
    """
    Construct a ClearActive command to inactivate all values in programmer.

    Returns:
        str: MA command to clear active values
    """
    return "clearactive"


def clear_all() -> str:
    """
    Construct a ClearAll command to empty the entire programmer.

    Returns:
        str: MA command to clear all
    """
    return "clearall"


# ============================================================================
# FIX FUNCTION KEYWORD
# ============================================================================
# Fix parks fixture values (pins them to current output, overriding playback).
# ============================================================================


def fix_fixture(
    ids: int | list[int] | None = None,
    end: int | None = None,
) -> str:
    """
    Fix (park) fixture values, pinning them to current output.

    When called without arguments, fixes all currently selected fixtures.
    Fix overrides playback and holds the fixture at its current output level.

    Args:
        ids: Fixture number(s) to fix (optional — fixes selection if omitted)
        end: End ID for range (thru syntax)

    Returns:
        str: MA command string

    Examples:
        >>> fix_fixture()
        'fix'
        >>> fix_fixture(1)
        'fix fixture 1'
        >>> fix_fixture([1, 3, 5])
        'fix fixture 1 + 3 + 5'
        >>> fix_fixture(1, end=10)
        'fix fixture 1 thru 10'
    """
    if ids is None:
        return "fix"
    if isinstance(ids, list):
        fixtures_str = " + ".join(str(i) for i in ids)
        return f"fix fixture {fixtures_str}"
    if end is not None:
        return f"fix fixture {ids} thru {end}"
    return f"fix fixture {ids}"


# ============================================================================
# LOCATE FUNCTION KEYWORD
# ============================================================================
# Locate fires fixtures to their locate (default) state.
# ============================================================================


def locate(
    fixture_ids: int | list[int] | None = None,
    end: int | None = None,
) -> str:
    """
    Locate selected fixtures (fire to default/locate state).

    Locate fires the selected fixtures to their default state: full intensity,
    open colour, centre position, beam fully open.

    When fixture_ids are provided, locates those specific fixtures.
    When called bare, resets the current selection.

    Args:
        fixture_ids: Fixture number(s), single int or list (optional)
        end: Ending number for range: fixture_ids Thru end (optional)

    Returns:
        str: MA command string

    Examples:
        >>> locate()
        'locate'
        >>> locate(1)
        'locate fixture 1'
        >>> locate(1, 10)
        'locate fixture 1 thru 10'
        >>> locate([1, 3, 5])
        'locate fixture 1 + 3 + 5'
    """
    if fixture_ids is None:
        return "locate"
    if isinstance(fixture_ids, list):
        ids_str = " + ".join(str(f) for f in fixture_ids)
        return f"locate fixture {ids_str}"
    if end is not None:
        return f"locate fixture {fixture_ids} thru {end}"
    return f"locate fixture {fixture_ids}"


# ============================================================================
# INVERT FUNCTION KEYWORD
# ============================================================================
# Invert reverses the current fixture selection.
# ============================================================================


def invert() -> str:
    """
    Invert the current fixture selection.

    Inverts the selection so all unselected fixtures become selected and
    all previously selected fixtures are deselected.

    Returns:
        str: MA command string

    Examples:
        >>> invert()
        'invert'
    """
    return "invert"


# ============================================================================
# ALIGN FUNCTION KEYWORD
# ============================================================================
# Align distributes programmer values evenly across a selection.
# ============================================================================


def align(mode: str | None = None) -> str:
    """
    Align programmer values across the current fixture selection.

    Align distributes the values in the programmer evenly from the first to
    the last fixture in the selection. The optional mode controls direction.

    Args:
        mode: Alignment mode — ">" left-to-right, "<" right-to-left,
            "><" center-out, "<>" edges-in, or None for default toggle.

    Returns:
        str: MA command string

    Examples:
        >>> align()
        'align'
        >>> align(">")
        'align >'
        >>> align("<>")
        'align <>'
    """
    if mode is not None:
        return f"align {mode}"
    return "align"


# ============================================================================
# FLIP FUNCTION KEYWORD
# ============================================================================


def flip() -> str:
    """
    Construct a Flip command to flip pan/tilt to alternate position.

    Flip cycles through alternative pan/tilt positions for moving lights
    that can reach the same point from different orientations.

    Returns:
        str: MA command string

    Examples:
        >>> flip()
        'Flip'
    """
    return "Flip"


# ============================================================================
# IF SELECTION FILTER KEYWORDS
# ============================================================================
# These qualifiers narrow the active fixture selection to only those matching
# the given output or programmer state condition.
# ============================================================================


def if_active() -> str:
    """
    Construct an 'If Active' command to filter selection to active fixtures.

    Narrows the current selection to fixtures that have at least one
    attribute at a non-zero output value (i.e. contributing to output).

    Returns:
        str: MA command string

    Examples:
        >>> if_active()
        'If Active'
    """
    return "If Active"


def if_output() -> str:
    """
    Construct an 'If Output' command to filter selection to fixtures with output.

    Narrows the current selection to fixtures that have any output value,
    whether driven by playback, park, or the programmer.

    Returns:
        str: MA command string

    Examples:
        >>> if_output()
        'If Output'
    """
    return "If Output"


def if_prog() -> str:
    """
    Construct an 'If Programmer' command to filter selection to programmer fixtures.

    Narrows the current selection to only those fixtures that currently
    have values active in the programmer.

    Returns:
        str: MA command string

    Examples:
        >>> if_prog()
        'If Programmer'
    """
    return "If Programmer"


def end_if() -> str:
    """
    Construct an 'EndIf' command to close a macro conditional block.

    EndIf terminates an If/While conditional block inside a grandMA2 macro.
    Not typically used as a standalone telnet command — primarily used
    in macro line construction via macro_condition_line().

    Returns:
        str: MA command string

    Examples:
        >>> end_if()
        'EndIf'
    """
    return "EndIf"


# ============================================================================
# FULL HIGHLIGHT / BLIND EDIT MODE KEYWORDS
# ============================================================================


def full_highlight() -> str:
    """
    Construct a FullHighlight command.

    FullHighlight is the combined Full + Highlight mode toggle.
    It fires all selected fixtures to full intensity while also
    engaging highlight mode, making selected fixtures stand out
    against a dimmed background.

    Keyboard shortcut: double-press the Full key.

    Returns:
        str: MA command string

    Examples:
        >>> full_highlight()
        'FullHighlight'
    """
    return "FullHighlight"


def blind_edit() -> str:
    """
    Construct a BlindEdit command to enter edit mode in blind.

    BlindEdit enters the edit view for the currently selected object
    while in blind mode, allowing cue editing without affecting live output.

    Keyboard shortcut: MA + Edit key.

    Returns:
        str: MA command string

    Examples:
        >>> blind_edit()
        'BlindEdit'
    """
    return "BlindEdit"


# ============================================================================
# SHUFFLE FUNCTION KEYWORDS
# ============================================================================


def shuffle_selection() -> str:
    """
    Construct a ShuffleSelection command to randomise fixture selection order.

    ShuffleSelection randomises the order of the currently selected fixtures
    so that MAtricks and alignment operations process them in a random sequence.
    Useful for creating organic, non-linear looks.

    Keyboard shortcut: MA + Align key.

    Returns:
        str: MA command string

    Examples:
        >>> shuffle_selection()
        'ShuffleSelection'
    """
    return "ShuffleSelection"


def shuffle_values() -> str:
    """
    Construct a ShuffleValues command to randomise programmer values.

    ShuffleValues redistributes the current programmer values randomly
    across the selected fixtures. The same set of values is preserved
    but assigned to different fixtures in the selection.

    Returns:
        str: MA command string

    Examples:
        >>> shuffle_values()
        'ShuffleValues'
    """
    return "ShuffleValues"


# ============================================================================
# PREVIEW MODE KEYWORDS
# ============================================================================


def preview(executor_id: int | None = None) -> str:
    """
    Construct a Preview command to enter preview mode for an executor.

    Preview mode shows the output of a cue without affecting live output.
    When called with an executor_id it previews that specific executor;
    when called bare it activates preview mode for the currently selected.

    Args:
        executor_id: Executor number (optional).

    Returns:
        str: MA command string

    Examples:
        >>> preview()
        'Preview'
        >>> preview(5)
        'Preview Executor 5'
    """
    if executor_id is not None:
        return f"Preview Executor {executor_id}"
    return "Preview"


def preview_edit(executor_id: int | None = None) -> str:
    """
    Construct a PreviewEdit command to open the preview editor for an executor.

    PreviewEdit opens the cue content editor while in preview mode so that
    cues can be edited without affecting the live output.

    Args:
        executor_id: Executor number (optional).

    Returns:
        str: MA command string

    Examples:
        >>> preview_edit()
        'PreviewEdit'
        >>> preview_edit(3)
        'PreviewEdit Executor 3'
    """
    if executor_id is not None:
        return f"PreviewEdit Executor {executor_id}"
    return "PreviewEdit"


def preview_executor(executor_id: int) -> str:
    """
    Construct a PreviewExecutor command to directly preview a specific executor.

    PreviewExecutor combines selecting and previewing an executor in a single
    command, making it faster to switch the preview target during programming.

    Args:
        executor_id: Executor number (required).

    Returns:
        str: MA command string

    Examples:
        >>> preview_executor(7)
        'PreviewExecutor 7'
    """
    return f"PreviewExecutor {executor_id}"
