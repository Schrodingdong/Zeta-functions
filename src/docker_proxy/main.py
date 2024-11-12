from contextlib import asynccontextmanager
from fastapi import FastAPI
# from controllers import container_controller
from controllers import zeta_controller
from services.zeta import zeta_environment, zeta_service, zeta_metadata
import threading
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup logger
    logging.basicConfig(
        format='%(asctime)s %(levelname)s [%(name)s.%(funcName)s] : %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        filename='docker_proxy.log',
        encoding='utf-8',
        level=logging.INFO
    )
    # Setup zeta environment
    logger.info("Setup env")
    global_network = zeta_environment.setup_environment()
    # Start heartbeat thread
    logger.info("starting hearbeat thread ...")
    heartbeat_thread = threading.Thread(
        target=zeta_metadata.accept_heartbeat_connection,
        daemon=True
    )
    heartbeat_thread.start()
    # Start termination thread
    logger.info("starting idle termination thread ...")
    container_termination_thread = threading.Thread(
        target=zeta_metadata.terminate_idle_containers,
        daemon=True
    )
    container_termination_thread.start()
    yield
    # Cleanup running zetas
    logger.info("Pre-shutdown cleanup ...")
    zeta_service.exterminate_all_zeta()
    # Cleanup zeta environment
    logger.info("clearing up env ...")
    zeta_environment.clean_environment(global_network)

# Define fastapi app
app = FastAPI(lifespan=lifespan)

# Register routers
# app.include_router(container_controller.router, prefix="/container")
app.include_router(zeta_controller.router, prefix="/zeta")
