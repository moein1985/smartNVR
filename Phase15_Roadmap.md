# Phase 15: Commercialization Roadmap

**Status:** In Progress  
**Started:** 2026-07-22

---

## Sub-Phase 15.1: Logging & OTA Update Pipeline (3–4 days)

- [x] Step 1: Create `infrastructure/logging_config.py` with `RotatingFileHandler`
- [x] Step 2: Replace `logging.basicConfig` in `fastapi_app.py` with `setup_logging()`
- [x] Step 3: Add `LOG_LEVEL` to `settings.py` and `.env`
- [x] Step 4: Add request logging middleware (correlation ID, response time)
- [ ] Step 5: Create `infrastructure/api/routes/system_routes.py` — log viewer endpoint
- [ ] Step 6: Create `update-agent` sidecar container with Docker socket access
- [ ] Step 7: Implement OTA upload endpoint + background update sequence
- [ ] Step 8: Implement rollback mechanism with health check
- [ ] Step 9: Add "System Updates" section to Flutter settings page
- [ ] Step 10: Tests: logging rotation, OTA upload, rollback scenario

---

## Sub-Phase 15.2: Backend Orchestrator (4–5 days)

- [ ] Step 1: Add `docker` PyPI package to `pyproject.toml`
- [ ] Step 2: Create `infrastructure/orchestrator/hardware_discovery.py`
- [ ] Step 3: Create `infrastructure/orchestrator/container_manager.py`
- [ ] Step 4: Create `infrastructure/orchestrator/compose_override.py`
- [ ] Step 5: Add system routes to `fastapi_app.py`
- [ ] Step 6: Add Frigate config update integration
- [ ] Step 7: Add Docker socket proxy for security
- [ ] Step 8: Add hardware/container widgets to web panel
- [ ] Step 9: Tests: hardware discovery mock, compose override generation

---

## Sub-Phase 15.3: IP Protection & Obfuscation (2–3 days)

- [ ] Step 1: Evaluate PyArmor trial — obfuscate `src/frigate_intelligence/`
- [ ] Step 2: Create multi-stage `Dockerfile.obfuscated`
- [ ] Step 3: Update CI/CD: `flutter build apk --obfuscate --split-debug-info`
- [ ] Step 4: Create `docker save` build script for tarball generation
- [ ] Step 5: Verify obfuscated container passes all tests
- [ ] Step 6: Secure debug symbol storage policy

---

## Sub-Phase 15.4: Air-Gapped Installer & Hardware Locking (3–4 days)

- [ ] Step 1: Create `license_generator.py` (MAC + SHA-256)
- [ ] Step 2: Create `install.sh` with prerequisite detection
- [ ] Step 3: Package offline Docker/NVIDIA RPMs
- [ ] Step 4: Create Makeself `.run` archive builder script
- [ ] Step 5: Test full air-gapped install on clean server
- [ ] Step 6: Test hardware lock bypass scenarios
- [ ] Step 7: Documentation: customer deployment guide
