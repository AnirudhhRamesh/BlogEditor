from typing import List, Optional
from pydantic import BaseModel

class Prompt(BaseModel):
    """
    Represents a prompt for an LLM
    """
    text: str
    model: str

class SimpleResponse(BaseModel):
    """
    Represents a simple response from an LLM
    """
    response: str

class ListResponse(BaseModel):
    """
    Represents a list response from an LLM
    """
    response: List[str]