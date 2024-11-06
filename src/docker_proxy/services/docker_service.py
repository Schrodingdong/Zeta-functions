"""
docker service to wrap the DockerClient instance. To be used to execute container engine specific commands.
"""
from docker import DockerClient
import os

DOCKER_SOCK = 'unix://var/run/docker.sock'
DOCKER_HOST = DOCKER_SOCK
DOCKER_PORT = 2373
docker_client = DockerClient(DOCKER_HOST)
SOCKET_DIR = os.path.join(os.getcwd(), "src/docker_proxy/tmp")  # synced with the runner's main.py
SOCKET_PATH = os.path.join(SOCKET_DIR, "docker_proxy.sock")     # synced with the runner's main.py

# Image Management Service =======================================================
def list_images():
    """
    List all docker images images
    """
    return docker_client.images.list()

def get_image_from_tag(image_tag: str):
    """
    Retrieve the image tagged `image_tag`

    Attributes
    ---
    - image_tag: str
    """
    return list(filter(
        lambda image: image_tag in image.tags,
        list_images()
    ))[0]

def get_image_from_id(image_id: str):
    """
    Retrieve the image with id `image_id`

    Attributes
    ---
    - image_id: str
    """
    return list(filter(
        lambda image: (image.id == image_id) or (image.short_id in image_id),
        list_images()
    ))[0]

def get_images_from_prefix(prefix: str):
    """
    Return a list of images given a string prefix. The matching is done to the `image.tags` elements.

    Attributes
    ---
    - prefix: str
    """
    image_list = docker_client.images.list()
    found_images = []
    for image in image_list:
        for tag in image.tags:
            if prefix in tag:
                found_images.append(image)
                break
    return found_images

def build_image(image_name: str, dockerfile_path: str):
    """
    Build an image of `image_name`, using the dockerfile specified at `dockerfile_path`

    Attributes
    ---
    - image_name: str
        The image name to be used
    - dockerfile_path: str
        Dockerfile to use for the build
    """
    try:
        docker_client.images.build(tag=image_name, path=dockerfile_path)
    except:
        raise Exception("Unable to build the image '" + image_name + "': "+ dockerfile_path)

def delete_images_from_prefix(prefix: str):
    """
    Delete the images prefixed with `prefix`

    Attributes
    ---
    - prefix: str
        Prefix to check the image tag on.
    
    Return Value
    ---
    - removed_containers: List
    """
    image_list = docker_client.images.list()
    removed_images = []
    for image in image_list:
        for tag in image.tags:
            if prefix in tag:
                try:
                    print("deleting image:", tag)
                    docker_client.images.remove(image=image.id)
                except:
                    print("FORCE deleting image:", tag)
                    docker_client.images.remove(image=image.id, force=True)
                finally:
                    removed_images.append(image.id)
                break
    return removed_images

# Container Management Service ===================================================
def instanciate_container_from_image(container_name: str, image_id: str, ports: dict):
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
    # Instanciate the container
    container = docker_client.containers.run(
        image=image_id, 
        name=container_name,
        detach=True, 
        ports=ports,
        volumes={
            SOCKET_PATH: {
                'bind': "/zeta/tmp/docker_proxy.sock", 
                'mode': 'ro'
            }
        }
    )
    return container

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
    print("container list : ", list(docker_client.containers.list(all=True)))
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
            print("Removing container:", container_name_or_id)
            docker_client.containers.get(container_name_or_id).remove()
        except:
            print("Forcefully Removing container:", container_name_or_id)
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
            print("Can't remove container: ", name)
            continue
    return removed