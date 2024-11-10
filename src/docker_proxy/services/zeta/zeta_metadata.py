import services.docker_service as docker_service
import time
import logging
logger = logging.getLogger(__name__)

# Zeta metadata ===============================================================
# Zeta metadata should be tightly linked to the current deployment.
# A change in the functions means a redeployment,
# Therfore deleting and re creating the metadata
zeta_meta = {}


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
            "containerPorts": container.ports
        }
    )


def delete_zeta_container_metadata(zeta_name: str):
    if zeta_name not in zeta_meta:
        return
    zeta_meta[zeta_name]["runnerContainer"] = []


def delete_zeta_metadata(zeta_name: str):
    if zeta_name not in zeta_meta:
        return
    del zeta_meta[zeta_name]
