"""Update Agent — OTA patching with automatic rollback.

This module runs inside the update-agent sidecar container. It has access
to the Docker socket (/var/run/docker.sock) and the shared data volume
(./data:/app/data) to perform safe container updates.

Update sequence:
1. Tag the current image as :rollback
2. Load the new image from the .tar file
3. Restart the target container with the new image
4. Poll the health endpoint for up to 60 seconds
5. If healthy → update succeeds; if unhealthy → rollback to :rollback tag
"""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_HEALTH_POLL_INTERVAL = 5
_HEALTH_TIMEOUT = 60


@dataclass
class UpdateResult:
    status: str  # "success" | "rolled_back" | "failed"
    message: str
    old_image: str = ""
    new_image: str = ""
    rollback_image: str = ""
    health_check_passed: bool = False
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "message": self.message,
            "old_image": self.old_image,
            "new_image": self.new_image,
            "rollback_image": self.rollback_image,
            "health_check_passed": self.health_check_passed,
            "details": self.details,
        }


class UpdateAgent:
    """Orchestrates a safe OTA update for a Docker container."""

    def __init__(
        self,
        update_file: str,
        container_name: str = "frigate-intelligence",
        health_url: str = "http://frigate-intelligence:8000/api/v1/health",
        image_tag: str = "latest",
        rollback_tag: str = "rollback",
        compose_dir: str = "/app",
    ) -> None:
        self._update_file = Path(update_file)
        self._container_name = container_name
        self._health_url = health_url
        self._image_tag = image_tag
        self._rollback_tag = rollback_tag
        self._compose_dir = compose_dir

    def run(self) -> dict:
        """Execute the full update sequence with rollback on failure."""
        logger.info(f"Starting OTA update from {self._update_file}")

        if not self._update_file.exists():
            return UpdateResult(
                status="failed",
                message=f"Update file not found: {self._update_file}",
            ).to_dict()

        try:
            client = self._get_docker_client()
        except ImportError:
            return UpdateResult(
                status="failed",
                message="docker PyPI package is not installed",
            ).to_dict()
        if client is None:
            return UpdateResult(
                status="failed",
                message="docker PyPI package is not installed",
            ).to_dict()

        old_image = self._get_current_image(client)
        if not old_image:
            return UpdateResult(
                status="failed",
                message=f"Container '{self._container_name}' not found or has no image",
            ).to_dict()

        rollback_image = self._tag_rollback(client, old_image)
        logger.info(f"Tagged {old_image} as {rollback_image}")

        new_image = self._load_image(client)
        if not new_image:
            return UpdateResult(
                status="failed",
                message="Failed to load new image from tar file",
            ).to_dict()
        logger.info(f"Loaded new image: {new_image}")

        self._restart_container(client)
        logger.info("Container restarted with new image")

        healthy = self._wait_for_health()
        if healthy:
            logger.info("Health check passed — update successful")
            return UpdateResult(
                status="success",
                message="Update applied successfully",
                old_image=old_image,
                new_image=new_image,
                rollback_image=rollback_image,
                health_check_passed=True,
            ).to_dict()

        logger.warning("Health check failed — initiating rollback")
        self._rollback(client, rollback_image)
        healthy_after_rollback = self._wait_for_health()

        return UpdateResult(
            status="rolled_back",
            message="Update rolled back due to health check failure",
            old_image=old_image,
            new_image=new_image,
            rollback_image=rollback_image,
            health_check_passed=healthy_after_rollback,
            details={"rollback_health": healthy_after_rollback},
        ).to_dict()

    def _get_docker_client(self):
        """Lazily import docker and return a client. Raises ImportError if not installed."""
        import docker

        return docker.from_env()

    def _get_current_image(self, client) -> str:
        """Return the image tag of the currently running container."""
        try:
            containers = client.containers.list(filters={"name": self._container_name})
            if not containers:
                return ""
            container = containers[0]
            return container.image.tags[0] if container.image.tags else container.image.id
        except Exception as e:
            logger.error(f"Failed to get current container image: {e}")
            return ""

    def _tag_rollback(self, client, image_tag: str) -> str:
        """Tag the current image as :rollback for potential rollback."""
        try:
            image = client.images.get(image_tag)
            rollback_ref = f"{image_tag.split(':')[0]}:{self._rollback_tag}"
            image.tag(rollback_ref)
            return rollback_ref
        except Exception as e:
            logger.error(f"Failed to tag rollback image: {e}")
            return ""

    def _load_image(self, client) -> str:
        """Load a new Docker image from a .tar file."""
        try:
            with self._update_file.open("rb") as f:
                result = client.images.load(f.read())
            if result:
                img = result[0]
                return img.tags[0] if img.tags else img.id
            return ""
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            return ""

    def _restart_container(self, client) -> None:
        """Restart the target container via Docker Compose or direct restart."""
        try:
            containers = client.containers.list(filters={"name": self._container_name})
            if containers:
                containers[0].restart(timeout=30)
        except Exception as e:
            logger.error(f"Failed to restart container: {e}")

    def _wait_for_health(self) -> bool:
        """Poll the health endpoint for up to _HEALTH_TIMEOUT seconds."""
        deadline = time.time() + _HEALTH_TIMEOUT
        while time.time() < deadline:
            try:
                resp = httpx.get(self._health_url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "ok":
                        return True
            except Exception:
                pass
            time.sleep(_HEALTH_POLL_INTERVAL)
        return False

    def _rollback(self, client, rollback_image: str) -> None:
        """Revert to the :rollback image and restart."""
        logger.info(f"Rolling back to {rollback_image}")
        try:
            containers = client.containers.list(filters={"name": self._container_name})
            if containers:
                container = containers[0]
                container.stop(timeout=15)
                container.remove(force=True)

            client.containers.run(
                rollback_image,
                name=self._container_name,
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                ports={"8000/tcp": 8088},
                volumes={
                    "/opt/frigate/config": {"bind": "/opt/frigate/config", "mode": "ro"},
                    f"{self._compose_dir}/data": {"bind": "/app/data", "mode": "rw"},
                },
                network="frigate_default",
            )
            logger.info("Rollback container started")
        except Exception as e:
            logger.error(f"Rollback failed: {e}", exc_info=True)
