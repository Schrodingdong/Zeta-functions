from contextlib import asynccontextmanager
from fastapi import FastAPI
from controllers import container_controller
from controllers import zeta_controller
from services.zeta import zeta_environment, zeta_service
import threading
import socket
import os
import json
import logging

logger = logging.getLogger(__name__)

# Start heartbeat check thread
SOCKET_DIR = os.path.join(os.getcwd(), "src/docker_proxy/tmp")  # synced with the runner's main.py
SOCKET_PATH = os.path.join(SOCKET_DIR, "docker_proxy.sock")  # synced with the runner's main.py
def accept_heartbeat_connection():
    """
    Heartbeat implementation using sockets.
    """
    # Clean up the socket file if it already exists
    if not os.path.isdir(SOCKET_DIR):
        os.mkdir(SOCKET_DIR)
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)
    # Create / bind the Unix socket
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(SOCKET_PATH)
    server_socket.listen(1)
    try:
        while True:
            connection, client_address = server_socket.accept()
            try:
                # Receive and process data
                while data := connection.recv(1024):
                    meta = json.loads(data.decode())
                    logger.info(f"HEARTBEAT - Heartbeat received: {meta}")
                    zeta_controller.heartbeat_check(meta)
            finally:
                connection.close()
    except KeyboardInterrupt:
        logger.info("Hearbeat socket shutting down")
    finally:
        server_socket.close()
        os.remove(SOCKET_PATH)

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
    heartbeat_thread = threading.Thread(target=accept_heartbeat_connection, daemon=True)
    heartbeat_thread.start()
    logger.info("start hearbeat thread")
    # Start termination thread
    container_termination_thread = threading.Thread(target=zeta_controller.terminate_idle_containers, daemon=True)
    container_termination_thread.start()
    logger.info("start idle termination thread")
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
app.include_router(container_controller.router, prefix="/container")
app.include_router(zeta_controller.router, prefix="/zeta")
