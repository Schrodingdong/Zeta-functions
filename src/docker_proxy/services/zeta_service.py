from fastapi import File, UploadFile
import services.docker_service as docker_service 
import services.dns_service as dns_service
import subprocess
import tempfile
import requests
import uuid
import time
import os

# Create the function
async def create_zeta(zeta_name: str, file: UploadFile = File(...)):
    """
    Create the zeta function. 
    ...
    Attributes
    ---
    zeta_name : str
        Zeta function name.
    file : fastapi.UploadFile
        File to use to create the runner image.
    """
    # Cleaning old zeta image
    try:
        print("Cleaning old zeta images")
        clean_old_zeta(zeta_name)
    except Exception as e:
        raise RuntimeError("Error cleaning old zeta function: " + str(e))
    try:
        print("exctracting handler data")
        handler_content = await extract_handler_data(file)
    except Exception as e:
        raise RuntimeError("Error reading handler and extracting content: " + str(e))
    print("Build runner image")
    runner_image_name = build_zeta_runner_image(handler_content, zeta_name)
    if not runner_image_name:
        raise RuntimeError("Error buidling runner image.")
    print("Generating zeta metadata")
    meta = create_zeta_metadata(zeta_name)
    return meta

def clean_old_zeta(zeta_name: str):
    """
    Clean old zeta files, images, containers and metadata. The steps to do so are as follow :
    - Shutdown any up containers with old related images
    - Delete old related images

    Attributes 
    ---
    - zeta_image: str
    """
    # Shutdown any up containers with old related images
    print("[ZETA CLEANUP] - cleaning up old zeta containers")
    old_images = docker_service.get_images_from_prefix(zeta_name)
    try:
        for image in old_images:
            old_containers = docker_service.get_containers_of_image(image.id)
            for container in old_containers:
                docker_service.remove_container(container.id)
    except:
        print("No container found for", zeta_name)
    # Delete old related images
    print("[ZETA CLEANUP] - cleaning up old zeta image runner")
    try:
        docker_service.delete_images_from_prefix(zeta_name)
    except Exception as e:
        raise RuntimeError("Error deleting images from prefix " + zeta_name + " : " + str(e))
    # Delete zeta metadata
    print("[ZETA CLEANUP] - Deleting old zeta_metadata")
    delete_zeta_metadata(zeta_name)

async def extract_handler_data(file: UploadFile = File(...)):
    # Read the file and extract the handler content
    try:
        file_data = await process_file(file)
        if file_data == None:
            raise Exception("Error reading the file")
        func = file_data["content"]
    except:
        raise RuntimeError("Error reading file data.")
    return func

