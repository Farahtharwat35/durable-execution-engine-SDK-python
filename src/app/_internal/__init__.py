"""
Internal implementation details. Do not import directly.
This module is for internal use by app.py, service.py, and workflow_context.py only.
"""

import inspect
import os
import sys

from .internal_client import InternalEndureClient
from .service_registry import ServiceRegistry
from .utils import validate_retention_period
from .workflow import Workflow


def _is_testing():
    # Skipping during pytest or unittest runs
    return "PYTEST_CURRENT_TEST" in os.environ or any(
        "pytest" in arg or "unittest" in arg for arg in sys.argv
    )


def _check_caller():
    if _is_testing():
        return

    frame = inspect.currentframe().f_back.f_back
    caller_module = frame.f_globals.get("__name__", "")

    allowed_modules = {
        "app.app",
        "app.service",
        "app.workflow_context",
    }

    if caller_module not in allowed_modules:
        raise ImportError(
            f"The '_internal' module cannot be imported from '{caller_module}'. "
            "It is only for use by app.py, service.py, and workflow_context.py"
        )


_check_caller()

__all__ = [
    "InternalEndureClient",
    "ServiceRegistry",
    "validate_retention_period",
    "Workflow",
]
