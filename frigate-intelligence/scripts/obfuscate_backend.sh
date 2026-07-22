#!/usr/bin/env bash
#
# obfuscate_backend.sh — Obfuscate Python source code for IP protection.
#
# Primary strategy: PyArmor (if available and licensed)
# Fallback strategy:  compileall + delete raw .py files
#
set -euo pipefail

SRC_DIR="${1:-src}"
DIST_DIR="${2:-dist}"

echo "=== Backend Obfuscation ==="
echo "Source:  $SRC_DIR"
echo "Output:  $DIST_DIR"
echo ""

# ─── Strategy 1: PyArmor ───
if command -v pyarmor &>/dev/null; then
    echo "[pyarmor] Found — attempting obfuscation..."
    if pyarmor gen -O "$DIST_DIR" "$SRC_DIR"; then
        echo "[pyarmor] Obfuscation successful."
        echo "[pyarmor] Obfuscated output in: $DIST_DIR"

        # Verify: ensure no .py files in dist/ (pyarmor outputs .pyc or encrypted .py)
        RAW_COUNT=$(find "$DIST_DIR" -name "*.py" -not -name "__init__.py" | wc -l)
        if [ "$RAW_COUNT" -gt 0 ]; then
            echo "[pyarmor] WARNING: $RAW_COUNT raw .py files found in dist/ — reviewing..."
        fi
        echo "=== Obfuscation complete (PyArmor) ==="
        exit 0
    else
        echo "[pyarmor] Failed — falling back to compileall strategy."
    fi
else
    echo "[pyarmor] Not installed — using compileall fallback."
fi

# ─── Strategy 2: compileall fallback ───
echo "[compileall] Compiling all .py files to .pyc..."
mkdir -p "$DIST_DIR"

# Copy the source tree to dist/
cp -r "$SRC_DIR" "$DIST_DIR/"

# Compile all Python files to bytecode
PYTHON_BIN="python3"
if ! command -v python3 &>/dev/null; then
    PYTHON_BIN="python"
fi
echo "[compileall] Using: $PYTHON_BIN"
$PYTHON_BIN -m compileall -q "$DIST_DIR"

# Remove all raw .py files (keep __pycache__ with .pyc files)
echo "[compileall] Removing raw .py files..."
find "$DIST_DIR" -name "*.py" -delete

# Verify no .py files remain
RAW_COUNT=$(find "$DIST_DIR" -name "*.py" | wc -l)
if [ "$RAW_COUNT" -gt 0 ]; then
    echo "[compileall] ERROR: $RAW_COUNT .py files still present!"
    exit 1
fi

echo "[compileall] Obfuscation complete. .pyc files in: $DIST_DIR"
echo "=== Obfuscation complete (compileall) ==="
