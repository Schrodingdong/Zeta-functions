from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from enum import Enum
import requests
import json

import service as docker_service


# Type definition ==============================
class ContainerLifecycleMethods(Enum):
    STOP = 0
    RESTART = 1
    RUN = 2 
    REMOVE = 3
class LifecycleMethod(BaseModel):
    state: str

# Heartbeat check ===============================
import threading
import time
from datetime import timedelta, datetime

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    heartbeat_thread = threading.Thread(target=terminate_idle_containers, daemon=True)
    heartbeat_thread.start()
    yield

# Fastapi App definition ========================
app = FastAPI(lifespan=lifespan)

# Hearbeat Definition ===========================
class HeartbeatMeta(BaseModel):
    containerId: str
    timestamp: float 

@app.post("/heartbeat")
async def heartbeat_check(meta: HeartbeatMeta):
    container_id = meta.containerId
    if container_id:
        container = docker_service.get_container(container_id)
        if container.name == container_id or container.id == container_id or container.short_id == container_id:
            with lock:
                container_last_activity[container.id] = datetime.now()

# Container Management ===========================
@app.get("/container/{id}")
def get_container(id: str):
    try:
        container = docker_service.get_container(id)
        return {
            "status": "Success",
            "message": "Successfully retrieved the container",
            "containerData": {
                "name": container.name,
                "status": container.status,
                "short_id": container.short_id,
                "id": container.id,
                "image": container.image.id,
                "ports": container.ports,
                "health": container.health
            }
        }
    except:
        raise HTTPException(status_code=500, detail="Error retrieving the container: " + id)

@app.post("/container/manage/{container_id}")
def manage_container(container_id: str, lifecycleMethod: LifecycleMethod):
    state = lifecycleMethod.state
    try:
        container = docker_service.get_container(container_id)
    except:
        raise HTTPException(status_code=500, detail="Error retrieving the container: " + container_id)
    return_message = {}
    if state == ContainerLifecycleMethods.RUN.name :
        try:
            docker_service.run_container(container_id)
            return_message["status"] = "Success"
            return_message["message"] = "Sucessfully ran the container"
        except:
           raise HTTPException(status_code=500, detail="Error running the container: " + container_id)
    elif state == ContainerLifecycleMethods.STOP.name :
        try:
            docker_service.stop_container(container_id)
            return_message["status"] = "Success"
            return_message["message"] = "Sucessfully stopped the container"
        except:
            raise HTTPException(status_code=500, detail="Error stopping the container: " + container_id)
    elif state == ContainerLifecycleMethods.RESTART.name :
        try:
            docker_service.restart_container(container_id)
            return_message["status"] = "Success"
            return_message["message"] = "Sucessfully restarted the container"
        except:
            raise HTTPException(status_code=500, detail="Error restarting the container: " + container_id)
    elif state == ContainerLifecycleMethods.REMOVE.name :
        try:
            docker_service.remove_container(container_id)
            return_message["status"] = "Success"
            return_message["message"] = "Sucessfully removed the container"
            
        except:
            raise HTTPException(status_code=500, detail="Error removing the container: " + container_id)
    if len(return_message) == 0:
        raise HTTPException(status_code=422, detail="Unrecognized lifecycle command: " + state)
    return_message["containerData"] = {
        "name": container.name,
        "status": container.status,
        "short_id": container.short_id,
        "id": container.id,
        "image": container.image.id,
        "ports": container.ports,
        "health": container.health
    }
    return return_message

@app.post("/container")
async def instanciate_container(container_name: str, file: UploadFile = File(...)):
    try:
        # Read the file from the request
        file_data = await docker_service.process_file(file)
        if file_data == None:
            raise Exception("Error reading the file")

        func = file_data["content"]

        # Instanciate container
        container_id = docker_service.instanciate_container(
            container_name= container_name,
            cmd= "",
            function = func
        )
        container = docker_service.get_container(container_id)
        return {
            "status": "RUNNING",
            "message": "Sucessfully started the container of id " + container.short_id,
            "containerData": {
                "name": container.name,
                "status": container.status,
                "short_id": container.short_id,
                "id": container.id,
                "image": container.image.id,
                "ports": container.ports,
                "health": container.health
            }
        }
    except Exception as err:
        print(str(err))
        raise HTTPException(status_code=500, detail="Error starting the container: " + container_name)

@app.delete("/container/prune")
def prune_containers():
    try:
        removed_containers = docker_service.prune_containers()
        return {
            "status": "REMOVED",
            "message": "Removed " +  str(len(removed_containers)) + " containers",
            "containerList": removed_containers
        }
    except:
        raise HTTPException(status_code=500, detail="Error prunning the containers.")

# Zeta function ===================================
@app.post("/zeta/create/{zeta_name}")
async def create_zeta(zeta_name: str, file: UploadFile = File(...)):
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
        return response.status_code == 200
    except:
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

@app.post("/zeta/run/{zeta_name}")
def run_function(zeta_name: str, params: dict = {}):
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
        time.sleep(0.5)
    # Proxy the request to the zeta
    try:
        response = requests.post(
            url=host_name+"/run", 
            data=json.dumps(params)
        )
        content = response.content.decode()
        return {"status": "Success", "response": json.loads(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))