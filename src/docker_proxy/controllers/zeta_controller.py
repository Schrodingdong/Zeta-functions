from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
import service as docker_service
import requests, time, json, threading
from datetime import timedelta, datetime

# Initialize Router ====================================================
router = APIRouter()

# Utils ================================================================
def is_zeta_up(zeta_name: str):
    # Checks if the container is running
    if not docker_service.is_container_running(zeta_name):
        print("Zeta container is not running")
        return False
    # Checks if the app has successfully started
    container = docker_service.get_container(zeta_name)
    ports = container.ports["8000/tcp"][0]
    host_ip = ports["HostIp"]
    host_port = ports["HostPort"]
    host_name = "http://" + host_ip + ":" + host_port
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
    image_list = docker_service.retrieve_images()
    for image in image_list:
        image_tags = image.tags
        for tag in image_tags:
            if zeta_name in tag:
                return image
    return None


# Heartbeat check  ===============================================
class HeartbeatMeta(BaseModel):
    containerId: str
    timestamp: float 

container_last_activity = {}
lock = threading.Lock()
IDLE_TIMEOUT = timedelta(seconds=30)

def terminate_idle_containers():
    while True:
        with lock:
            print(list(container_last_activity.items()))
            for container_id, last_activity in list(container_last_activity.items()):
                if datetime.now() - last_activity > IDLE_TIMEOUT:
                    try:
                        docker_service.stop_container(container_id)
                        docker_service.remove_container(container_id)
                        del container_last_activity[container_id]
                        print(f"Terminated idle container {container_id}")
                    except Exception as e:
                        print(f"Error terminating container {container_id}: {e}")
        time.sleep(15)

# Endpoints ============================================================
@router.post("/heartbeat")
async def heartbeat_check(meta: HeartbeatMeta):
    container_id = meta.containerId
    if container_id:
        container = docker_service.get_container(container_id)
        if container.name == container_id or container.id == container_id or container.short_id == container_id:
            with lock:
                container_last_activity[container.id] = datetime.now()

@router.post("/create/{zeta_name}")
async def create_zeta(zeta_name: str, file: UploadFile = File(...)):
    # Retrieve old images linked to the name:
    old_images = docker_service.retrieve_images_from_prefix(zeta_name)
    # Shutdown any up containers with those images
    try:
        for image in old_images:
            old_containers = docker_service.get_containers_of_image(image.id)
            for container in old_containers:
                docker_service.remove_container(container.id)
    except:
        print("No container found for", zeta_name)
    # Delete old related images
    docker_service.delete_images_from_prefix(zeta_name)

    # Read the file and extract the handler content
    try:
        file_data = await docker_service.process_file(file)
        if file_data == None:
            raise Exception("Error reading the file")
        func = file_data["content"]
    except:
        raise HTTPException(status_code=500, detail="Error reading file data.")
    # Generate the docker file
    try:
        runner_image_name = docker_service.buildRunnerImage(func, zeta_name)
        if runner_image_name:
            return {
                "status": "Success",
                "message": "Successfully created the zeta function.",
                "runnerImageName": runner_image_name
            }
        else:
            raise Exception("Error buidling runner image.")
    except:
        raise HTTPException(status_code=500, detail="Error buidling runner image.")

@router.post("/run/{zeta_name}")
async def run_function(zeta_name: str, params: dict = {}):
    """
    Proxy to run the function inside the container
    """
    if(not is_zeta_up(zeta_name)):
        # Cold start
        runner_image = retrieve_runner_image(zeta_name)
        if runner_image == None:
            raise HTTPException(status_code=500, detail="Unable to run the zeta function '" + zeta_name + "'")
        container = docker_service.instanciate_container_from_image(
            container_name=zeta_name,
            image_id=runner_image.id
        )
    # Hot Start
    container = docker_service.get_container(zeta_name)
    ports = container.ports["8000/tcp"][0]
    host_ip = ports["HostIp"]
    host_port = ports["HostPort"]
    host_name = "http://" + host_ip + ":" + host_port
    # Wait until the container is up
    TIMEOUT = 60
    start_time = time.time()
    while not is_zeta_up(zeta_name):
        if time.time() - start_time > TIMEOUT:
            raise HTTPException(status_code=500, detail="Zeta function is not up, exited due to timeout")
        time.sleep(1)
    # Proxy the request to the zeta
    try:
        print("proxy the request", host_name+"/run")
        response = requests.post(
            url=host_name+"/run", 
            data=json.dumps(params)
        )
        content = response.content.decode()
        return {"status": "Success", "response": json.loads(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))