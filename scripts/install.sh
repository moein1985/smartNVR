#!/usr/bin/env bash
#
# install.sh — One-click air-gapped installer for Frigate Intelligence
#
# Flow:
#   1. Verify hardware license
#   2. Detect prerequisites (Docker, NVIDIA, docker compose)
#   3. Load Docker images from tarballs
#   4. Create frigate_default network
#   5. docker compose up -d
#   6. Health check
#   7. Print success message with access URLs
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── Configuration ───
LICENSE_FILE="${LICENSE_FILE:-$SCRIPT_DIR/license.lic}"
LICENSE_SALT="${LICENSE_SALT:-frigate-intelligence-2026}"
COMPOSE_FILE="${COMPOSE_FILE:-$SCRIPT_DIR/docker-compose.yml}"
IMAGES_DIR="${IMAGES_DIR:-$SCRIPT_DIR/images}"
PACKAGES_DIR="${PACKAGES_DIR:-$SCRIPT_DIR/docker-offline-packages}"
HEALTH_URL="${HEALTH_URL:-http://localhost:8088/api/v1/health}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-60}"

# ─── Helper functions ───
log()   { echo "[install] $*"; }
fail()  { echo "[install] ERROR: $*" >&2; exit 1; }
ok()    { echo "[install] ✅ $*"; }

# ─── Step 1: Hardware License Verification ───
log "=== Step 1/7: Hardware License Verification ==="
if [ -f "$LICENSE_FILE" ]; then
    bash "$SCRIPT_DIR/verify_hardware.sh" --salt "$LICENSE_SALT" --license "$LICENSE_FILE" \
        || fail "Hardware verification failed. This software is not licensed for this machine."
    ok "Hardware license verified."
else
    log "WARNING: No license file found at $LICENSE_FILE — skipping verification."
    log "         This is only acceptable for development environments."
fi
echo ""

# ─── Step 2: Prerequisite Detection ───
log "=== Step 2/7: Prerequisite Detection ==="

# Docker
if command -v docker &>/dev/null; then
    DOCKER_VERSION=$(docker --version)
    ok "Docker found: $DOCKER_VERSION"
else
    log "Docker not found. Attempting offline installation..."
    if [ -d "$PACKAGES_DIR" ]; then
        # ─── Offline Docker installation (stub) ───
        # On Debian/Ubuntu:
        #   sudo dpkg -i "$PACKAGES_DIR"/docker-ce*.deb
        #   sudo dpkg -i "$PACKAGES_DIR"/docker-ce-cli*.deb
        #   sudo dpkg -i "$PACKAGES_DIR"/containerd.io*.deb
        # On RHEL/CentOS:
        #   sudo rpm -ivh "$PACKAGES_DIR"/docker-ce*.rpm
        #   sudo rpm -ivh "$PACKAGES_DIR"/containerd.io*.rpm
        log "  Offline packages found in: $PACKAGES_DIR"
        log "  Run: sudo dpkg -i $PACKAGES_DIR/docker-ce*.deb  (Debian/Ubuntu)"
        log "  Run: sudo rpm -ivh $PACKAGES_DIR/docker-ce*.rpm  (RHEL/CentOS)"
        fail "Please install Docker from offline packages and re-run this script."
    else
        fail "Docker not found and no offline packages directory at $PACKAGES_DIR"
    fi
fi

# Docker Compose
if docker compose version &>/dev/null 2>&1; then
    ok "Docker Compose (plugin) found."
elif command -v docker-compose &>/dev/null; then
    ok "Docker Compose (standalone) found."
    fail "Standalone docker-compose detected — please use the docker compose plugin."
else
    fail "Docker Compose not found. Install docker-compose-plugin from offline packages."
fi

# NVIDIA Container Toolkit (optional, for GPU support)
if command -v nvidia-smi &>/dev/null; then
    ok "NVIDIA GPU detected: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
    if docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi &>/dev/null 2>&1; then
        ok "NVIDIA Container Toolkit working."
    else
        log "WARNING: NVIDIA Container Toolkit not configured."
        log "         GPU features will be unavailable."
        log "         Install nvidia-container-toolkit from offline packages."
    fi
else
    log "No NVIDIA GPU detected — CPU-only mode."
fi
echo ""

# ─── Step 3: Load Docker Images ───
log "=== Step 3/7: Loading Docker Images ==="
if [ -d "$IMAGES_DIR" ]; then
    TAR_COUNT=$(find "$IMAGES_DIR" -name "*.tar" | wc -l)
    log "Found $TAR_COUNT image tarball(s) in $IMAGES_DIR"
    for tarball in "$IMAGES_DIR"/*.tar; do
        if [ -f "$tarball" ]; then
            log "  Loading: $(basename "$tarball")..."
            docker load -i "$tarball"
            ok "  Loaded: $(basename "$tarball")"
        fi
    done
else
    fail "Images directory not found: $IMAGES_DIR"
fi
echo ""

# ─── Step 4: Create Docker Network ───
log "=== Step 4/7: Creating Docker Network ==="
if docker network inspect frigate_default &>/dev/null 2>&1; then
    ok "Network 'frigate_default' already exists."
else
    docker network create frigate_default
    ok "Network 'frigate_default' created."
fi
echo ""

# ─── Step 5: Docker Compose Up ───
log "=== Step 5/7: Starting Services ==="
if [ -f "$COMPOSE_FILE" ]; then
    docker compose -f "$COMPOSE_FILE" up -d
    ok "Services started."
else
    fail "Compose file not found: $COMPOSE_FILE"
fi
echo ""

# ─── Step 6: Health Check ───
log "=== Step 6/7: Health Check ==="
log "Waiting for services to become healthy (timeout: ${HEALTH_TIMEOUT}s)..."
HEALTH_OK=false
for i in $(seq 1 "$HEALTH_TIMEOUT"); do
    if curl -sf "$HEALTH_URL" &>/dev/null; then
        HEALTH_OK=true
        break
    fi
    sleep 1
    printf "."
done
echo ""

if [ "$HEALTH_OK" = true ]; then
    ok "Health check passed — service is responding."
else
    fail "Health check failed — service did not respond within ${HEALTH_TIMEOUT}s."
fi
echo ""

# ─── Step 7: Success Message ───
log "=== Step 7/7: Installation Complete ==="
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  🎉 Frigate Intelligence installed successfully!            ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║  Access URLs:                                                ║"
echo "║    • Backend API:  http://localhost:8088                     ║"
echo "║    • Frigate NVR:  http://localhost:5000                     ║"
echo "║    • Web Panel:    http://localhost:3000                     ║"
echo "║                                                              ║"
echo "║  Next steps:                                                 ║"
echo "║    1. Install the Flutter app on your device                 ║"
echo "║    2. Point the app to this server's IP address              ║"
echo "║    3. Configure cameras via Frigate web UI                   ║"
echo "║                                                              ║"
echo "║  Logs:       docker compose -f $COMPOSE_FILE logs -f       ║"
echo "║  Stop:       docker compose -f $COMPOSE_FILE down           ║"
echo "║  Restart:    docker compose -f $COMPOSE_FILE restart        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
