from fastapi import File, UploadFile
from services.docker import image_service, container_service
from . import zeta_metadata as meta
from . import pns_service as pns
from . import zeta_utils as utils
from . import zeta_environment as zeta_env
import requests
import time
import logging
import json
logger = logging.getLogger(__name__)


async def create_zeta(zeta_name: str, file: UploadFile = File(...)):
    """
    Create/Deploy the zeta function.
    ...
    Attributes
    ---
    zeta_name : str
        Zeta function name.
    file : fastapi.UploadFile
        File to use to create the runner image.
    """
    # Delete previous zeta deployment
    if is_zeta_created(zeta_name):
        try:
            logger.info("Deleting previous zeta deployment")
            delete_zeta(zeta_name)
        except Exception as e:
            logger.error(e)
            raise RuntimeError("Error cleaning old zeta function")
    # extract handler
    logger.info("Extracting handler from input files")
    try:
        handler_content = await utils.extract_handler_data(file)
    except Exception as e:
        logger.error(e)
        raise RuntimeError("Error reading handler and extracting content")
    # Build runner image
    logger.info("Build the zeta runner image")
    try:
        utils.build_zeta_runner_image(handler_content, zeta_name)
    except Exception as e:
        logger.error(e)
        raise RuntimeError("Error buidling runner image.")
    # Generating zeta metadata
    logger.info("Create zeta function metadata")
    try:
        zeta_meta = meta.create_zeta_metadata(zeta_name)
    except Exception as e:
        logger.error(e)
        raise RuntimeError("Error creating zeta metadata.")
    return zeta_meta


# Get zeta function
def get_zeta_metadata(zeta_name: str) -> dict:
    return meta.get_zeta_metadata(zeta_name)


# Delete the function(s)
def delete_zeta(zeta_name: str):
    """
    Delete the specified zeta.
    The steps to do so are as follow :
    - Check if it exists in the metadata registry
    - Shutdown any up containers with related images
    - Delete related images
    - Delete metadata

    Attributes
    ---
    - zeta_name: str
    """
    # Check it is in the meta registery
    if not is_zeta_created(zeta_name):
        raise RuntimeError("Zeta function not found")
    # Down the container
    if container_service.does_container_exist(zeta_name):
        try:
            container_service.stop_container(zeta_name)
            container_service.remove_container(zeta_name)
            logger.info(f"Successfully removed zeta runner container: {zeta_name}")
        except Exception as e:
            logger.warning(f"Unable to stop and remove the container: {e}")
    else:
        logger.info(f"No container found for {zeta_name}")
    # Delete its images
    try:
        removed_images = image_service.delete_images_from_prefix(zeta_name)
        logger.info(f"Successfully removed zeta runner images: {removed_images}")
    except Exception as e:
        logger.error(f"Unable to remove the zeta runner images: {e}")
    # Delete its metadata
    meta.delete_zeta_metadata(zeta_name)


def exterminate_all_zeta():
    """
    Deletes all running zeta functions.
    """
    zeta_name_list = []
    for zeta_name in meta.get_all_zeta_metadata():
        zeta_name_list.append(zeta_name)
    counter = 0
    for zeta_name in zeta_name_list:
        delete_zeta(zeta_name)
        counter += 1
    logger.info(f"Deleted {counter} zetas")


# Run the function ============================================================
def cold_start_zeta(zeta_name: str):
    """
    Cold start the zeta function

    Attributes
    ---
    - zeta_name: str
    """
    runner_image = utils.retrieve_runner_image(zeta_name)
    if runner_image is None:
        raise RuntimeError("Unable to run the zeta function '" + zeta_name + "'")
    try:
        # Get dynamic port and set it for the zeta in the DNS
        host_port = pns.retrieve_dynamic_port()
        pns.set_zeta_port(zeta_name, host_port)
        # Instanciate the container
        container_service.instanciate_container_from_image(
            container_name=zeta_name,
            image_id=runner_image.id,
            ports={"8000": host_port},  # 8000 is the open container port
            network=zeta_env.GLOBAL_NETWORK_NAME
        )
        # Update container metadata
        meta.update_zeta_container_metadata(zeta_name)
    except Exception as e:
        logger.error(e)
        raise RuntimeError(f"Unable to run the zeta function '{zeta_name}'")


def run_zeta(zeta_name: str, params: dict = {}):
    try:
        container = container_service.get_container(zeta_name)
    except Exception:
        raise RuntimeError(f"Unable to run the zeta function '{zeta_name}'")
    container_hostname = utils.retrieve_container_hostname(container)
    # Wait until the container is up
    TIMEOUT = 60
    start_time = time.time()
    while not is_zeta_up(zeta_name):
        if time.time() - start_time > TIMEOUT:
            raise RuntimeError("Zeta function is not up. Exit due to timeout")
        time.sleep(1)
    # Proxy the request to the zeta
    logger.info(f"Proxying request to: {zeta_name}")
    try:
        response = requests.post(
            url=container_hostname+"/run",
            data=json.dumps(params)
        )
        content = response.content.decode()
        return json.loads(content)
    except Exception as e:
        raise e


# utils =======================================================================
def is_zeta_created(zeta_name: str) -> bool:
    is_zeta_registered = meta.is_zeta_registered(zeta_name)
    return is_zeta_registered


def is_zeta_up(zeta_name: str) -> bool:
    """
    Checks if the zeta function is up and running.
    This verification is done in 2 steps:
    - Verify that the container is up and in `RUNNING` state.
    - Verify if the zeta application inside the container has started.

    Attributes
    ---
    - zeta_name: str
    """
    # Checks if the container is running
    if not container_service.is_container_running(zeta_name):
        logger.warning("Zeta container is not RUNNING")
        return False
    # Checks if the app has successfully started
    container = container_service.get_container(zeta_name)
    host_name = utils.retrieve_container_hostname(container)
    try:
        response = requests.get(host_name+"/is-running")
        logger.info("Zeta container is UP")
        return response.status_code == 200
    except Exception:
        logger.warning("Zeta container is not UP")
        return False
