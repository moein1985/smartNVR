#!/usr/bin/env bash
#
# build_tarballs.sh — Build obfuscated Docker image and generate tarball
#
# This script:
#   1. Builds the obfuscated backend Docker image using Dockerfile.obfuscated
#   2. Saves it as a .tar tarball for air-gapped deployment
#   3. Verifies the image contains no raw .py source files
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"
BACKEND_DIR="$ROOT_DIR/frigate-intelligence"
OUTPUT_DIR="$ROOT_DIR/frigate-intelligence/data/updates"

IMAGE_NAME="frigate-intelligence"
IMAGE_TAG="obfuscated"
TARBALL_NAME="frigate-intelligence-latest.tar"

echo "=== Tarball Generation Pipeline ==="
echo ""

# ─── Step 1: Build obfuscated Docker image ───
echo "[1/4] Building obfuscated Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
docker build \
    -f "$BACKEND_DIR/Dockerfile.obfuscated" \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    "$BACKEND_DIR"

echo "[1/4] Image built successfully."
echo ""

# ─── Step 2: Verify no raw .py files in the image ───
echo "[2/4] Verifying no raw .py files in final image..."
RAW_COUNT=$(docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" \
    find /app/src -name "*.py" 2>/dev/null | wc -l)

if [ "$RAW_COUNT" -gt 0 ]; then
    echo "FATAL: $RAW_COUNT raw .py files found in production image!"
    docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" find /app/src -name "*.py"
    exit 1
fi
echo "[2/4] OK: No raw .py files in image."
echo ""

# ─── Step 3: Create output directory ───
echo "[3/4] Preparing output directory..."
mkdir -p "$OUTPUT_DIR"
echo "[3/4] Output: $OUTPUT_DIR/$TARBALL_NAME"
echo ""

# ─── Step 4: Save image as tarball ───
echo "[4/4] Saving Docker image as tarball..."
docker save -o "$OUTPUT_DIR/$TARBALL_NAME" "${IMAGE_NAME}:${IMAGE_TAG}"

TARBALL_SIZE=$(du -h "$OUTPUT_DIR/$TARBALL_NAME" | cut -f1)
echo "[4/4] Tarball saved: $OUTPUT_DIR/$TARBALL_NAME ($TARBALL_SIZE)"
echo ""

echo "=== Tarball Generation Complete ==="
echo "  Image:    ${IMAGE_NAME}:${IMAGE_TAG}"
echo "  Tarball:  $OUTPUT_DIR/$TARBALL_NAME"
echo "  Size:     $TARBALL_SIZE"
