from contextlib import asynccontextmanager
from fastapi import FastAPI
from controllers import container_controller
from controllers import zeta_controller 
from services import  zeta_service
import threading
import socket
import os
import json

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
            print("[SOCKET CONNECTION] - waiting for connection...")
            connection, client_address = server_socket.accept()
            try:
                print(f"[SOCKET CONNECTION] - Connection established.")
                # Receive and process data
                while data := connection.recv(1024):
                    meta = json.loads(data.decode())
                    print(f"[SOCKET CONNECTION] - Received: {meta}")
                    zeta_controller.heartbeat_check(meta)
            finally:
                connection.close()
    except KeyboardInterrupt:
        print("[SOCKET CONNECTION] - Shutting down.")
    finally:
        server_socket.close()
        os.remove(SOCKET_PATH)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start heartbeat thread
    heartbeat_thread = threading.Thread(target=accept_heartbeat_connection)
    heartbeat_thread.start()
    # Start 
    container_termination_thread = threading.Thread(target=zeta_controller.terminate_idle_containers, daemon=True)
    container_termination_thread.start()
    yield
    # Cleanup running zetas
    zeta_service.prune_zeta()

# Define fastapi app
app = FastAPI(lifespan=lifespan)

# Register routers
app.include_router(container_controller.router, prefix="/container")
app.include_router(zeta_controller.router, prefix="/zeta")