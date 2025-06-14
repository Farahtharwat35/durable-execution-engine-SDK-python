
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum



class LogStatus(Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"

class RetryMechanism(Enum):
    EXPONENTIAL = "exponential"
    LINEAR    = "linear"
    CONSTANT   = "constant"

@dataclass
class Log():
    status: LogStatus
    input:Optional[dict] = None
    output: Optional[dict] = None
    max_retries: Optional[int] = None
    retry_method: Optional[RetryMechanism] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
@dataclass
class Response():
    status: int
    payload: Optional[dict] = None

    def to_dict(self):
        return {
            "status": self.status,
            "payload": self.payload if self.payload is not None else {}
        }

class EndureException(Exception):
    def __init__(self,status_code: int , output:any):
        self.output = output
        self.status_code = status_code

@dataclass
class ErrorResponse():
    output: any 

