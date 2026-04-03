# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
Network / Session Function Keywords for grandMA2 Command Builder

Covers MA-Net2 session management and network configuration operations:
- join_session / leave_session / end_session: session lifecycle
- invite_station / disconnect_station: per-station session control
- take_control / drop_control: console master control handoff
- set_ip: NIC IP address assignment
- set_hostname: console hostname

All keywords belong to FunctionalDomain.NETWORK_SESSION in vocab.py.
Low urgency for single-console Telnet-only deployments; builders are
provided for completeness and multi-console script authoring.
"""


# ============================================================================
# SESSION LIFECYCLE
# ============================================================================


def join_session(session_name: str) -> str:
    """
    Construct a JoinSession command.

    Connects the console to an existing MA-Net2 session by name.

    Args:
        session_name: Name of the session to join (may contain spaces).

    Returns:
        str: MA command string

    Examples:
        >>> join_session("My Session")
        'JoinSession "My Session"'
        >>> join_session("Stage1")
        'JoinSession "Stage1"'
    """
    return f'JoinSession "{session_name}"'


def leave_session() -> str:
    """
    Construct a LeaveSession command.

    Disconnects the console from the current MA-Net2 session without
    ending it for other participants.

    Returns:
        str: MA command string

    Examples:
        >>> leave_session()
        'LeaveSession'
    """
    return "LeaveSession"


def end_session() -> str:
    """
    Construct an EndSession command.

    Terminates the current MA-Net2 session for all connected consoles.

    Returns:
        str: MA command string

    Examples:
        >>> end_session()
        'EndSession'
    """
    return "EndSession"


# ============================================================================
# PER-STATION CONTROL
# ============================================================================


def invite_station(station_id: int) -> str:
    """
    Construct an InviteStation command.

    Sends a join invitation to a station by its MA-Net2 numeric ID.

    Args:
        station_id: Numeric MA-Net2 station index (1-based).

    Returns:
        str: MA command string

    Examples:
        >>> invite_station(2)
        'InviteStation 2'
        >>> invite_station(5)
        'InviteStation 5'
    """
    return f"InviteStation {station_id}"


def disconnect_station(station_id: int) -> str:
    """
    Construct a DisconnectStation command.

    Forcibly removes a station from the MA-Net2 session by its numeric ID.

    Args:
        station_id: Numeric MA-Net2 station index (1-based).

    Returns:
        str: MA command string

    Examples:
        >>> disconnect_station(2)
        'DisconnectStation 2'
        >>> disconnect_station(3)
        'DisconnectStation 3'
    """
    return f"DisconnectStation {station_id}"


# ============================================================================
# MASTER CONTROL HANDOFF
# ============================================================================


def take_control() -> str:
    """
    Construct a TakeControl command.

    Claims the master role in the MA-Net2 session, giving this console
    priority for fader and executor output.

    Returns:
        str: MA command string

    Examples:
        >>> take_control()
        'TakeControl'
    """
    return "TakeControl"


def drop_control() -> str:
    """
    Construct a DropControl command.

    Releases the master role in the MA-Net2 session.

    Returns:
        str: MA command string

    Examples:
        >>> drop_control()
        'DropControl'
    """
    return "DropControl"


# ============================================================================
# NETWORK CONFIGURATION
# ============================================================================


def set_ip(interface: int, address: str) -> str:
    """
    Construct a SetIP command.

    Assigns an IP address to a console NIC. The console has up to two
    network interfaces (1 and 2). The address is quoted in the command.

    Args:
        interface: NIC index — 1 or 2 (dual-NIC consoles).
        address: IPv4 address in dotted-quad notation, e.g. "192.168.1.100".

    Returns:
        str: MA command string

    Examples:
        >>> set_ip(1, "192.168.1.100")
        'SetIP 1 "192.168.1.100"'
        >>> set_ip(2, "10.0.0.50")
        'SetIP 2 "10.0.0.50"'
    """
    return f'SetIP {interface} "{address}"'


def set_hostname(name: str) -> str:
    """
    Construct a SetHostname command.

    Assigns the MA-Net2 hostname for this console. The name is quoted
    to handle names that contain spaces.

    Args:
        name: Desired hostname string.

    Returns:
        str: MA command string

    Examples:
        >>> set_hostname("MyConsole")
        'SetHostname "MyConsole"'
        >>> set_hostname("FOH Console 1")
        'SetHostname "FOH Console 1"'
    """
    return f'SetHostname "{name}"'
