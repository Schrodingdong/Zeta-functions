from fastapi import FastAPI, HTTPException
import requests
import time
import importlib.util
import os 
import json

# Heartbeat Definition =============================================
def send_heartbeat():
    print("Sending heartbeat")
    try:
        container_id = os.environ['HOSTNAME']
        container_meta = {"containerId": container_id, "timestamp": time.time()}
        host = "http://host.docker.internal" # issue with docker on linux
        port = "8000"
        path = "/zeta/heartbeat"
        url = host+":"+port+path
        print("sending heartbeat to", url)
        response = requests.post(
            url=url, 
            data=json.dumps(container_meta)
        )
        print(f"Heartbeat sent: {response.status_code}")
    except Exception as e:
        print(f"Failed to send heartbeat: {e}")

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
            # TODO fix heartbeat
            # send_heartbeat()
            return response
        else:
            raise HTTPException(status_code=404, detail="main_handler function not found in handler.py")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))