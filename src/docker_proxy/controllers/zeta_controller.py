from fastapi import APIRouter, HTTPException, File, UploadFile, status
from pydantic import BaseModel
from datetime import timedelta, datetime
import services.docker_service as docker_service
import services.zeta_service as zeta_service
import requests, time, json, threading, logging

# Initialize Logger ====================================================
logger = logging.getLogger(__name__)

# Initialize Router ====================================================
router = APIRouter()

# Heartbeat check  =====================================================
container_last_activity = {}
lock = threading.Lock()
IDLE_TIMEOUT = timedelta(seconds=30)

def terminate_idle_containers():
    while True:
        with lock:
            for container_name, last_activity in list(container_last_activity.items()):
                if isinstance(last_activity, float):
                    last_activity = datetime.fromtimestamp(last_activity)
                if datetime.now() - last_activity > IDLE_TIMEOUT:
                    try:
                        # Removing zeta function runner containers
                        docker_service.stop_container(container_name)
                        docker_service.remove_container(container_name)
                        del container_last_activity[container_name]
                        # Removing container meta for zeta
                        zeta_service.delete_zeta_container_metadata(container_name)
                        logger.info(f"Terminated idle zeta runner container {container_name}")
                    except Exception as e:
                        logger.info(f"Error terminating zeta runner container {container_name}: {e}")
        time.sleep(15)

def heartbeat_check(meta: dict):
    container_id = meta["containerId"]
    timestamp = meta["timestamp"]
    if container_id:
        container = docker_service.get_container(container_id)
        if container.name == container_id or container.id == container_id or container.short_id == container_id:
            with lock:
                container_last_activity[container.name] = float(timestamp)
    logger.info(f"Container activity list: {list(container_last_activity.items())}")

# Endpoints ============================================================
@router.get("/meta/")
async def get_all_zeta_metadata():
    logger.info("Retrieving all zeta function metadata ...")
    meta = zeta_service.get_all_zeta_metadata()
    meta_list = []
    for el in meta :
        meta_list.append(meta[el])
    return meta_list

@router.get("/meta/{zeta_name}")
async def get_zeta_metadata(zeta_name: str):
    logger.info(f"Retrieving zeta function metadata for: {zeta_name} ...")
    meta = zeta_service.get_zeta_metadata(zeta_name)
    if len(meta) == 0:
        raise HTTPException(status_code=500, detail=f"Unable to find the zeta function {zeta_name}")
    return meta


@router.post("/create/{zeta_name}")
async def create_zeta(zeta_name: str, file: UploadFile = File(...)):
    logger.info(f"Creating the zeta function: {zeta_name} ...")
    if len(zeta_name) <= 1:
        raise HTTPException(status_code=500, detail=f"Zeta name ('{zeta_name}') length needs to be 2 or more characters in length.")
    try:
        zeta_metadata = await zeta_service.create_zeta(zeta_name, file)
        return {
            "status": "success",
            "message": f"successfully created the zeta function '{zeta_name}'",
            "zetaMetadata": zeta_metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to create the zeta function '{zeta_name}': {str(e)}")

@router.post("/run/{zeta_name}")
async def run_function(zeta_name: str, params: dict = {}):
    """
    Start the function and proxy the request to it.
    """
    logger.info(f"Running the zeta function: {zeta_name} ...")
    # Check if the function exists
    zeta_meta = zeta_service.get_zeta_metadata(zeta_name)
    if len(zeta_meta) == 0:
        raise HTTPException(status_code=404, detail=f"Zeta function {zeta_name} not found.")
    # Start the function
    if(not zeta_service.is_zeta_up(zeta_name)):
        logger.info(f"Cold starting zeta : {zeta_name} ...")
        container_hostname = zeta_service.cold_start_zeta(zeta_name)
    else:
        logger.info(f"starting zeta : {zeta_name} ...")
        container_hostname = zeta_service.warm_start_zeta(zeta_name)
    # Proxy the request to the zeta
    logger.info(f"running zeta : {zeta_name}")
    try:
        response = requests.post(
            url=container_hostname+"/run", 
            data=json.dumps(params)
        )
        content = response.content.decode()
        return {"status": "Success", "response": json.loads(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{zeta_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zeta(zeta_name: str):
    logger.info(f"Deleting the zeta function: {zeta_name} ...")
    try:
        zeta_service.clean_zeta(zeta_name)
    except Exception as e:
        logger.error(f"Failed to delete the zeta function {zeta_name}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while deleting the zeta function.")
