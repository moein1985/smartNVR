import logging
from collections import deque
from pathlib import Path

from fastapi import APIRouter, Body, File, HTTPException, Query, UploadFile

logger = logging.getLogger(__name__)

_LOG_FILE = Path("data/logs/app.log")
_UPDATE_DIR = Path("data/updates")


def create_system_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/system", tags=["system"])

    @router.get("/logs")
    async def get_logs(
        lines: int = Query(100, ge=1, le=1000, description="Number of log lines to return"),
    ):
        """Return the last N lines from the application log file."""
        if not _LOG_FILE.exists():
            return {"lines": [], "total": 0, "message": "Log file not found"}

        try:
            with _LOG_FILE.open("r", encoding="utf-8") as f:
                tail = deque(f, maxlen=lines)
        except OSError as e:
            logger.error(f"Failed to read log file: {e}")
            raise HTTPException(status_code=500, detail="Failed to read log file") from e

        result = list(tail)
        return {"lines": result, "total": len(result)}

    @router.post("/update")
    async def upload_update(file: UploadFile = File(...)):
        """Accept a .tar update package, save it, and trigger the update agent."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        if not file.filename.endswith(".tar"):
            raise HTTPException(
                status_code=400,
                detail="Update file must be a .tar archive",
            )

        _UPDATE_DIR.mkdir(parents=True, exist_ok=True)
        dest = _UPDATE_DIR / file.filename

        try:
            content = await file.read()
            dest.write_bytes(content)
        except OSError as e:
            logger.error(f"Failed to save update file: {e}")
            raise HTTPException(status_code=500, detail="Failed to save update file") from e
        finally:
            await file.close()

        logger.info(f"Update package saved: {dest} ({len(content)} bytes)")

        try:
            from frigate_intelligence.updater.agent import UpdateAgent

            agent = UpdateAgent(
                update_file=str(dest),
                container_name="frigate-intelligence",
                health_url="http://frigate-intelligence:8000/api/v1/health",
            )
            result = agent.run()
        except Exception as e:
            logger.error(f"Update agent failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Update failed: {e}") from e

        if result.get("status") == "rolled_back":
            return {"status": "rolled_back", "message": result.get("message", "Update rolled back"), "details": result}
        return {"status": "ok", "message": "Update applied successfully", "details": result}

    @router.get("/hardware")
    async def get_hardware():
        """Return discovered CPU, RAM, and GPU resources."""
        from frigate_intelligence.infrastructure.orchestrator.hardware_discovery import (
            HardwareDiscovery,
        )

        try:
            discovery = HardwareDiscovery()
            info = discovery.discover()
            return info.to_dict()
        except Exception as e:
            logger.error(f"Hardware discovery failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Hardware discovery failed: {e}") from e

    @router.get("/containers")
    async def get_containers(all_statuses: bool = Query(False, description="Include stopped containers")):
        """Return list of Docker containers and their statuses."""
        from frigate_intelligence.infrastructure.orchestrator.container_manager import (
            ContainerManager,
        )

        try:
            manager = ContainerManager()
            return {"containers": manager.to_dict_list(all_statuses=all_statuses)}
        except Exception as e:
            logger.error(f"Container listing failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Container listing failed: {e}") from e

    @router.post("/assign")
    async def assign_resources(payload: dict = Body(...)):
        """Accept resource pinning payload and write docker-compose.override.yml."""
        from frigate_intelligence.infrastructure.orchestrator.compose_override import (
            ComposeOverrideGenerator,
            ResourceAssignment,
        )

        assignments_data = payload.get("assignments", [])
        if not assignments_data:
            raise HTTPException(status_code=400, detail="No assignments provided")

        assignments: list[ResourceAssignment] = []
        for item in assignments_data:
            service = item.get("service")
            if not service:
                raise HTTPException(status_code=400, detail="Each assignment requires a 'service' name")
            assignments.append(
                ResourceAssignment(
                    service=service,
                    cpuset=item.get("cpuset"),
                    gpu_ids=item.get("gpu_ids"),
                    memory_limit=item.get("memory_limit"),
                )
            )

        try:
            generator = ComposeOverrideGenerator()
            path = generator.write(assignments)
            return {
                "status": "ok",
                "message": f"Override file written to {path}",
                "path": str(path),
            }
        except Exception as e:
            logger.error(f"Failed to write override file: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to write override: {e}") from e

    return router
