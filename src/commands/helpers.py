"""
Internal Helper Functions for grandMA2 Command Builder

This module contains internal helper functions used by the command builder.
These functions are not intended for external use.
"""

import logging
from typing import Any

from .constants import STORE_BOOL_OPTIONS, STORE_FLAG_OPTIONS, STORE_VALUE_OPTIONS

logger = logging.getLogger(__name__)


def _build_store_options(**kwargs: Any) -> str:
    """
    Build option string for store commands.

    Handles three types of options:
    1. Flag options (no value): /merge, /overwrite, /noconfirm
    2. Boolean options: /cueonly=true, /tracking=false
    3. Value options: /source=output, /screen=1

    Args:
        **kwargs: Option name-value pairs

    Returns:
        str: Formatted option string (e.g., " /merge /cueonly=true")
    """
    options_parts = []

    for key, value in kwargs.items():
        if value is None:
            continue

        # Normalize key (remove underscores, convert to lowercase)
        option_key = key.replace("_", "").lower()

        # Handle flag options (no value needed)
        if option_key in STORE_FLAG_OPTIONS:
            if value:  # Only add if True
                options_parts.append(f"/{option_key}")

        # Handle boolean options (need =true or =false)
        elif option_key in STORE_BOOL_OPTIONS:
            bool_value = "true" if value else "false"
            options_parts.append(f"/{option_key}={bool_value}")

        # Handle value options
        elif option_key in STORE_VALUE_OPTIONS:
            options_parts.append(f"/{option_key}={value}")

        else:
            logger.warning(
                f"Unknown store option '{key}' (normalized: '{option_key}') — "
                "this option will be ignored. Check for typos."
            )

    if options_parts:
        return " " + " ".join(options_parts)
    return ""

