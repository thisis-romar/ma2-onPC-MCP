"""
Command Builder Module for grandMA2

This module provides high-level functions to construct grandMA2 command strings.
These functions are responsible only for generating correctly formatted commands,
not for sending them.

According to coding-standards.md, these functions are "thin wrappers" that
only construct MA commands without any Telnet logic.

=============================================================================
grandMA2 Keyword Classification
=============================================================================

The grandMA2 command line syntax follows these general rules:
- Basic syntax: [Function] [Object]
- All objects have a default function which is used if no function is given.
- Most functions have a default object or object type.
- Objects are arranged in a hierarchical tree structure.

Keywords are classified into three types:

1. HELPING KEYWORDS (Prepositions/Conjunctions)
   - Used to create relations between functions and objects
   - Examples: At, Thru, +, If, While

2. OBJECT KEYWORDS (Nouns)
   - Used to allocate objects in your show file
   - Usually used with numbers, IDs, names, and labels
   - Examples: Fixture, Channel, Group, Preset, Cue, Sequence, Executor

3. FUNCTION KEYWORDS (Verbs)
   - Perform a task or function
   - Often followed by objects to which the function applies
   - Some functions are global and don't need objects (e.g., Blackout)
   - Examples: Store, Delete, Copy, Goto, Clear, Label, SelFix

=============================================================================
"""

# Constants
from .constants import (
    PRESET_TYPES,
    STORE_BOOL_OPTIONS,
    STORE_FLAG_OPTIONS,
    STORE_VALUE_OPTIONS,
)

# Helpers (public API)
from .helpers import MA2_SPECIAL_CHARS, quote_name

# Function Keywords
from .functions import (
    # Helping Keywords (Plus +, Minus -, And, If)
    add_to_selection,
    add_user_var,
    add_var,
    # Appearance Function Keyword
    appearance,
    # Assign Function Keyword
    assign,
    assign_delay,
    assign_fade,
    assign_function,
    assign_property,
    assign_to_layout,
    # Blackout
    blackout,
    # Import/Export Function Keywords
    export_object,
    import_object,
    import_fixture_type_cmd,
    import_layer_cmd,
    # At Function Keyword
    at,
    at_full,
    at_relative,
    at_zero,
    attribute_at,
    # Call Function Keywords
    call,
    # Other Function Keywords
    call_preset,
    # Navigation Function Keywords
    changedest,
    channel_at,
    clear,
    clear_active,
    clear_all,
    clear_selection,
    condition_and,
    # Copy Function Keyword
    copy,
    copy_cue,
    # Cut Function Keyword
    cut,
    def_go_back,
    def_go_forward,
    def_go_pause,
    # Delete Function Keyword
    delete,
    delete_cue,
    delete_fixture,
    delete_group,
    delete_messages,
    delete_preset,
    # Edit Function Keyword
    edit,
    empty,
    executor_at,
    fixture_at,
    flash_executor,
    get_user_var,
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
    group_at,
    blind,
    freeze,
    highlight,
    if_condition,
    # Info Function Keyword
    info,
    info_cue,
    info_group,
    info_preset,
    # Label Function Keyword
    label,
    label_group,
    label_preset,
    list_attribute,
    list_cue,
    list_effect_library,
    list_group,
    list_library,
    list_macro_library,
    list_messages,
    # List Function Keyword
    list_objects,
    list_oops,
    list_preset,
    list_shows,
    oops,
    list_user_var,
    list_var,
    load_show,
    # Macro Placeholder
    macro_with_input_after,
    macro_with_input_before,
    # Move Function Keyword
    move,
    delete_show,
    new_show,
    off_executor,
    on_executor,
    page_next,
    page_previous,
    # Park Function Keywords
    park,
    # Paste Function Keyword
    paste,
    pause_sequence,
    preset_type_at,
    release_executor,
    # Remove Function Keyword
    remove,
    remove_effect,
    remove_fixture,
    remove_from_selection,
    remove_preset_type,
    remove_selection,
    select_fixture,
    select_group,
    # Variable Function Keywords
    set_user_var,
    set_var,
    save_show,
    solo,
    solo_executor,
    store,
    store_cue,
    store_cue_timed,
    store_group,
    store_matricks,
    store_preset,
    temp_fader,
    unpark,
    update,
    update_cue,
)

# Object Keywords
from .objects import (
    attribute,
    channel,
    cue,
    cue_part,
    dmx,
    dmx_universe,
    executor,
    feature,
    fixture,
    group,
    layout,
    preset,
    preset_type,
    sequence,
    timecode,
    timecode_slot,
    timer,
)

__all__ = [
    # Constants
    "PRESET_TYPES",
    "STORE_FLAG_OPTIONS",
    "STORE_BOOL_OPTIONS",
    "STORE_VALUE_OPTIONS",
    # Helpers (wildcard spec)
    "MA2_SPECIAL_CHARS",
    "quote_name",
    # Object Keywords
    "attribute",
    "feature",
    "fixture",
    "channel",
    "group",
    "layout",
    "preset",
    "preset_type",
    "cue",
    "cue_part",
    "sequence",
    "executor",
    "dmx",
    "dmx_universe",
    "timecode",
    "timecode_slot",
    "timer",
    # Blackout
    "blackout",
    # Import/Export Function Keywords
    "export_object",
    "import_object",
    "import_fixture_type_cmd",
    "import_layer_cmd",
    # Assign Function Keyword
    "assign",
    "assign_delay",
    "assign_property",
    "assign_fade",
    "assign_function",
    "assign_to_layout",
    "empty",
    "temp_fader",
    # Label Function Keyword
    "label",
    # Appearance Function Keyword
    "appearance",
    # At Function Keyword
    "at",
    "at_full",
    "at_zero",
    "attribute_at",
    "fixture_at",
    "channel_at",
    "group_at",
    "executor_at",
    "preset_type_at",
    # Edit Function Keyword
    "edit",
    # Cut Function Keyword
    "cut",
    # Paste Function Keyword
    "paste",
    # Copy Function Keyword
    "copy",
    "copy_cue",
    # Move Function Keyword
    "move",
    # Macro Placeholder (@ Character)
    "macro_with_input_after",
    "macro_with_input_before",
    # Other Function Keywords
    "store",
    "store_cue",
    "store_group",
    "store_matricks",
    "store_preset",
    "select_fixture",
    "clear",
    "clear_selection",
    "clear_active",
    "clear_all",
    "label_group",
    "label_preset",
    # Delete Function Keyword
    "delete",
    "delete_cue",
    "delete_fixture",
    "delete_group",
    "delete_messages",
    "delete_preset",
    # Remove Function Keyword
    "remove",
    "remove_effect",
    "remove_fixture",
    "remove_preset_type",
    "remove_selection",
    # List Function Keyword
    "list_objects",
    "list_attribute",
    "list_cue",
    "list_group",
    "list_messages",
    "list_preset",
    # List* (specialized)
    "list_shows",
    "list_oops",
    "list_library",
    "list_effect_library",
    "list_macro_library",
    # Info Function Keyword
    "info",
    "info_cue",
    "info_group",
    "info_preset",
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
    # GoFast (<<< and >>>)
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
    # Blind / Freeze
    "blind",
    "freeze",
    # Highlight
    "highlight",
    # Timecode goto
    "goto_timecode",
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
    "save_show",
    "delete_show",
    # Navigation Function Keywords
    "changedest",
    # Store / Update
    "store_cue_timed",
    "update",
    "update_cue",
    # Oops (undo)
    "oops",
    # Backward Compatibility Aliases
    "select_group",
    "call_preset",
]
