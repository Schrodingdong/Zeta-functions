from fastapi import APIRouter, HTTPException, File, UploadFile, status
from services.zeta import zeta_service, zeta_metadata
import logging


logger = logging.getLogger(__name__)
router = APIRouter()


def check_if_zeta_exists_or_404(zeta_name: str):
    # Check if the zeta exists
    is_zeta_created = zeta_service.is_zeta_created(zeta_name)
    if not is_zeta_created:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zeta function '{zeta_name}' not found."
        )


@router.get("/meta")
async def get_all_zeta_metadata():
    logger.info("Retrieving all zeta function metadata ...")
    meta = zeta_metadata.get_all_zeta_metadata()
    return meta


@router.get("/meta/{zeta_name}")
async def get_zeta_metadata(zeta_name: str):
    logger.info(f"Retrieving zeta function metadata for: {zeta_name} ...")
    # Check if the zeta exists
    check_if_zeta_exists_or_404(zeta_name)
    # retrieve zeta metadata
    meta = zeta_metadata.get_zeta_metadata(zeta_name)
    if len(meta) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unable to find the zeta function {zeta_name}"
        )
    return meta


@router.post("/create/{zeta_name}", status_code=status.HTTP_201_CREATED)
async def create_zeta(zeta_name: str, file: UploadFile = File(...)):
    logger.info(f"Creating the zeta function: {zeta_name} ...")
    # Check name length
    if len(zeta_name) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Zeta name ('{zeta_name}') length needs to be 2 or more characters in length."
        )
    # Create the zeta
    try:
        zeta_metadata = await zeta_service.create_zeta(zeta_name, file)
        return {
            "status": "success",
            "message": f"successfully created the zeta function '{zeta_name}'",
            "zetaMetadata": zeta_metadata
        }
    except Exception as e:
        logger.error(f"An Exception has occured: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to create the zeta '{zeta_name}'"
        )


@router.post("/run/{zeta_name}")
async def run_function(zeta_name: str, params: dict = {}):
    """
    Start the function and proxy the request to it.
    """
    logger.info(f"Running the zeta function: {zeta_name} ...")
    # Check if the zeta exists
    check_if_zeta_exists_or_404(zeta_name)
    # Cold start the zeta if it is not up
    if not zeta_service.is_zeta_up(zeta_name):
        zeta_service.cold_start_zeta(zeta_name)
    # Run the zeta
    try:
        json_content = zeta_service.run_zeta(zeta_name, params)
        return {"status": "Success", "response": json_content}
    except Exception as e:
        logger.error(f"An Exception has occured: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while running the zeta '{zeta_name}'"
        )


@router.delete("/{zeta_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zeta(zeta_name: str):
    logger.info(f"Deleting the zeta function: {zeta_name} ...")
    # Check if the zeta exists
    check_if_zeta_exists_or_404(zeta_name)
    # Delete the zeta
    try:
        zeta_service.delete_zeta(zeta_name)
    except Exception as e:
        logger.error(f"An Exception has occured: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the zeta '{zeta_name}'"
        )
