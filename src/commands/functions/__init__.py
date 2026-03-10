"""
Function Keywords for grandMA2 Command Builder

This module organizes Function Keywords by functionality into multiple submodules:
- store.py: Store-related functions
- selection.py: Selection and clear-related functions
- playback.py: Playback control-related functions
- edit.py: Edit operations (Copy, Move, Delete, Remove)
- assignment.py: Assignment-related functions
- labeling.py: Label and appearance-related functions
- values.py: Value setting functions (At keyword)
- info.py: Information query functions (List, Info)
- macro.py: Macro placeholder-related functions

Function keywords are the "verbs" of the console. They perform a task or
function and are often followed by objects to which the function applies.
Some functions are global and do not need to be followed by objects.

Examples: Store, Delete, Copy, Goto, Clear, Label, SelFix, Go, Pause
"""

# Store Function Keywords
# Backward Compatibility Aliases
# select_group -> group (from objects.py)
# call_preset -> preset (from objects.py)
from ..objects import group as select_group
from ..objects import preset as call_preset

# Assignment Function Keywords
from .assignment import (
    assign,
    assign_delay,
    assign_fade,
    assign_function,
    assign_property,
    assign_to_layout,
    empty,
    temp_fader,
)

# Call Function Keywords
from .call import (
    call,
)

# Edit Function Keywords (Edit, Cut, Paste, Copy, Move, Delete, Remove)
from .edit import (
    copy,
    copy_cue,
    cut,
    delete,
    delete_cue,
    delete_fixture,
    delete_group,
    delete_messages,
    delete_preset,
    edit,
    move,
    oops,
    paste,
    remove,
    remove_effect,
    remove_fixture,
    remove_preset_type,
    remove_selection,
)

# Helping Keywords (Plus +, Minus -, And, If)
from .helping import (
    add_to_selection,
    at_relative,
    condition_and,
    if_condition,
    page_next,
    page_previous,
    remove_from_selection,
)

# Import/Export Function Keywords
from .importexport import (
    export_object,
    import_fixture_type_cmd,
    import_layer_cmd,
    import_object,
)

# Info Function Keywords (List, Info)
from .info import (
    info,
    info_cue,
    info_group,
    info_preset,
    list_attribute,
    list_cue,
    list_effect_library,
    list_group,
    list_library,
    list_macro_library,
    list_messages,
    list_objects,
    list_oops,
    list_preset,
    list_shows,
)

# Labeling Function Keywords (Label, Appearance)
from .labeling import (
    appearance,
    label,
    label_group,
    label_preset,
)

# Macro Placeholder Function Keywords
from .macro import (
    macro_with_input_after,
    macro_with_input_before,
)

# Navigation Function Keywords (ChangeDest / cd)
from .navigation import (
    changedest,
)

# Park Function Keywords (Park, Unpark)
from .park import (
    park,
    unpark,
)

# Playback Function Keywords (Go, Pause, Goto, GoFast, DefGo)
from .playback import (
    blackout,
    blind,
    def_go_back,
    def_go_forward,
    def_go_pause,
    flash_executor,
    freeze,
    go,
    go_back,
    go_back_executor,
    go_executor,
    go_fast_back,
    go_fast_forward,
    go_macro,
    go_sequence,
    goto,
    goto_cue,
    goto_timecode,
    off_executor,
    on_executor,
    pause_sequence,
    release_executor,
    solo,
    solo_executor,
)

# Selection Function Keywords (SelFix, Clear)
from .selection import (
    clear,
    clear_active,
    clear_all,
    clear_selection,
    highlight,
    select_fixture,
)
from .store import (
    delete_show,
    load_show,
    new_show,
    save_show,
    store,
    store_cue,
    store_cue_timed,
    store_group,
    store_preset,
    update,
    update_cue,
)

# Values Function Keywords (At)
from .values import (
    at,
    at_full,
    at_zero,
    attribute_at,
    channel_at,
    executor_at,
    fixture_at,
    group_at,
    preset_type_at,
)

# Variable Function Keywords
from .variables import (
    add_user_var,
    add_var,
    get_user_var,
    list_user_var,
    list_var,
    set_user_var,
    set_var,
)

__all__ = [
    # Import/Export Function Keywords
    "export_object",
    "import_object",
    "import_fixture_type_cmd",
    "import_layer_cmd",
    # Store / Update / Show management
    "store",
    "store_cue",
    "store_cue_timed",
    "store_group",
    "store_preset",
    "save_show",
    "delete_show",
    "update",
    "update_cue",
    # SelFix
    "select_fixture",
    # Clear
    "clear",
    "clear_selection",
    "clear_active",
    "clear_all",
    # Label
    "label",
    "label_group",
    "label_preset",
    # Delete
    "delete",
    "delete_cue",
    "delete_group",
    "delete_preset",
    "delete_fixture",
    "delete_messages",
    # Remove
    "remove",
    "remove_selection",
    "remove_preset_type",
    "remove_fixture",
    "remove_effect",
    # Go
    "go",
    "go_executor",
    "go_macro",
    # GoBack
    "go_back",
    "go_back_executor",
    # Goto
    "goto",
    # Go/Pause/Goto (Legacy)
    "go_sequence",
    "pause_sequence",
    "goto_cue",
    # GoFast
    "go_fast_back",
    "go_fast_forward",
    # DefGo (Selected Executor)
    "def_go_back",
    "def_go_forward",
    "def_go_pause",
    # Executor on/off/flash/solo/release
    "on_executor",
    "off_executor",
    "flash_executor",
    "solo",
    "solo_executor",
    "release_executor",
    # Blackout
    "blackout",
    # Blind / Freeze (universal toggles)
    "blind",
    "freeze",
    # Highlight
    "highlight",
    # Timecode goto
    "goto_timecode",
    # Edit
    "edit",
    # Cut
    "cut",
    # Paste
    "paste",
    # Copy
    "copy",
    "copy_cue",
    # Move
    "move",
    # Oops (undo)
    "oops",
    # Assign
    "assign",
    "assign_delay",
    "assign_property",
    "assign_function",
    "assign_fade",
    "assign_to_layout",
    "empty",
    "temp_fader",
    # Appearance
    "appearance",
    # At
    "at",
    "at_full",
    "at_zero",
    "fixture_at",
    "channel_at",
    "group_at",
    "executor_at",
    "preset_type_at",
    "attribute_at",
    # List
    "list_objects",
    "list_cue",
    "list_group",
    "list_preset",
    "list_attribute",
    "list_messages",
    # List* (specialized)
    "list_shows",
    "list_oops",
    "list_library",
    "list_effect_library",
    "list_macro_library",
    # Info
    "info",
    "info_group",
    "info_cue",
    "info_preset",
    # Macro Placeholder
    "macro_with_input_after",
    "macro_with_input_before",
    # Helping Keywords (Plus +, Minus -, And, If)
    "at_relative",
    "add_to_selection",
    "remove_from_selection",
    "page_next",
    "page_previous",
    "condition_and",
    "if_condition",
    # Park Function Keywords
    "park",
    "unpark",
    # Call Function Keywords
    "call",
    # Variable Function Keywords
    "set_user_var",
    "set_var",
    "add_user_var",
    "add_var",
    "get_user_var",
    "list_var",
    "list_user_var",
    # Show Management
    "load_show",
    "new_show",
    # Navigation Function Keywords
    "changedest",
    # Backward Compatibility Aliases
    "select_group",
    "call_preset",
]
