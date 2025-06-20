from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class LogStatus(Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


class RetryMechanism(Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    CONSTANT = "constant"


def log_to_dict(log: "Log") -> dict:
    """Convert a Log instance to a dictionary with proper enum handling"""
    return {
        "status": log.status.value if log.status else None,
        "input": log.input,
        "output": log.output,
        "max_retries": log.max_retries,
        "retry_method": (
            log.retry_mechanism.value if log.retry_mechanism else None
        ),
        "timestamp": log.timestamp.replace(tzinfo=timezone.utc).isoformat() if log.timestamp else None,
    }


@dataclass
class Log:
    status: LogStatus
    input: Optional[dict] = None
    output: Optional[dict] = None
    max_retries: Optional[int] = None
    retry_mechanism: Optional[RetryMechanism] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        """Convert Log to a dictionary for JSON serialization"""
        return log_to_dict(self)


@dataclass
class Response:
    status_code: int
    payload: Optional[dict] = None

    def to_dict(self):
        return {
            "status_code": self.status_code,
            "payload": (self.payload if self.payload is not None else {}),
        }


class EndureException(Exception):
    def __init__(self, status_code: int, output: any):
        self.output = output
        self.status_code = status_code


@dataclass
class ErrorResponse:
    output: any
