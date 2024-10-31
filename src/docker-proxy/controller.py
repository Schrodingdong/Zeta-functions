from fastapi import FastAPI
from pydantic import BaseModel
from enum import Enum

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
            "containerId": container.id
        }
    except:
        return {
            "status": "Error",
            "message": "Error retrieving the container",
            "containerId": id
        }

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
            return_message["status"] = "Error"
            return_message["message"] = "Error ran the container"
    elif state == ContainerLifecycleMethods.STOP.name :
        try:
            docker_service.stop_container(container_id)
            return_message["status"] = "Success"
            return_message["message"] = "Sucessfully stopped the container"
        except:
            return_message["status"] = "Error"
            return_message["message"] = "Error stopping the container"
    elif state == ContainerLifecycleMethods.RESTART.name :
        try:
            docker_service.restart_container(container_id)
            return_message["status"] = "Success"
            return_message["message"] = "Sucessfully restarted the container"
        except:
            return_message["status"] = "Error"
            return_message["message"] = "Error restarting the container"
    elif state == ContainerLifecycleMethods.REMOVE.name :
        try:
            docker_service.remove_container(container_id)
            return_message["status"] = "Success"
            return_message["message"] = "Sucessfully removed the container"
        except:
            return_message["status"] = "Error"
            return_message["message"] = "Error removing the container"
    if len(return_message) == 0:
        return_message["status"] = "Error"
        return_message["message"] = "Unrecognized lifecycle command: " + state
        return_message["containerData"] = None
    else:
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

class ContainerInstanceParameters(BaseModel):
    container_name: str
    cmd: str
    func: str
@app.post("/container")
def instanciate_container(params: ContainerInstanceParameters):
    try:
        container_id = docker_service.instanciate_container(
            container_name= params.container_name,
            cmd= params.cmd if len(params.cmd) != 0 else "",
            function = params.func
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
        print(err)
        return {
            "status": "ERROR",
            "message": "Error starting the container: ",
            "containerData": None
        }


@app.delete("/container/prune")
def prune_containers():
    removed_containers = docker_service.prune_containers()
    return {
        "status": "REMOVED",
        "message": "Removed " +  str(len(removed_containers)) + " containers",
        "containerList": removed_containers
    }