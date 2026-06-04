from services.docker import network_service
import logging
logger = logging.getLogger(__name__)


GLOBAL_NETWORK_NAME = "zeta_network"


def setup_environment():
    """
    Setup zeta environment.
    """
    try:
        if not network_service.does_network_exist(GLOBAL_NETWORK_NAME):
            return network_service.create_network(GLOBAL_NETWORK_NAME)
        else:
            return network_service.get_network(GLOBAL_NETWORK_NAME)
    except Exception as e:
        logger.error(e)
        raise RuntimeError(f"Unable to create global network '{GLOBAL_NETWORK_NAME}'")


def clean_environment(network):
    """
    Cleanup zeta environment.
    """
    try:
        network.remove()
    except Exception as e:
        logger.error(e)
        raise RuntimeError(f"Unable to delete the network {network.name}")
