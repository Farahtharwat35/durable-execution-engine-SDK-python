"""
Internal implementation details. Do not import directly.
This module is for internal use by app.py, service.py, and workflow_context.py only.
"""
import inspect
import sys

def _check_caller():
    frame = inspect.currentframe().f_back.f_back
    caller_module = frame.f_globals['__name__']
    allowed_modules = {'app.app', 'app.service', 'app.workflow_context'}
    if caller_module not in allowed_modules:
        raise ImportError(
            f"The '_internal' module cannot be imported from '{caller_module}'. "
            "It is only for use by app.py, service.py, and workflow_context.py"
        )

_check_caller()

from .internal_client import InternalEndureClient
from .service_registry import ServiceRegistry
from .types import (
    LogStatus,
    RetryMechanism,
    Log,
    Response,
    EndureException,
    ErrorResponse
)
from .utils import validate_retention_period
from .workflow import Workflow

__all__ = [
    "InternalEndureClient",
    "ServiceRegistry",
    "LogStatus",
    "RetryMechanism",
    "Log",
    "Response",
    "EndureException",
    "ErrorResponse",
    "validate_retention_period",
    "Workflow"
]
