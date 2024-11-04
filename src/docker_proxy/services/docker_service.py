from docker import DockerClient

DOCKER_SOCK = 'unix://var/run/docker.sock'
DOCKER_HOST = DOCKER_SOCK
DOCKER_PORT = 2373
docker_client = DockerClient(DOCKER_HOST)
container_prefix = "POMS"

# Image Management Service =======================================================
def retrieve_images():
    return docker_client.images.list()

def retrieve_images_from_prefix(prefix: str):
    image_list = docker_client.images.list()
    found_images = []
    for image in image_list:
        for tag in image.tags:
            if prefix in tag:
                found_images.append(image)
                break
    return found_images

def build_image(image_name: str, dockerfile_path:str):
    try:
        docker_client.images.build(tag=image_name, path=dockerfile_path)
    except:
        raise Exception("Unable to build the image '" + image_name + "': "+ dockerfile_path)

def delete_images_from_prefix(prefix: str):
    """
    given a prefix, delete the images that contains it
    """
    image_list = docker_client.images.list()
    for image in image_list:
        for tag in image.tags:
            if prefix in tag:
                try:
                    print("deleting image:", tag)
                    docker_client.images.remove(image=image.id)
                except:
                    print("FORCE deleting image:", tag)
                    docker_client.images.remove(image=image.id, force=True)
                break

# Container Management Service ===================================================
def instanciate_container_from_image(container_name: str, image_id: str):
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
        ports={"8000":9090}
    )
    return container


def instanciate_container(container_name: str, cmd: str, function: str) -> str:
    try:
        if container_name in list(map(lambda x: x.name, docker_client.containers.list(all=True))):
            remove_container(container_name)
        # imageRunnerName = buildRunnerImage(function)
        imageRunnerName = "unknown"
        container = docker_client.containers.run(image=imageRunnerName, name=container_name, command=cmd, detach=True, ports={"8000":9090})
        return container.id
    except Exception as err :
        raise RuntimeError("Unable to create the container: ", err)

def is_container_running(container_name: str):
    container_list_name = list(map(lambda x: x.name, docker_client.containers.list()))
    return container_name in container_list_name

def get_container(name_or_id: str):
    try:
        container = docker_client.containers.get(name_or_id)
        return container
    except Exception as err :
        raise RuntimeError("Unable to retrieve the container: ", err)

def get_containers_of_image(image_id: str):
    container_list = []
    print("container list : ", list(docker_client.containers.list(all=True)))
    for container in list(docker_client.containers.list(all=True)):
        if container.image.id == image_id:
            container_list.append(container)
    return container_list

def restart_container(name_or_id: str):
    try:
        docker_client.containers.get(name_or_id).restart()
    except Exception as err :
        raise RuntimeError("Unable to restart the container of id "+ name_or_id + " : ", err)

def stop_container(name_or_id: str):
    try:
        docker_client.containers.get(name_or_id).stop()
    except Exception as err :
        raise RuntimeError("Unable to stop the container of id", name_or_id, ":", err)

def run_container(name_or_id: str):
    try:
        docker_client.containers.run(name_or_id)
    except Exception as err :
        raise RuntimeError("Unable to run the container of id", name_or_id, ":", err)

def remove_container(name_or_id: str):
    try:
        try:
            print("Removing container:", name_or_id)
            docker_client.containers.get(name_or_id).remove()
        except:
            print("Forcefully Removing container:", name_or_id)
            docker_client.containers.get(name_or_id).remove(force=True)
    except Exception as err :
        raise RuntimeError("Unable to remove the container of id", name_or_id, ":", err)

def prune_containers() -> list:
    removed = []
    for name in list(map(lambda x: x.name, docker_client.containers.list(all=True))):
        try:
            remove_container(name)
            removed.append(name)
        except:
            print("Can't remove container: ", name)
            continue
    return removed

# Utils =======================================================
def prefixContainerName(name):
    return container_prefix + "_" + name