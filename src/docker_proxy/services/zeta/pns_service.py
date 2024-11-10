from random import randint
from requests.exceptions import ConnectionError, ReadTimeout
import requests
import logging


logger = logging.getLogger(__name__)
PNS = {}  # Port Name System - port-to-containerName mapping


def set_zeta_port(zeta_name: str, container_port: int):
    PNS[container_port] = zeta_name


def purge_pns_port():
    for port in PNS:
        del PNS[port]


def delete_pns_port_entry(container_port: int):
    if container_port not in PNS:
        return
    del PNS[container_port]


def retrieve_dynamic_port():
    """
    Get dynamic port from the [1024, 49151] range.
    The condition to retrieve a port are :
    - Port shouldn't be in the PNS
    - Port shouldn't be used by other apps
    """
    def is_port_in_pns(port: int):
        return port in PNS

    def is_port_used_by_other_app(port: int):
        try:
            requests.get(f"http://localhost:{port}", timeout=0.1)
            logger.warning(f"conflicting ports : {port} already in use")
            return True
        except ReadTimeout:
            logger.warning(f"conflicting ports : {port} already in use")
            return True
        except ConnectionError:
            return False

    port = randint(1024, 49151)
    while True:
        if is_port_in_pns(port) or is_port_used_by_other_app(port):
            port = ((port + 1) % 49151) + 1025
        else:
            break
    return port
