from fastapi import File, UploadFile
from .. import docker_service
import subprocess
import tempfile
import logging
import uuid
import time
import os


logger = logging.getLogger(__name__)


def build_zeta_runner_image(function: str, zeta_name: str = ""):
    """
    Build the runner image `<zeta_name>-zeta-runner-image-<uuid>:latest`
    from the base image `python-base-runner:latest`

    Attributes
    ---
    - function: str
        The handler file strigified, to be baked in the runner image.
        (TODO: Make sure it can handle multi-file support)
    - zeta_name: str
        The Zeta function to be deployed
    """
    BASE_RUNNER = "python-base-runner:latest"
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Define file paths
        function_file_path = os.path.join(tmpdirname, "function.py")
        dockerfile_path = os.path.join(tmpdirname, "Dockerfile")
        # Write the function to a Python file
        with open(function_file_path, "w") as f:
            f.write(function)
        # Generate a Dockerfile
        dockerfile_content = f"""
        FROM {BASE_RUNNER}
        WORKDIR /zeta
        COPY function.py /zeta/handler/handler.py
        """
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)
        # Build the Docker image
        image_name = f"{zeta_name}-runner-image-{uuid.uuid4()}"
        try:
            docker_service.build_image(
                image_name=image_name,
                dockerfile_path=tmpdirname
            )
        except subprocess.CalledProcessError as e:
            logger.error(e)
            raise RuntimeError("Error occurred while building the Docker image:")
    # Return the image name
    return image_name


async def process_file(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")
    return {"filename": file.filename, "content": text}


def retrieve_runner_image(zeta_name: str):
    """
    Retrieve Image runner from the zeta function name
    """
    image_list = docker_service.list_images()
    for image in image_list:
        image_tags = image.tags
        for tag in image_tags:
            if tag.startswith(zeta_name):
                return image
    return None


def retrieve_container_hostname(container):
    """
    Retrieve the container hostname in the form:
    - `http://{host_ip}:{host_port}`
    """
    TIMEOUT = 60
    start_time = time.time()
    while len(container.ports) == 0:
        container = docker_service.get_container(container.name)
        if time.time() - start_time > TIMEOUT:
            raise RuntimeError(
                "Unable to retreive container hostname. Exit due to timeout"
            )
        time.sleep(0.5)
    ports = container.ports["8000/tcp"][0]
    host_ip = ports["HostIp"]
    host_port = ports["HostPort"]
    host_name = f"http://{host_ip}:{host_port}"
    return host_name


async def extract_handler_data(file: UploadFile = File(...)):
    """
    Read the file and extract the handler content.
    """
    try:
        file_data = await process_file(file)
        if file_data is None:
            raise Exception("Error reading the file")
        func = file_data["content"]
    except Exception as e:
        logger.error(e)
        raise RuntimeError("Error reading file data.")
    return func
