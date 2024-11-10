import services.docker_service as docker_service
import logging
logger = logging.getLogger(__name__)


GLOBAL_NETWORK_NAME = "zeta_network"


def setup_environment():
    """
    Setup zeta environment.
    """
    try:
        return docker_service.create_network(GLOBAL_NETWORK_NAME)
    except Exception as e:
        raise RuntimeError(str(e))


def clean_environment(network):
    """
    Cleanup zeta environment.
    """
    try:
        network.remove()
    except Exception as e:
        logger.error(e)
        raise RuntimeError(f"Unable to delete the network {network.name}")
