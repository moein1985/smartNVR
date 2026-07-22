import logging
from collections import deque
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

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

    return router
