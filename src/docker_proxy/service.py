from docker import DockerClient
import os
import tempfile
import subprocess
import uuid
import requests

DOCKER_SOCK = 'unix://var/run/docker.sock'
DOCKER_HOST = DOCKER_SOCK
DOCKER_PORT = 2373
docker_client = DockerClient(DOCKER_HOST)
container_prefix = "POMS"

def prefixContainerName(name):
    return container_prefix + "_" + name

# Build the runner image (python_runner:latest) from the base image (python_base_runner:latest)
def buildRunnerImage(function: str):
    INSTANCE_IMAGE_PATH = "./instance_images"
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Define file paths
        function_file_path = os.path.join(tmpdirname, "function.py")
        dockerfile_path = os.path.join(tmpdirname, "Dockerfile")

        # Write the function to a Python file
        with open(function_file_path, "w") as f:
            f.write(function)

        # Generate a Dockerfile
        dockerfile_content = """
        FROM python-base-runner:latest
        WORKDIR /zeta
        COPY function.py /zeta/handler/handler.py
        """
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)

        # Build the Docker image
        image_name = f"runner_image_{uuid.uuid4()}"
        try:
            docker_client.images.build(tag=image_name, path=tmpdirname)
        except subprocess.CalledProcessError as e:
            print("Error occurred while building the Docker image:", e)
            return None

    # Return the image name
    return image_name

# Container Management Service ===================================================
def instanciate_container(container_name: str, cmd: str, function: str) -> str:
    try:
        if container_name in list(map(lambda x: x.name, docker_client.containers.list(all=True))):
            remove_container(container_name)
        imageRunnerName = buildRunnerImage(function)
        container = docker_client.containers.run(image=imageRunnerName, name=container_name, command=cmd, detach=True, ports={"8000":9090})
        return container.id
    except Exception as err :
        raise RuntimeError("Unable to create the container: ", err)

def get_container(name_or_id: str):
    try:
        container = docker_client.containers.get(name_or_id)
        return container
    except Exception as err :
        print(err)
        raise RuntimeError("Unable to retrieve the container: ", err)

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

# Serverlessy ==================================================
def run_function(container_id: str):
    # container = get_container(container_id)
    # send request to retrieve the lambda result
    if 'docker.sock' in DOCKER_HOST:
        lambda_output = requests.get("localhost:9999/run")
    else:
        lambda_output = requests.get(DOCKER_HOST + "9999/run")
    return lambda_output
