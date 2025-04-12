from pydantic import BaseModel
from typing import Optional, Dict


class Execution(BaseModel):
    execution_id: Optional[str] = None  
    status: Optional[str] = None  
    output: Optional[Dict] = None  
    last_log: Optional[str] = None  
