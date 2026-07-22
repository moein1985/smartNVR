# Customer Deployment Guide

## Frigate Intelligence — Air-Gapped Installation

This guide walks you through deploying Frigate Intelligence on a customer's
server without internet access.

---

## Prerequisites

### On the Build Machine (with internet)

1. **Docker** — for building obfuscated images
2. **Flutter SDK** — for building the release APK
3. **Makeself** — for creating the self-extracting installer
4. **Python 3.12+** — for license generation

### On the Target Server (air-gapped)

1. **Linux OS** — Ubuntu 22.04+ or RHEL 9+ recommended
2. **Docker Engine** — can be installed from offline packages
3. **Docker Compose plugin** — included in offline packages
4. **NVIDIA GPU** (optional) — for GPU-accelerated detection
5. **NVIDIA Container Toolkit** (optional) — for Docker GPU passthrough

---

## Build Process (on build machine)

### 1. Generate a Hardware License

Before deployment, obtain the MAC address of the target server's primary
network interface.

```bash
# On the target server, run:
ip link show | grep ether | head -1
# Example output: link/ether aa:bb:cc:dd:ee:ff

# On the build machine, generate the license:
cd scripts/
python license_generator.py \
    --mac aa:bb:cc:dd:ee:ff \
    --salt "your-secret-salt-here" \
    --output license.lic
```

**Keep the salt secret!** Anyone with the salt can generate licenses.

### 2. Build the Obfuscated Backend

```bash
# Build the obfuscated Docker image and save as tarball
./scripts/build_tarballs.sh
```

This produces `frigate-intelligence/data/updates/frigate-intelligence-latest.tar`.

### 3. Build the Flutter APK

```bash
cd frigate_app/
./scripts/build_release.sh
```

This produces an obfuscated APK and debug symbols in `build/symbols/`.
**Store the symbols securely** — see `docs/debug_symbol_storage_policy.md`.

### 4. Build the Installer Archive

```bash
# Install makeself if not already:
#   sudo apt install makeself  (Debian/Ubuntu)
#   brew install makeself      (macOS)

cd scripts/
./build_installer.sh
```

This produces `dist/frigate-intelligence-installer-v1.0.0.run`.

---

## Deployment Process (on target server)

### 1. Transfer Files

Copy the following to the target server via USB or local network:

```
frigate-intelligence-installer-v1.0.0.run    # The installer archive
license.lic                                   # The hardware license file
```

### 2. Run the Installer

```bash
# Make executable
chmod +x frigate-intelligence-installer-v1.0.0.run

# Set the license salt (must match what was used to generate the license)
export LICENSE_SALT="your-secret-salt-here"

# Run the installer
./frigate-intelligence-installer-v1.0.0.run
```

The installer will:
1. ✅ Verify the hardware license (MAC address match)
2. ✅ Check for Docker and NVIDIA prerequisites
3. ✅ Load Docker images from tarballs
4. ✅ Create the `frigate_default` Docker network
5. ✅ Start all services via `docker compose up -d`
6. ✅ Run a health check
7. ✅ Print access URLs

### 3. Access the System

| Service | URL |
|---------|-----|
| Backend API | `http://<server-ip>:8088` |
| Frigate NVR | `http://<server-ip>:5000` |
| Web Panel | `http://<server-ip>:3000` |

### 4. Install the Mobile App

Install the `frigate-intelligence-v1.0.0.apk` on your Android device.
Open the app and enter the server's IP address in Settings.

---

## Post-Installation

### Updating the System

To update the system with a new version:

1. Build a new tarball on the build machine
2. Transfer the `.tar` file to the server
3. Run the OTA update via the Flutter app's Settings → System Updates
4. Or manually: `docker load -i new-image.tar && docker compose restart`

### Managing Services

```bash
# View logs
docker compose -f docker-compose.yml logs -f

# Stop services
docker compose -f docker-compose.yml down

# Restart services
docker compose -f docker-compose.yml restart
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| License verification failed | Ensure `LICENSE_SALT` matches the build-time salt |
| Docker not found | Install from `docker-offline-packages/` directory |
| GPU not detected | Install `nvidia-container-toolkit` from offline packages |
| Health check timeout | Check logs: `docker compose logs -f` |
| Port already in use | Edit `docker-compose.yml` to change port mappings |

---

## Security Notes

- The installer archive contains **no raw Python source code** — all backend
  code is obfuscated (`.pyc` or PyArmor-encrypted).
- The Flutter APK is obfuscated with `--obfuscate --split-debug-info`.
- The hardware license binds the software to a specific MAC address.
- Debug symbols must be stored securely and never distributed to customers.
