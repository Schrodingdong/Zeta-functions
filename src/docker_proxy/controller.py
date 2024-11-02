from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from enum import Enum
import requests
import json

import service as docker_service


# Type definition ===========================
class ContainerLifecycleMethods(Enum):
    STOP = 0
    RESTART = 1
    RUN = 2 
    REMOVE = 3
class LifecycleMethod(BaseModel):
    state: str



# Endpoint definition ===========================
app = FastAPI()
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
    container = docker_service.get_container(container_id)
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