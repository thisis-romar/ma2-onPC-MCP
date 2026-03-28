"""
Macro Placeholder Function Keywords for grandMA2 Command Builder

The "@" character is used in macros as a placeholder for user input.
This is completely different from the "At" keyword.

- @ at the end: User input will come after the command
- @ at the beginning: User input will come before the command (CLI must be disabled)

Included functions:
- macro_with_input_after: Add user input placeholder at the end of command
- macro_with_input_before: Add user input placeholder at the beginning of command
"""


def macro_with_input_after(command: str) -> str:
    """
    Create a macro line with user input placeholder at the end.

    The @ at the end means the user will provide input after
    executing the macro.

    Args:
        command: The command prefix before user input

    Returns:
        str: Macro line with @ placeholder at the end

    Examples:
        >>> macro_with_input_after("Load")
        'Load @'
        >>> macro_with_input_after("Attribute Pan At")
        'Attribute Pan At @'
    """
    return f"{command} @"


def macro_with_input_before(command: str) -> str:
    """
    Create a macro line with user input placeholder at the beginning.

    The @ at the beginning means the user's previous command line
    input will be prepended. Note: CLI must be disabled for this to work.

    Args:
        command: The command suffix after user input

    Returns:
        str: Macro line with @ placeholder at the beginning

    Examples:
        >>> macro_with_input_before("Fade 20")
        '@ Fade 20'
    """
    return f"@ {command}"
