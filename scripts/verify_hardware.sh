#!/usr/bin/env bash
#
# verify_hardware.sh — Verify that the current machine's MAC address
# matches the license file. Exits with error if mismatch.
#
# Usage: ./verify_hardware.sh --salt "my-secret-salt" [--license license.lic]
#
set -euo pipefail

LICENSE_FILE="${LICENSE_FILE:-license.lic}"
SALT="${LICENSE_SALT:-}"

# ─── Parse arguments ───
while [[ $# -gt 0 ]]; do
    case "$1" in
        --salt)
            SALT="$2"
            shift 2
            ;;
        --license)
            LICENSE_FILE="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            exit 2
            ;;
    esac
done

if [ -z "$SALT" ]; then
    echo "ERROR: --salt is required (or set LICENSE_SALT env var)"
    exit 2
fi

if [ ! -f "$LICENSE_FILE" ]; then
    echo "ERROR: License file not found: $LICENSE_FILE"
    exit 2
fi

# ─── Detect the primary MAC address ───
# Strategy: Get the MAC of the first non-loopback, non-virtual interface
get_primary_mac() {
    local mac=""

    # Try ip command (modern Linux)
    if command -v ip &>/dev/null; then
        mac=$(ip -o link show | \
              grep -v 'lo\|docker\|br-\|veth\|virbr' | \
              awk '{print $2, $17}' | \
              head -1 | awk '{print $2}')
    fi

    # Fallback: try ifconfig (older systems)
    if [ -z "$mac" ] && command -v ifconfig &>/dev/null; then
        mac=$(ifconfig 2>/dev/null | \
              grep -A1 'eth0\|enp\|ens\|enx' | \
              grep -oE '([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}' | \
              head -1)
    fi

    # Fallback: read from /sys/class/net
    if [ -z "$mac" ]; then
        for iface in /sys/class/net/*; do
            iface_name=$(basename "$iface")
            if [ "$iface_name" != "lo" ] && \
               [ "$iface_name" != "docker0" ] && \
               [[ ! "$iface_name" =~ ^br- ]] && \
               [[ ! "$iface_name" =~ ^veth ]]; then
                mac=$(cat "$iface/address" 2>/dev/null || true)
                if [ -n "$mac" ]; then
                    break
                fi
            fi
        done
    fi

    if [ -z "$mac" ]; then
        echo "ERROR: Could not detect MAC address"
        return 1
    fi

    # Normalize to lowercase
    echo "$mac" | tr '[:upper:]' '[:lower:]'
}

# ─── Compute SHA-256 hash ───
compute_hash() {
    local mac="$1"
    local salt="$2"
    echo -n "${mac}:${salt}" | sha256sum | awk '{print $1}'
}

# ─── Main verification ───
echo "=== Hardware License Verification ==="

CURRENT_MAC=$(get_primary_mac) || exit 1
echo "  Detected MAC: $CURRENT_MAC"

COMPUTED_HASH=$(compute_hash "$CURRENT_MAC" "$SALT")
LICENSED_HASH=$(cat "$LICENSE_FILE" | tr -d '[:space:]')

echo "  Computed hash: ${COMPUTED_HASH:0:16}..."
echo "  Licensed hash: ${LICENSED_HASH:0:16}..."

if [ "$COMPUTED_HASH" = "$LICENSED_HASH" ]; then
    echo "  ✅ Hardware verified — license matches."
    exit 0
else
    echo "  ❌ HARDWARE MISMATCH — license does not match this machine!"
    echo "  This software is not licensed for this hardware."
    exit 1
fi
