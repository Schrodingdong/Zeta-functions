from fastapi import FastAPI, HTTPException
import socket
import time
import importlib.util
import os 
import json

# Heartbeat Definition =============================================
SOCKET_DIR = os.path.join(os.getcwd(), "tmp")
SOCKET_PATH = os.path.join(SOCKET_DIR, "docker_proxy.sock")
def send_heartbeat():
    print("Sending heartbeat")
    try:
        container_id = os.environ['HOSTNAME']
        container_meta = {"containerId": container_id, "timestamp": time.time()}
        # Connect to the Unix socket
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_socket.connect(SOCKET_PATH)
        # Send heartbeat
        try:
            meta_bytes = json.dumps(container_meta).encode("utf-8")
            client_socket.sendall(meta_bytes)
            print(f"[HEARTBEAT] - Heartbeat sent")
        finally:
            client_socket.close()
    except Exception as e:
        print(f"[HEARTBEAT] - Failed to send heartbeat: {e}")

app = FastAPI()

@app.get("/is-running")
def is_running():
    return {
        "status": "UP",
        "timestamp": time.time()
    }

@app.post("/run")
def run_handler(params: dict = {}):
    try:
        print("python_runner params:",params)
        # Define the path to handler.py
        handler_path = os.path.join("handler", "handler.py")
        
        # Load the handler module dynamically
        spec = importlib.util.spec_from_file_location("handler", handler_path)
        handler_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(handler_module)
        
        # Call main_handler if it exists in handler.py
        if hasattr(handler_module, "main_handler"):
            response = handler_module.main_handler(params)
            send_heartbeat()
            return response
        else:
            raise HTTPException(status_code=404, detail="main_handler function not found in handler.py")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))