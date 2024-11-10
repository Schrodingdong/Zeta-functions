"""
Zeta metadata should be tightly linked to the current deployment.
A change in the functions means a redeployment,
Therfore deleting and re creating the metadata
"""
import services.docker_service as docker_service
from datetime import datetime, timedelta
import threading
import logging
import socket
import time
import json
import os


SOCKET_DIR = os.path.join(os.getcwd(), "src/docker_proxy/tmp")
SOCKET_PATH = os.path.join(SOCKET_DIR, "docker_proxy.sock")
IDLE_TIMEOUT = timedelta(seconds=30)
logger = logging.getLogger(__name__)
lock = threading.Lock()
zeta_meta = {}


# Zeta Heartbeat =============================================================
def terminate_idle_containers():
    """
    Terminate IDLE zeta container runners if idle for more than `IDLE_TIMEOUT`
    """
    while True:
        with lock:
            for container_name in zeta_meta:
                runner_container_list = zeta_meta[container_name]["runnerContainer"]
                for runner_container in runner_container_list:
                    last_heartbeat = runner_container["lastHeartbeat"]
                    if isinstance(last_heartbeat, float) or isinstance(last_heartbeat, int):
                        last_heartbeat = datetime.fromtimestamp(last_heartbeat)
                    if datetime.now() - last_heartbeat > IDLE_TIMEOUT:
                        if not docker_service.does_container_exist(container_name):
                            logger.warning(f"Zeta runner container {container_name} doesn't exist")
                            continue
                        try:
                            # Removing zeta function runner containers
                            docker_service.stop_container(container_name)
                            docker_service.remove_container(container_name)
                            # Removing container meta for zeta
                            delete_zeta_container_metadata(container_name)
                            logger.info(f"Terminated idle zeta runner container {container_name}")
                        except Exception as e:
                            logger.error(f"Error terminating zeta runner container {container_name}: {e}")
        time.sleep(15)


def accept_heartbeat_connection():
    """
    Heartbeat implementation using sockets.
    """
    # Clean up the socket file if it already exists
    if not os.path.isdir(SOCKET_DIR):
        os.mkdir(SOCKET_DIR)
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)
    # Create / bind the Unix socket
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(SOCKET_PATH)
    server_socket.listen(1)
    try:
        while True:
            connection, client_address = server_socket.accept()
            try:
                # Receive and process data
                while data := connection.recv(1024):
                    meta = json.loads(data.decode())
                    logger.info(f"HEARTBEAT - Heartbeat received: {meta}")
                    container_id = meta["containerId"]
                    timestamp = meta["timestamp"]
                    update_zeta_heartbeat(container_id, timestamp)
            finally:
                connection.close()
    except KeyboardInterrupt:
        logger.info("Hearbeat socket shutting down")
    finally:
        server_socket.close()
        os.remove(SOCKET_PATH)


# Zeta metadata ===============================================================
def create_zeta_metadata(zeta_name: str):
    runner_image_list = docker_service.get_images_from_prefix(zeta_name)
    if len(runner_image_list) > 1:  # Normaly, this shouldn't happen
        errmsg = f"Found {len(runner_image_list)} runners found for zeta {zeta_name}"
        logger.error(errmsg)
        raise RuntimeError(errmsg)
    elif len(runner_image_list) == 0:
        errmsg = f"No runners found for zeta: {zeta_name}"
        logger.error(errmsg)
        raise RuntimeError(errmsg)
    runner_image = runner_image_list[0]
    meta = {
        "zetaName": zeta_name,
        "runnerImage": {
            "imageId": runner_image.id,
            "tags": runner_image.tags
        },
        "runnerContainer": [],
        "createdAt": time.time(),
    }
    zeta_meta[zeta_name] = meta
    return meta


def get_all_zeta_metadata():
    """
    Returns a dict of the zeta names and metadata.
    """
    return zeta_meta


def get_zeta_metadata(zeta_name: str):
    """
    Returns metadata for the specified zeta.

    Attributes
    ---
    zeta_name: str
    """
    if not is_zeta_registered(zeta_name):
        return {}
    return zeta_meta[zeta_name]


def is_zeta_registered(zeta_name: str) -> bool:
    """
    Checks if the specified zeta is registered in the metadata.
    """
    return zeta_name in zeta_meta


def update_zeta_container_metadata(zeta_name: str):
    try:
        container = docker_service.get_container(zeta_name)
    except Exception as e:
        logger.error(e)
        raise RuntimeError(f"Can't find zeta container runner: {zeta_name}")
    zeta_meta[zeta_name]["runnerContainer"].append(
        {
            "containerName": container.name,
            "containerId": container.id,
            "containerPorts": container.ports,
            "lastHeartbeat": 0
        }
    )


def update_zeta_heartbeat(container_id: str, timestamp: str):
    if container_id:
        container = docker_service.get_container(container_id)
        "".startswith
        if container.name == container_id or container.id.startswith(container_id):
            if is_zeta_registered(container.name):
                with lock:
                    runner_container_list = zeta_meta[container.name]["runnerContainer"]
                    runner_container = list(filter(
                        lambda rc: rc["containerName"] == container.name,
                        runner_container_list
                    ))[0]
                    runner_container["lastHeartbeat"] = float(timestamp)


def delete_zeta_container_metadata(zeta_name: str):
    if zeta_name not in zeta_meta:
        return
    # Clean the PNS record
    container_metadata = zeta_meta[zeta_name]["runnerContainer"]
    ports = container_metadata["containerPorts"]
    print(ports)
    # Clean the metadata
    zeta_meta[zeta_name]["runnerContainer"] = []


def delete_zeta_metadata(zeta_name: str):
    if zeta_name not in zeta_meta:
        return
    # Delete the zeta container metadata
    delete_zeta_container_metadata(zeta_name)
    # Delete the zeta metadata
    del zeta_meta[zeta_name]
