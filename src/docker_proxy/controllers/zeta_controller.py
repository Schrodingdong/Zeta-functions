from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
import services.docker_service as docker_service
import services.zeta_service as zeta_service
from datetime import timedelta, datetime
import requests, time, json, threading

# Initialize Router ====================================================
router = APIRouter()
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
    try:
        await zeta_service.create_zeta(zeta_name, file)
        return {
            "status": "success",
            "message": "successfully created the zeta function '" + zeta_name + "'"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unable to create the zeta function '" + zeta_name + "': " + str(e))

@router.post("/run/{zeta_name}")
async def run_function(zeta_name: str, params: dict = {}):
    """
    Start the function and proxy the request to it.
    """
    # Proxy the request to the zeta
    if(not zeta_service.is_zeta_up(zeta_name)):
        container_hostname = zeta_service.cold_start_zeta(zeta_name)
    else:
        container_hostname = zeta_service.warm_start_zeta(zeta_name)
    # Proxy the request to the zeta
    try:
        print("proxy the request", container_hostname+"/run")
        response = requests.post(
            url=container_hostname+"/run", 
            data=json.dumps(params)
        )
        content = response.content.decode()
        return {"status": "Success", "response": json.loads(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))