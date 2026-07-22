#!/usr/bin/env python3
"""
license_generator.py — Generate SHA-256 hardware-locked license files.

Usage:
    python license_generator.py --mac AA:BB:CC:DD:EE:FF --salt "my-secret-salt" --output license.lic
    python license_generator.py --mac aa:bb:cc:dd:ee:ff --salt "my-secret-salt"  # prints to stdout

The license hash is computed as:
    SHA-256(normalized_mac + ":" + salt)

The MAC address is normalized to lowercase with colon separators before hashing.
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path


def normalize_mac(mac: str) -> str:
    """Normalize a MAC address to lowercase AA:BB:CC:DD:EE:FF format."""
    # Remove all separators and whitespace, then rejoin with colons
    cleaned = re.sub(r"[\s:.-]", "", mac).lower()
    if len(cleaned) != 12:
        raise ValueError(
            f"Invalid MAC address: '{mac}' — expected 12 hex digits, got {len(cleaned)}"
        )
    if not re.match(r"^[0-9a-f]{12}$", cleaned):
        raise ValueError(f"Invalid MAC address: '{mac}' — contains non-hex characters")
    return ":".join(cleaned[i : i + 2] for i in range(0, 12, 2))


def generate_license_hash(mac: str, salt: str) -> str:
    """Generate a SHA-256 license hash from a MAC address and salt."""
    normalized = normalize_mac(mac)
    payload = f"{normalized}:{salt}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a hardware-locked license file from a MAC address."
    )
    parser.add_argument(
        "--mac",
        required=True,
        help="MAC address of the target machine (e.g., AA:BB:CC:DD:EE:FF)",
    )
    parser.add_argument(
        "--salt",
        required=True,
        help="Secret salt/key for license generation",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output file path (default: print to stdout)",
    )
    args = parser.parse_args()

    try:
        license_hash = generate_license_hash(args.mac, args.salt)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(license_hash + "\n", encoding="utf-8")
        print(f"License file written to: {output_path}")
        print(f"  MAC:   {normalize_mac(args.mac)}")
        print(f"  Hash:  {license_hash}")
    else:
        print(license_hash)

    return 0


if __name__ == "__main__":
    sys.exit(main())
