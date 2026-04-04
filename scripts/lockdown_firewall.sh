#!/usr/bin/env bash
# scripts/lockdown_firewall.sh
# Host-firewall rules that restrict grandMA2 Telnet (TCP 30000) to loopback
# while preserving MA-Net2 multicast traffic on the LAN interface.
#
# This makes the MCP server the sole gateway to the console's Telnet port.
# All external access must go through the MCP layer's OAuth/rights/license
# enforcement.
#
# Usage:
#   sudo bash scripts/lockdown_firewall.sh [--apply | --remove | --status]
#
# Requires: iptables (Linux) or Windows Firewall (via netsh).
# Idempotent — safe to run multiple times.

set -euo pipefail

TELNET_PORT="${GMA_TELNET_PORT:-30000}"
CHAIN_NAME="GMA2_LOCKDOWN"

# ── Helpers ──────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Usage: sudo bash $0 [--apply | --remove | --status]

  --apply    Create firewall rules restricting TCP $TELNET_PORT to loopback
  --remove   Remove all rules created by this script
  --status   Show current rule state

Environment:
  GMA_TELNET_PORT   Override Telnet port (default: 30000)

What this does:
  1. ACCEPT TCP $TELNET_PORT from 127.0.0.1 (loopback — MCP server)
  2. DROP   TCP $TELNET_PORT from all other sources
  3. ACCEPT MA-Net2 multicast (UDP 6454 Art-Net, UDP 5568 sACN) — untouched

What this does NOT do:
  - Block MA-Net2 session traffic (UDP multicast, different ports)
  - Affect outbound connections from this machine
  - Persist across reboots (use iptables-save/iptables-restore for that)
EOF
    exit 1
}

require_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "[error] This script must be run as root (sudo)." >&2
        exit 1
    fi
}

# ── Platform detection ───────────────────────────────────────────────

detect_platform() {
    if command -v iptables &>/dev/null; then
        echo "linux"
    elif command -v netsh &>/dev/null; then
        echo "windows"
    else
        echo "[error] Neither iptables nor netsh found. Cannot configure firewall." >&2
        exit 1
    fi
}

# ── Linux (iptables) ────────────────────────────────────────────────

linux_chain_exists() {
    iptables -L "$CHAIN_NAME" -n &>/dev/null 2>&1
}

linux_apply() {
    require_root

    if linux_chain_exists; then
        echo "[info] Chain $CHAIN_NAME already exists — removing before re-applying."
        linux_remove
    fi

    echo "[apply] Creating iptables chain: $CHAIN_NAME"
    iptables -N "$CHAIN_NAME"

    # Rule 1: Accept loopback traffic to Telnet port
    iptables -A "$CHAIN_NAME" -p tcp --dport "$TELNET_PORT" -s 127.0.0.1 -j ACCEPT
    iptables -A "$CHAIN_NAME" -p tcp --dport "$TELNET_PORT" -s ::1 -j ACCEPT 2>/dev/null || true

    # Rule 2: Drop everything else to Telnet port
    iptables -A "$CHAIN_NAME" -p tcp --dport "$TELNET_PORT" -j DROP

    # Rule 3: Return for all other traffic (no effect on MA-Net2, etc.)
    iptables -A "$CHAIN_NAME" -j RETURN

    # Insert chain jump at top of INPUT
    iptables -I INPUT 1 -j "$CHAIN_NAME"

    echo "[apply] Done. TCP $TELNET_PORT restricted to loopback."
    echo "[apply] MA-Net2 multicast (UDP 6454/5568) is unaffected."
    echo ""
    echo "[note] These rules do NOT persist across reboots."
    echo "       To persist: iptables-save > /etc/iptables/rules.v4"
}

linux_remove() {
    require_root

    if ! linux_chain_exists; then
        echo "[info] Chain $CHAIN_NAME does not exist — nothing to remove."
        return
    fi

    echo "[remove] Removing iptables chain: $CHAIN_NAME"

    # Remove jump from INPUT
    while iptables -D INPUT -j "$CHAIN_NAME" 2>/dev/null; do :; done

    # Flush and delete chain
    iptables -F "$CHAIN_NAME"
    iptables -X "$CHAIN_NAME"

    echo "[remove] Done. TCP $TELNET_PORT is no longer restricted."
}

linux_status() {
    if linux_chain_exists; then
        echo "[status] Chain $CHAIN_NAME exists. Rules:"
        iptables -L "$CHAIN_NAME" -n -v --line-numbers
        echo ""
        echo "[status] INPUT chain references:"
        iptables -L INPUT -n -v --line-numbers | grep "$CHAIN_NAME" || echo "  (none)"
    else
        echo "[status] Chain $CHAIN_NAME does not exist. Telnet port is unrestricted."
    fi
}

# ── Windows (netsh) ─────────────────────────────────────────────────

NETSH_RULE_BLOCK="GMA2-Lockdown-Block-Telnet"
NETSH_RULE_ALLOW="GMA2-Lockdown-Allow-Loopback"

windows_apply() {
    echo "[apply] Creating Windows Firewall rules for port $TELNET_PORT"

    # Remove existing rules first (idempotent)
    netsh advfirewall firewall delete rule name="$NETSH_RULE_BLOCK" 2>/dev/null || true
    netsh advfirewall firewall delete rule name="$NETSH_RULE_ALLOW" 2>/dev/null || true

    # Allow loopback
    netsh advfirewall firewall add rule name="$NETSH_RULE_ALLOW" \
        dir=in action=allow protocol=tcp localport="$TELNET_PORT" \
        remoteip=127.0.0.1 enable=yes

    # Block everything else
    netsh advfirewall firewall add rule name="$NETSH_RULE_BLOCK" \
        dir=in action=block protocol=tcp localport="$TELNET_PORT" \
        enable=yes

    echo "[apply] Done. TCP $TELNET_PORT restricted to loopback."
    echo "[apply] Windows Firewall rules persist across reboots."
}

windows_remove() {
    echo "[remove] Removing Windows Firewall rules"
    netsh advfirewall firewall delete rule name="$NETSH_RULE_BLOCK" 2>/dev/null || true
    netsh advfirewall firewall delete rule name="$NETSH_RULE_ALLOW" 2>/dev/null || true
    echo "[remove] Done."
}

windows_status() {
    echo "[status] Windows Firewall rules for GMA2-Lockdown:"
    netsh advfirewall firewall show rule name="$NETSH_RULE_ALLOW" 2>/dev/null || echo "  Allow rule: not found"
    netsh advfirewall firewall show rule name="$NETSH_RULE_BLOCK" 2>/dev/null || echo "  Block rule: not found"
}

# ── Dispatch ─────────────────────────────────────────────────────────

ACTION="${1:---status}"
PLATFORM="$(detect_platform)"

case "$ACTION" in
    --apply)
        case "$PLATFORM" in
            linux)   linux_apply   ;;
            windows) windows_apply ;;
        esac
        ;;
    --remove)
        case "$PLATFORM" in
            linux)   linux_remove   ;;
            windows) windows_remove ;;
        esac
        ;;
    --status)
        case "$PLATFORM" in
            linux)   linux_status   ;;
            windows) windows_status ;;
        esac
        ;;
    --help|-h)
        usage
        ;;
    *)
        echo "[error] Unknown option: $ACTION" >&2
        usage
        ;;
esac
