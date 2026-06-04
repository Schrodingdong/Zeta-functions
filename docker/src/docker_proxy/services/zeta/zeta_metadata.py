"""
Zeta metadata should be tightly linked to the current deployment.
A change in the functions means a redeployment,
Therfore deleting and re creating the metadata
"""
from services.docker import image_service, container_service
from datetime import datetime, timedelta
from . import pns_service
from . import db
import threading
import logging
import socket
import time
import json
import os


SOCKET_DIR = os.path.join(os.getcwd(), "src/docker_proxy/tmp")
SOCKET_PATH = os.path.join(SOCKET_DIR, "docker_proxy.sock")
IDLE_TIMEOUT = timedelta(seconds=30).total_seconds()
logger = logging.getLogger(__name__)
lock = threading.Lock()
zeta_meta = {}


# Zeta Heartbeat =============================================================
def terminate_idle_containers():
    """
    Terminate IDLE zeta container runners if idle for more than `IDLE_TIMEOUT`
    """
    while True:
        zeta_meta_list = db.fetch_all_zeta_functions()
        for zeta_meta in zeta_meta_list:
            # TODO: Zeta supports 1 container per function as of now
            rcn = zeta_meta["runner_container_name"]
            rclh = zeta_meta["runner_container_last_heartbeat"]
            if rclh is None or rclh == 0:
                logger.warning("Zeta Container Runner still getting initialized, can't terminate.")
                continue
            if time.time() - rclh > IDLE_TIMEOUT:
                if not container_service.does_container_exist(rcn):
                    logger.warning(f"Zeta runner container {rcn} doesn't exist")
                    continue
                try:
                    # Removing zeta function runner containers
                    container_service.stop_container(rcn)
                    container_service.remove_container(rcn)
                    # Removing container meta for zeta
                    delete_zeta_container_metadata(rcn)
                    logger.info(f"Terminated idle zeta runner container {rcn}")
                except Exception as e:
                    logger.error(f"Error terminating zeta runner container {rcn}: {e}")
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
                    timestamp = int(meta["timestamp"])
                    update_zeta_heartbeat(container_id, timestamp)
            finally:
                connection.close()
    except KeyboardInterrupt:
        logger.info("Hearbeat socket shutting down")
    finally:
        server_socket.close()
        os.remove(SOCKET_PATH)


# Zeta metadata ===============================================================
def initialize_metadata_db():
    db.initialize_db()


# Create ======================================================================
def create_zeta_metadata(zeta_name: str):
    """
    Create zeta metadata for the specified zeta.

    Attributes
    ---
    zeta_name: str
    """
    runner_image_list = image_service.get_images_from_prefix(zeta_name)
    if len(runner_image_list) > 1:
        # Normaly, this shouldn't happen unless if manually poked
        # around the docker images
        errmsg = f"Found {len(runner_image_list)} runners found for zeta {zeta_name}"
        logger.error(errmsg)
        raise RuntimeError(errmsg)
    elif len(runner_image_list) == 0:
        errmsg = f"No runners found for zeta: {zeta_name}"
        logger.error(errmsg)
        raise RuntimeError(errmsg)
    runner_image = runner_image_list[0]
    # Save meta to DB
    try:
        db.insert_zeta_runner_image(
            image_id=str(runner_image.id),
            tag=str(runner_image.tags[0])
        )
    except Exception as e:
        logger.error("Error inserting the zeta runner image details in DB: " + str(e))
        raise e
    try:
        db.insert_zeta_function(
            name=zeta_name,
            created_at=time.time(),
            runner_image_id=runner_image.id,
            runner_container_id=None
        )
    except Exception as e:
        logger.error("Error inserting the zeta function metadata in DB: " + str(e))
        raise e
    # Retrieve the created zeta metadata
    try:
        meta = db.fetch_zeta_function_by_name(zeta_name)
    except Exception as e:
        logger.error("Couldn't fetch zeta metadata: " + str(e))
        raise e
    return meta


# Read ========================================================================
def get_all_zeta_metadata():
    """
    Returns a dict of the zeta names and metadata.
    """
    return db.fetch_all_zeta_functions()


def get_zeta_metadata(zeta_name: str):
    """
    Returns metadata for the specified zeta.

    Attributes
    ---
    zeta_name: str
    """
    if not is_zeta_registered(zeta_name):
        return {}
    return db.fetch_zeta_function_by_name(zeta_name)


def is_zeta_registered(zeta_name: str) -> bool:
    """
    Checks if the specified zeta is registered in the metadata.

    Attributes
    ---
    zeta_name: str
    """
    meta_dict = db.fetch_zeta_function_by_name(zeta_name)
    return len(meta_dict) > 0


# Update ======================================================================
def update_zeta_container_metadata(zeta_name: str):
    """
    Update the zeta container runner metadata for the specified zeta.

    Attributes
    ---
    zeta_name: str
    """
    try:
        container = container_service.get_container(zeta_name)
    except Exception as e:
        errmsg = f"Can't find zeta container runner: {zeta_name}"
        logger.error(errmsg + " : " + e)
        raise RuntimeError(errmsg)
    logger.info(container.ports)
    ports = container.ports["8000/tcp"][0]
    host_ip = ports["HostIp"]
    host_port = ports["HostPort"]
    db.insert_zeta_runner_container(
        function_name=zeta_name,
        container_name=container.name,
        container_id=container.id,
        host_ip=host_ip,
        host_port=host_port
    )


def update_zeta_heartbeat(container_id: str, timestamp: int):
    # TODO: change container_id to use zeta_name
    """
    Update the zeta container runner Heartbeat for the specified zeta.

    Attributes
    ---
    zeta_name: str
    """
    if container_id:
        container = container_service.get_container(container_id)
        if container.name == container_id or container.id.startswith(container_id):
            if is_zeta_registered(container.name):
                db.update_zeta_runner_container_heartbeat(container_id, timestamp)
                # with lock:
                    # runner_container_list = zeta_meta[container.name]["runnerContainer"]
                    # runner_container = list(filter(
                    #     lambda rc: rc["containerName"] == container.name,
                    #     runner_container_list
                    # ))[0]
                    # runner_container["lastHeartbeat"] = float(timestamp)


# Deletion ====================================================================
def delete_zeta_container_metadata(zeta_name: str):
    """
    Delete the zeta container runner metadata for the specified zeta.

    Attributes
    ---
    zeta_name: str
    """
    if not is_zeta_registered(zeta_name):
        return
    # Clean the PNS record
    # container_meta_list = zeta_meta[zeta_name]["runnerContainer"]
    # for container_meta in container_meta_list:
    #     container_port = int(container_meta["containerPorts"]["8000/tcp"][0]["HostPort"])
    #     pns_service.delete_pns_port_entry(container_port)
    # Clean the metadata
    db.delete_zeta_runner_container(zeta_name)


def delete_zeta_metadata(zeta_name: str):
    """
    Delete the metadata for the zeta function

    Attributes
    ---
    zeta_name: str
    """
    if not is_zeta_registered(zeta_name):
        return
    try:
        delete_zeta_container_metadata(zeta_name)
    except Exception as e:
        logger.error(f"Unable to delete zeta container metadata: {e}")
    try:
        db.delete_zeta_metadata(zeta_name)
    except Exception as e:
        logger.error(f"Unable to delete zeta metadata: {e}")
