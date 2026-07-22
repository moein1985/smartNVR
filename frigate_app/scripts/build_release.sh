#!/usr/bin/env bash
#
# build_release.sh — Build obfuscated Flutter release APK
#
# Produces:
#   - build/app/releases/frigate-intelligence-release.apk (obfuscated)
#   - build/symbols/ (debug symbols for crash deobfuscation)
#
set -euo pipefail

echo "=== Flutter Release Build (Obfuscated) ==="

# Ensure we're in the frigate_app directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Clean previous builds
echo "[1/4] Cleaning previous builds..."
flutter clean

# Fetch dependencies
echo "[2/4] Fetching dependencies..."
flutter pub get

# Build obfuscated release APK with split debug info
echo "[3/4] Building obfuscated release APK..."
flutter build apk --release --obfuscate --split-debug-info=./build/symbols

# Verify output
APK_PATH="build/app/outputs/flutter-apk/app-release.apk"
if [ -f "$APK_PATH" ]; then
    echo "[4/4] APK built successfully: $APK_PATH"
    APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
    echo "  Size: $APK_SIZE"
    echo "  Debug symbols: $(ls -la build/symbols/ 2>/dev/null | wc -l) files"
else
    echo "ERROR: APK not found at $APK_PATH"
    exit 1
fi

echo ""
echo "=== Flutter Release Build Complete ==="
echo "  APK:    $APK_PATH"
echo "  Symbols: build/symbols/"
echo ""
echo "IMPORTANT: Store build/symbols/ securely. Without these,"
echo "crash stack traces cannot be deobfuscated."
