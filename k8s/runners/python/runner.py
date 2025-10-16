from importlib import import_module
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def zeta_runner():
    zeta_module = import_module("handler.handler")
    val = zeta_module.zeta_handler()
    return val
