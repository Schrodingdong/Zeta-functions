from user.zeta import zetaHandler
from fastapi import FastAPI, Request
from pathlib import Path
from zeta_types import *
import logging
import json
import os

app = FastAPI()
logger = logging.getLogger(__name__)
os.makedirs('./log', exist_ok=True)
logging.basicConfig(
    filename='./log/zeta.log',
    encoding='utf-8',
    level=logging.DEBUG,
    format= '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

@app.post("/")
async def post(request: Request):
    logger.info(request.client)
    
    # Initialize event and context
    event = {
        "queryParams": dict(request.query_params),
        "body": await request.json()
    }
    context = {}
    logger.info(f"event: {event}")
    logger.info(f"context: {context}")
    
    # Create response
    response = {}
    try:
        data = ZetaHandlerResponse.model_validate(zetaHandler(event, context))
        logger.info("Handler data successfully validated on handler response schema")
        response = {
            "status": "SUCCESS",
            "data": json.loads(data.body)
        }
    except Exception as e:
        err = f"Error running the zeta: {e}"
        logger.exception(err)
        response = {
            "status": "ERROR",
            "message":  err
        }
    return response

