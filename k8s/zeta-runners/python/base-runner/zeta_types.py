from pydantic import BaseModel
from typing import Any

class Event(BaseModel):
    queryParams: dict
    body: Any
    
class Context(BaseModel):
    zetaName: str

class ZetaHandlerResponse(BaseModel):
    statusCode: int
    headers: dict[str, str]
    body: str