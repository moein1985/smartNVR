"""Container capability checker — determines GPU support for Docker containers."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_GPU_IMAGE_PATTERNS = ("tensorrt", "cuda", "nvidia/")


@dataclass
class ContainerCapability:
    supports_gpu: bool
    detection_strategy: str
    details: str = ""


class ContainerCapabilityChecker:
    """Checks whether a Docker container supports GPU acceleration.

    Uses three strategies in order:
    1. Inspect HostConfig.DeviceRequests for NVIDIA driver requests
    2. Match image name patterns (tensorrt, cuda, nvidia/)
    3. Default to CPU-only
    """

    def check(self, container) -> ContainerCapability:
        try:
            result = self._check_device_requests(container)
            if result:
                return result

            result = self._check_image_name(container)
            if result:
                return result

            return ContainerCapability(
                supports_gpu=False,
                detection_strategy="cpu_only",
                details="No GPU indicators found, defaulting to CPU-only",
            )
        except Exception as e:
            logger.error(
                "[ContainerCapability] Failed to check container %s: %s",
                getattr(container, "name", "unknown"),
                e,
                exc_info=True,
            )
            return ContainerCapability(
                supports_gpu=False,
                detection_strategy="error",
                details=str(e),
            )

    def _check_device_requests(self, container) -> ContainerCapability | None:
        try:
            attrs = container.attrs
            host_config = attrs.get("HostConfig", {})
            device_requests = host_config.get("DeviceRequests", [])

            for req in device_requests:
                driver = req.get("Driver", "")
                if driver == "nvidia":
                    device_ids = req.get("DeviceIDs", [])
                    logger.info(
                        "[ContainerCapability] Container '%s' has NVIDIA DeviceRequests (devices=%s)",
                        container.name,
                        device_ids,
                    )
                    return ContainerCapability(
                        supports_gpu=True,
                        detection_strategy="device_requests",
                        details=f"NVIDIA driver requested, DeviceIDs={device_ids}",
                    )
        except Exception as e:
            logger.warning(
                "[ContainerCapability] Error checking DeviceRequests for '%s': %s",
                getattr(container, "name", "unknown"),
                e,
            )
        return None

    def _check_image_name(self, container) -> ContainerCapability | None:
        try:
            image_name = ""
            if hasattr(container, "image") and container.image:
                if container.image.tags:
                    image_name = container.image.tags[0]
                elif hasattr(container.image, "id"):
                    image_name = container.image.id

            image_lower = image_name.lower()
            for pattern in _GPU_IMAGE_PATTERNS:
                if pattern in image_lower:
                    logger.info(
                        "[ContainerCapability] Container '%s' image '%s' matches GPU pattern '%s'",
                        container.name,
                        image_name,
                        pattern,
                    )
                    return ContainerCapability(
                        supports_gpu=True,
                        detection_strategy="image_pattern",
                        details=f"Image '{image_name}' matches pattern '{pattern}'",
                    )
        except Exception as e:
            logger.warning(
                "[ContainerCapability] Error checking image name for '%s': %s",
                getattr(container, "name", "unknown"),
                e,
            )
        return None
