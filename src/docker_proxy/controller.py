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
IDLE_TIMEOUT = timedelta(minutes=10)

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

# Middleware definition =========================
@app.middleware("http")
async def update_container_activity(request: Request, call_next):
    x_container_id = request.headers.get("X-Container-ID")
    if x_container_id:
        container = docker_service.get_container(x_container_id)
        if container.name == x_container_id or container.id == x_container_id or container.short_id == x_container_id:
            # Ensures we points to the long Id, whathever X-Container-ID is
            with lock:
                container_last_activity[container.id] = datetime.now()
    response = await call_next(request)
    return response

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
            with lock:
                # Delete it from the container_last_activity list
                try:
                    del container_last_activity[container.id]
                except:
                    print("Unable to delete activity of " + container_id + ", id: "+ container.id)
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

async def process_file(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")
    return {"filename": file.filename, "content": text}

@app.post("/container")
async def instanciate_container(container_name: str, file: UploadFile = File(...)):
    try:
        # Read the file from the request
        file_data = await process_file(file)
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
        with lock:
            container_last_activity[container.id] = datetime.now()
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
        raise HTTPException(status_code=500, detail="Error starting the container: " + container_id)


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
@app.post("/serverless/run/{container_name_or_id}")
def run_function(container_name_or_id: str, params: dict = {}):
    """
    Proxy to run the function inside the container
    """
    try:
        container = docker_service.get_container(container_name_or_id)
        ports = container.ports["8000/tcp"][0]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unable to find container:" + container_name_or_id)
    host_ip = ports["HostIp"]
    host_port = ports["HostPort"]
    url = "http://" + host_ip + ":" + host_port + "/run"
    try:
        response = requests.post(url, data=json.dumps(params))
        content = response.content.decode()
        return {"status": "Success", "response": json.loads(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))