def build_zeta_runner_image(function: str, zeta_name:str = ""):
    """
    Build the runner image `<zeta_name>-zeta-runner-image-<uuid>:latest` from the base image `python-base-runner:latest`

    Attributes
    ---
    - function: str
        The handler file strigified, to be baked in the runner image. (TODO: Make sure it can handle multi-file support)
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
            docker_service.build_image(image_name=image_name, dockerfile_path=tmpdirname)
        except subprocess.CalledProcessError as e:
            print("Error occurred while building the Docker image:", e)
            return None
    # Return the image name
    return image_name

async def process_file(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")
    return {"filename": file.filename, "content": text}

# Run the function
def cold_start_zeta(zeta_name:str):
    """
    Cold start the zeta function

    Attributes
    ---
    - zeta_name: str
    """
    runner_image = retrieve_runner_image(zeta_name)
    if runner_image == None:
        raise RuntimeError("Unable to run the zeta function '" + zeta_name + "'")
    try:
        # Get dynamic port and set it for the zeta in the DNS
        host_port = dns_service.retrieve_dynamic_port()
        dns_service.set_zeta_port(zeta_name, host_port)
        # Instanciate the container
        container = docker_service.instanciate_container_from_image(
            container_name=zeta_name,
            image_id=runner_image.id,
            ports={"8000":host_port} # 8000 is the open container port
        )
        # Update container metadata
        update_zeta_container_metadata(zeta_name)
    except:
        raise RuntimeError("Unable to run the zeta function '" + zeta_name + "'")
    container_hostname = retrieve_container_hostname(container)
    # Wait until the container is up
    TIMEOUT = 60
    start_time = time.time()
    while not is_zeta_up(zeta_name):
        if time.time() - start_time > TIMEOUT:
            raise RuntimeError("Zeta function is not up, exited due to timeout")
        time.sleep(1)
    return container_hostname

def warm_start_zeta(zeta_name: str):
    """
    Warm start the zeta function

    Attributes
    ---
    - zeta_name: str
    """
    try: 
        container = docker_service.get_container(zeta_name)
    except:
        raise RuntimeError("Unable to run the zeta function '" + zeta_name + "'")
    container_hostname = retrieve_container_hostname(container)
    # Wait until the container is up
    TIMEOUT = 60
    start_time = time.time()
    while not is_zeta_up(zeta_name):
        if time.time() - start_time > TIMEOUT:
            raise RuntimeError("Zeta function is not up, exited due to timeout")
        time.sleep(1)
    return container_hostname

def retrieve_container_hostname(container):
    TIMEOUT = 60
    start_time = time.time()
    while(len(container.ports) == 0):
        container = docker_service.get_container(container.name)
        if time.time() - start_time > TIMEOUT:
            raise RuntimeError("Unable to retreive container hostname. Exit due to timeout")
        time.sleep(0.5) 
    ports = container.ports["8000/tcp"][0]
    host_ip = ports["HostIp"]
    host_port = ports["HostPort"]
    host_name = "http://" + host_ip + ":" + host_port
    return host_name

# utils
def is_zeta_up(zeta_name: str):
    """
    Checks if the zeta function is up and running. This verification is done in 2 steps:
    - Verify that the container is up and in `RUNNING` state.
    - Verify if the zeta application inside the container has started.

    Attributes
    ---
    - zeta_name: str
    """
    # Checks if the container is running
    if not docker_service.is_container_running(zeta_name):
        print("Zeta container is not running")
        return False
    # Checks if the app has successfully started
    container = docker_service.get_container(zeta_name)
    host_name = retrieve_container_hostname(container)
    try:
        response = requests.get(host_name+"/is-running")
        print("Zeta container is UP")
        return response.status_code == 200
    except:
        print("Zeta container is not UP")
        return False

def retrieve_runner_image(zeta_name: str):
    """
    Retrieve Image runner from the zeta function name
    """
    image_list = docker_service.list_images()
    for image in image_list:
        image_tags = image.tags
        for tag in image_tags:
            if zeta_name in tag:
                return image
    return None

# Zeta metadata
# Zeta metadata should be tightly linked to the current deployment. a change in the functions means a redeployment, therfore deleting and re creating the metadata
zeta_meta = {}

def get_all_zeta_metadata():
    return zeta_meta

def get_zeta_metadata(zeta_name: str):
    if zeta_name not in zeta_meta:
        return {}
    return {
        zeta_name: zeta_meta[zeta_name]
    }

def update_zeta_container_metadata(zeta_name: str):
    try:
        container = docker_service.get_container(zeta_name)
    except:
        raise RuntimeError(f"Can't find zeta container runner: {zeta_name}")
    zeta_meta[zeta_name]["runnerContainer"].append(
        {
            "containerName": container.name,
            "containerId": container.id,
            "containerPorts": container.ports
        }
    )

def create_zeta_metadata(zeta_name: str):
    runner_image_list = docker_service.get_images_from_prefix(zeta_name)
    if len(runner_image_list) > 1:
        raise RuntimeError(f"Multiple runners found for zeta {zeta_name} : {len(runner_image_list)}")
    elif len(runner_image_list) == 0:
        raise RuntimeError(f"No runners found for zeta: {zeta_name}")
    runner_image = runner_image_list[0]
    meta = {
        "runnerImage": {
            "imageId": runner_image.id,
            "tags": runner_image.tags
        },
        "runnerContainer": [],
        "createdAt": time.time(),
    }
    zeta_meta[zeta_name] = meta
    return meta

def delete_zeta_metadata(zeta_name: str):
    if zeta_name not in zeta_meta:
        return
    del zeta_meta[zeta_name] 