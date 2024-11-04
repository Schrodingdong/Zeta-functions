from contextlib import asynccontextmanager
from fastapi import FastAPI
from controllers import container_controller
from controllers import zeta_controller 
import threading

# Start heartbeat check thread
@asynccontextmanager
async def lifespan(app: FastAPI):
    heartbeat_thread = threading.Thread(target=zeta_controller.terminate_idle_containers, daemon=True)
    heartbeat_thread.start()
    yield

# Define fastapi app
app = FastAPI(lifespan=lifespan)

# Register routers
app.include_router(container_controller.router, prefix="/container")
app.include_router(zeta_controller.router, prefix="/zeta")