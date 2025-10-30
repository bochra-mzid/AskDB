from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    query: Optional[str] = None
    response: str
