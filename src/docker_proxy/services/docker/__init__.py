from docker import DockerClient
import logging

DOCKER_SOCK = 'unix://var/run/docker.sock'
DOCKER_HOST = DOCKER_SOCK
DOCKER_PORT = 2373
docker_client = DockerClient(DOCKER_HOST)
logger = logging.getLogger(__name__)
