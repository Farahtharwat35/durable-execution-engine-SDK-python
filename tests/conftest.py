from unittest.mock import AsyncMock, patch
import pytest
from app import DurableApp, Service, WorkflowContext
from fastapi import Request
from pydantic import ValidationError


# This fixture provides a fresh App instance for each test that needs it
@pytest.fixture
def app():
    app_instance = DurableApp()
    yield app_instance


@pytest.fixture
def service():
    service_instance = Service()
    yield service_instance


@pytest.fixture
def workflow_context():
    context = WorkflowContext()
    yield context

@pytest.fixture
def mock_internal_client():
    with patch('app._internal.workflow.InternalEndureClient') as mock:
        yield mock

@pytest.fixture
async def mock_request():
    mock = AsyncMock()
    mock.json = AsyncMock()
    return mock
