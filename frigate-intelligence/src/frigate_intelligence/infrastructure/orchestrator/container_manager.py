"""Container manager module — lists and inspects running Docker containers."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ContainerInfo:
    name: str
    image: str
    status: str
    short_id: str
    ports: list[dict]


class ContainerManager:
    """Manages Docker containers via the docker SDK."""

    def __init__(self, client=None):
        self._client = client

    def _get_client(self):
        if self._client is not None:
            return self._client
        import docker

        return docker.from_env()

    def list_containers(self, all_statuses: bool = False) -> list[ContainerInfo]:
        try:
            client = self._get_client()
            containers = client.containers.list(all=all_statuses)
        except ImportError:
            logger.warning("docker PyPI package is not installed")
            return []
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            return []

        result: list[ContainerInfo] = []
        for c in containers:
            try:
                ports = []
                if hasattr(c, "ports") and c.ports:
                    for container_port, host_bindings in c.ports.items():
                        if host_bindings:
                            for binding in host_bindings:
                                ports.append(
                                    {
                                        "container_port": container_port,
                                        "host_ip": binding.get("HostIp", ""),
                                        "host_port": binding.get("HostPort", ""),
                                    }
                                )
                        else:
                            ports.append({"container_port": container_port})

                result.append(
                    ContainerInfo(
                        name=c.name,
                        image=c.image.tags[0] if c.image.tags else c.image.id,
                        status=c.status,
                        short_id=c.short_id,
                        ports=ports,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to inspect container: {e}")

        return result

    def to_dict_list(self, all_statuses: bool = False) -> list[dict]:
        containers = self.list_containers(all_statuses=all_statuses)
        return [
            {
                "name": c.name,
                "image": c.image,
                "status": c.status,
                "short_id": c.short_id,
                "ports": c.ports,
            }
            for c in containers
        ]
