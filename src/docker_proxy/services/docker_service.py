"""
docker service to wrap the DockerClient instance. To be used to execute container engine specific commands.
"""
from services.docker import docker_client, logger
import os

SOCKET_DIR = os.path.join(os.getcwd(), "src/docker_proxy/tmp")  # synced with the runner's main.py
SOCKET_PATH = os.path.join(SOCKET_DIR, "docker_proxy.sock")     # synced with the runner's main.py


def instanciate_container_from_image(container_name: str, image_id: str, ports: dict, network: str):
    """
    Instanciate a container for the image with id `image_id`, exposed on ports described in `ports`. 

    Attributes
    ---
    - container_name: str
    - image_name: str
    - ports: dict
        Port specification to publish the container following this format: `{"<container_port>" : <host_port>}`.
        for example: `ports = {"8000": 9090}`
    """
    # Check image exists
    found = False
    for image in docker_client.images.list():
        if image.id == image_id:
            found = True
            break

    if not found :
        raise Exception("Unable to find the specified image")
    # Check if network exists
    if len(network) > 0:
        filtered_net_list = docker_client.networks.list(names=[network])
        if len(filtered_net_list) == 0:
            raise Exception(f"Unable to find the network {network}")
    # Instanciate the container
    container = docker_client.containers.run(
        image=image_id,
        name=container_name,
        detach=True,
        ports=ports,
        network=network,
        volumes={
            SOCKET_PATH: {
                'bind': "/zeta/tmp/docker_proxy.sock",
                'mode': 'ro'
            }
        },
    )
    return container


def does_container_exist(container_name: str):
    """
    Checks if the container is in a `RUNNING` state

    Attributes
    ---
    - container_name: str
    """
    container_list_name = list(map(lambda x: x.name, docker_client.containers.list(all=True)))
    return container_name in container_list_name


def is_container_running(container_name: str):
    """
    Checks if the container is in a `RUNNING` state

    Attributes 
    ---
    - container_name: str
    """
    container_list_name = list(map(lambda x: x.name, docker_client.containers.list()))
    return container_name in container_list_name

def get_container(container_name_or_id: str):
    """
    Retrieve the specified container 

    Attributes
    ---
    - container_name_or_id: str
        Can be either the container name or id
    """
    try:
        container = docker_client.containers.get(container_name_or_id)
        return container
    except Exception as err :
        raise RuntimeError("Unable to retrieve the container: ", err)

def get_containers_of_image(image_id: str):
    """
    Get containers instanciated from an image of id `image_id`

    Attributes 
    ---
    - image_id: str
    """
    container_list = []
    for container in list(docker_client.containers.list(all=True)):
        if container.image.id == image_id:
            container_list.append(container)
    return container_list

def restart_container(container_name_or_id: str):
    """
    Restart the specified container

    Attributes
    ---
    - container_name_or_id: str
        Can be either the container name or id
    """
    try:
        docker_client.containers.get(container_name_or_id).restart()
    except Exception as err :
        raise RuntimeError("Unable to restart the container of id "+ container_name_or_id + " : ", err)

def stop_container(container_name_or_id: str):
    """
    Stop the specified container

    Attributes
    ---
    - container_name_or_id: str
        Can be either the container name or id
    """
    try:
        docker_client.containers.get(container_name_or_id).stop()
    except Exception as err :
        raise RuntimeError("Unable to stop the container of id", container_name_or_id, ":", err)

def run_container(container_name_or_id: str):
    """
    Run/Start the specified container

    Attributes
    ---
    - container_name_or_id: str
        Can be either the container name or id
    """
    try:
        docker_client.containers.run(container_name_or_id)
    except Exception as err :
        raise RuntimeError("Unable to run the container of id", container_name_or_id, ":", err)

def remove_container(container_name_or_id: str):
    """
    Remove the specified container

    Attributes
    ---
    - container_name_or_id: str
        Can be either the container name or id
    """
    try:
        try:
            logger.info(f"Removing container: {container_name_or_id}")
            docker_client.containers.get(container_name_or_id).remove()
        except:
            logger.info(f"Forcefully Removing container: {container_name_or_id}")
            docker_client.containers.get(container_name_or_id).remove(force=True)
    except Exception as err :
        raise RuntimeError("Unable to remove the container of id", container_name_or_id, ":", err)

def prune_containers() -> list:
    """
    Remove all containers, whathever the state they are in.
    """
    # TODO : Make sure that the once we add networking, we will be able to prune container spun up by a specific container
    removed = []
    for name in list(map(lambda x: x.name, docker_client.containers.list(all=True))):
        try:
            stop_container(name)
            remove_container(name)
            removed.append(name)
        except:
            logger.warning("Can't remove container: ", name)
            continue
    return removed
