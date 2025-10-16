from docker import DockerClient
import logging
import os


if "DOCKER_SOCKET" in os.environ:
    DOCKER_SOCK = 'unix:/'+os.environ["DOCKER_SOCKET"]
    print(f"> Found docker socket in the shell env variables: {DOCKER_SOCK}")
else:
    DOCKER_SOCK = 'unix://var/run/docker.sock'
    print(f"> Defaulting the docker.sock path to: {DOCKER_SOCK}")
DOCKER_HOST = DOCKER_SOCK
DOCKER_PORT = 2373
docker_client = DockerClient(DOCKER_HOST)
logger = logging.getLogger(__name__)
