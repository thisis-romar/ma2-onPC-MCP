# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
Advanced Timing Function Keywords for grandMA2 Command Builder

Covers cue fade curves and chaser step timing that are not covered by the
basic assign_fade / assign_delay builders:

- fade_path: Set the fade curve shape (FadePath keyword)
- out_fade: Set out-fade time for a cue (OutFade keyword)
- out_delay: Set out-delay time for a cue (OutDelay keyword)
- step_fade: Set the crossfade time between chaser steps (StepFade keyword)
- step_in_fade: Set the in-fade time for chaser steps (StepInFade keyword)
- step_out_fade: Set the out-fade time for chaser steps (StepOutFade keyword)
"""

# ============================================================================
# FADE PATH (CURVE SHAPE)
# ============================================================================

_VALID_FADE_PATHS = frozenset({
    "linear",
    "easeIn",
    "easeOut",
    "easeInOut",
    "step",
    "brokenLine",
})


def fade_path(path_type: str) -> str:
    """
    Construct a FadePath command to set the fade curve shape.

    The fade path controls how the attribute value changes over the fade
    duration — linear ramp, ease in/out, step change, or broken line.

    Args:
        path_type: Curve shape — one of: linear, easeIn, easeOut,
            easeInOut, step, brokenLine. Case-sensitive.

    Returns:
        str: MA command string

    Raises:
        ValueError: If path_type is not a recognised MA2 fade path.

    Examples:
        >>> fade_path("linear")
        'FadePath linear'
        >>> fade_path("easeInOut")
        'FadePath easeInOut'
        >>> fade_path("step")
        'FadePath step'
    """
    if path_type not in _VALID_FADE_PATHS:
        raise ValueError(
            f"Unknown fade path {path_type!r}. "
            f"Valid: {sorted(_VALID_FADE_PATHS)}"
        )
    return f"FadePath {path_type}"


# ============================================================================
# OUT FADE / OUT DELAY
# ============================================================================


def out_fade(
    value: float | int,
    cue_id: int | None = None,
    sequence_id: int | None = None,
) -> str:
    """
    Construct an OutFade command to set the out-fade time for a cue.

    The out-fade time controls how long attributes take to fade out when
    the cue is released or superseded by a higher-priority playback.

    When cue_id and sequence_id are provided the command is scoped to
    that specific cue in that sequence. When omitted it applies to the
    currently selected cue in the programmer.

    Args:
        value: Out-fade time in seconds (e.g. 2.5).
        cue_id: Cue number (optional).
        sequence_id: Sequence number (optional, only used when cue_id given).

    Returns:
        str: MA command string

    Examples:
        >>> out_fade(2.5)
        'OutFade 2.5'
        >>> out_fade(3, cue_id=5)
        'OutFade 3 Cue 5'
        >>> out_fade(1.5, cue_id=5, sequence_id=99)
        'OutFade 1.5 Cue 5 Sequence 99'
    """
    cmd = f"OutFade {value}"
    if cue_id is not None:
        cmd += f" Cue {cue_id}"
        if sequence_id is not None:
            cmd += f" Sequence {sequence_id}"
    return cmd


def out_delay(
    value: float | int,
    cue_id: int | None = None,
    sequence_id: int | None = None,
) -> str:
    """
    Construct an OutDelay command to set the out-delay time for a cue.

    The out-delay time is how long the console waits before starting the
    out-fade when a cue is released or superseded.

    Args:
        value: Out-delay time in seconds (e.g. 1.0).
        cue_id: Cue number (optional).
        sequence_id: Sequence number (optional, only used when cue_id given).

    Returns:
        str: MA command string

    Examples:
        >>> out_delay(1.0)
        'OutDelay 1.0'
        >>> out_delay(0.5, cue_id=3)
        'OutDelay 0.5 Cue 3'
        >>> out_delay(2, cue_id=3, sequence_id=10)
        'OutDelay 2 Cue 3 Sequence 10'
    """
    cmd = f"OutDelay {value}"
    if cue_id is not None:
        cmd += f" Cue {cue_id}"
        if sequence_id is not None:
            cmd += f" Sequence {sequence_id}"
    return cmd


# ============================================================================
# CHASER STEP FADE KEYWORDS
# ============================================================================


def step_fade(value: float | int) -> str:
    """
    Construct a StepFade command to set the crossfade time between chaser steps.

    StepFade sets how long the chaser takes to transition between consecutive
    steps. A value of 0 produces an instant snap; values > 0 produce a smooth
    crossfade of that duration in seconds.

    Args:
        value: Step crossfade time in seconds (e.g. 0.5).

    Returns:
        str: MA command string

    Examples:
        >>> step_fade(0.5)
        'StepFade 0.5'
        >>> step_fade(0)
        'StepFade 0'
    """
    return f"StepFade {value}"


def step_in_fade(value: float | int) -> str:
    """
    Construct a StepInFade command to set the in-fade time for chaser steps.

    StepInFade controls the individual in-fade time of each step — how long
    the step's attributes take to reach their target values as the step
    activates. This is independent of the overall chaser crossfade.

    Args:
        value: Step in-fade time in seconds.

    Returns:
        str: MA command string

    Examples:
        >>> step_in_fade(1.0)
        'StepInFade 1.0'
        >>> step_in_fade(0)
        'StepInFade 0'
    """
    return f"StepInFade {value}"


def step_out_fade(value: float | int) -> str:
    """
    Construct a StepOutFade command to set the out-fade time for chaser steps.

    StepOutFade controls the individual out-fade time of each step — how long
    the step's attributes take to fade away as the next step activates.
    This is independent of the overall chaser crossfade.

    Args:
        value: Step out-fade time in seconds.

    Returns:
        str: MA command string

    Examples:
        >>> step_out_fade(1.0)
        'StepOutFade 1.0'
        >>> step_out_fade(0)
        'StepOutFade 0'
    """
    return f"StepOutFade {value}"
