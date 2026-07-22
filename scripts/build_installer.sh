#!/usr/bin/env bash
#
# build_installer.sh — Build the Makeself .run installer archive
#
# This script gathers all required artifacts and packages them into
# a self-extracting .run archive using Makeself.
#
# Prerequisites:
#   - makeself installed (apt install makeself / brew install makeself)
#   - Docker images built as tarballs (run build_tarballs.sh first)
#   - Flutter APK built (run frigate_app/scripts/build_release.sh first)
#
# Output:
#   dist/frigate-intelligence-installer-v{VERSION}.run
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"
VERSION="${VERSION:-1.0.0}"
STAGING_DIR="$ROOT_DIR/dist/installer-staging"
OUTPUT_DIR="$ROOT_DIR/dist"
ARCHIVE_NAME="frigate-intelligence-installer-v${VERSION}.run"

log() { echo "[build_installer] $*"; }
fail() { echo "[build_installer] ERROR: $*" >&2; exit 1; }

echo "=== Frigate Intelligence Installer Builder ==="
echo "  Version:    $VERSION"
echo "  Staging:    $STAGING_DIR"
echo "  Output:     $OUTPUT_DIR/$ARCHIVE_NAME"
echo ""

# ─── Step 1: Clean and create staging directory ───
log "[1/6] Preparing staging directory..."
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR/images"
mkdir -p "$STAGING_DIR/docker-offline-packages"
mkdir -p "$STAGING_DIR/compose"
echo ""

# ─── Step 2: Copy Docker image tarballs ───
log "[2/6] Gathering Docker image tarballs..."
TARBALL_SRC="$ROOT_DIR/frigate-intelligence/data/updates"
if [ -d "$TARBALL_SRC" ] && ls "$TARBALL_SRC"/*.tar 1>/dev/null 2>&1; then
    cp "$TARBALL_SRC"/*.tar "$STAGING_DIR/images/"
    TARBALL_COUNT=$(find "$STAGING_DIR/images" -name "*.tar" | wc -l)
    log "  Copied $TARBALL_COUNT tarball(s)."
else
    log "  WARNING: No tarballs found in $TARBALL_SRC"
    log "           Run scripts/build_tarballs.sh first."
    fail "No Docker image tarballs found."
fi
echo ""

# ─── Step 3: Copy compose files ───
log "[3/6] Gathering Docker Compose files..."
COMPOSE_SRC="$ROOT_DIR/frigate-intelligence"
if [ -f "$COMPOSE_SRC/docker-compose.yml" ]; then
    cp "$COMPOSE_SRC/docker-compose.yml" "$STAGING_DIR/compose/"
    log "  Copied docker-compose.yml"
else
    fail "docker-compose.yml not found in $COMPOSE_SRC"
fi
echo ""

# ─── Step 4: Copy installation scripts ───
log "[4/6] Gathering installation scripts..."
cp "$SCRIPT_DIR/install.sh" "$STAGING_DIR/"
cp "$SCRIPT_DIR/verify_hardware.sh" "$STAGING_DIR/"
cp "$SCRIPT_DIR/license_generator.py" "$STAGING_DIR/"

# Copy the compose file to staging root as well (install.sh expects it)
cp "$STAGING_DIR/compose/docker-compose.yml" "$STAGING_DIR/docker-compose.yml"

chmod +x "$STAGING_DIR/install.sh" "$STAGING_DIR/verify_hardware.sh"
log "  Copied install.sh, verify_hardware.sh, license_generator.py"
echo ""

# ─── Step 5: Copy Flutter APK (optional) ───
log "[5/6] Gathering Flutter APK..."
APK_SRC="$ROOT_DIR/frigate_app/build/app/outputs/flutter-apk/app-release.apk"
if [ -f "$APK_SRC" ]; then
    mkdir -p "$STAGING_DIR/apk"
    cp "$APK_SRC" "$STAGING_DIR/apk/frigate-intelligence-v${VERSION}.apk"
    log "  Copied release APK."
else
    log "  WARNING: No APK found — installer will not include the mobile app."
    log "           Run frigate_app/scripts/build_release.sh first."
fi
echo ""

# ─── Step 6: Build Makeself archive ───
log "[6/6] Building Makeself .run archive..."
mkdir -p "$OUTPUT_DIR"

if ! command -v makeself &>/dev/null; then
    log "  makeself not found — staging directory is ready at:"
    log "    $STAGING_DIR"
    log ""
    log "  To create the .run archive, install makeself and run:"
    log "    makeself $STAGING_DIR $OUTPUT_DIR/$ARCHIVE_NAME \\"
    log "      \"Frigate Intelligence Installer v$VERSION\" \\"
    log "      ./install.sh"
    log ""
    log "  Or on Debian/Ubuntu: sudo apt install makeself"
    log "  Or on macOS: brew install makeself"
    fail "makeself not installed."
fi

makeself "$STAGING_DIR" "$OUTPUT_DIR/$ARCHIVE_NAME" \
    "Frigate Intelligence Installer v${VERSION}" \
    ./install.sh

ARCHIVE_SIZE=$(du -h "$OUTPUT_DIR/$ARCHIVE_NAME" | cut -f1)
echo ""
echo "=== Installer Build Complete ==="
echo "  Archive:  $OUTPUT_DIR/$ARCHIVE_NAME"
echo "  Size:     $ARCHIVE_SIZE"
echo ""
echo "  To deploy on the target server:"
echo "    1. Copy $ARCHIVE_NAME to the server"
echo "    2. Generate a license: python license_generator.py --mac <MAC> --salt <SALT> -o license.lic"
echo "    3. Run: ./$ARCHIVE_NAME"
echo ""
echo "  The archive is self-extracting and will run install.sh automatically."
