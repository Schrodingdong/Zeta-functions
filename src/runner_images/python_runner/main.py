from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import importlib.util
import os 

app = FastAPI()

@app.get("/run")
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
            return {"status": "success", "response": response}
        else:
            raise HTTPException(status_code=404, detail="main_handler function not found in handler.py")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))