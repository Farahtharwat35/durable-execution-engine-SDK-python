# Set environment variables before any imports
import os

os.environ["DURABLE_ENGINE_BASE_URL"] = "http://test-engine:8000"

import pytest
from unittest.mock import AsyncMock, Mock, patch
from app import DurableApp, Service, WorkflowContext
from app._internal.types import Response


@pytest.fixture(autouse=True)
def cleanup_test_env():
    """Clean up test environment variables after each test"""
    yield
    if "DURABLE_ENGINE_BASE_URL" in os.environ:
        del os.environ["DURABLE_ENGINE_BASE_URL"]


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
    context = WorkflowContext("test-execution-id")
    yield context


@pytest.fixture
def mock_internal_client():
    """Mock both requests and InternalEndureClient to prevent real HTTP calls"""
    http_response = Mock()
    http_response.status_code = 201
    http_response.json.return_value = {}

    # Blocking actual HTTP requests by mocking requests.patch
    with patch("requests.patch", return_value=http_response):
        with patch(
            "app._internal.workflow.InternalEndureClient"
        ) as MockClient:
            MockClient.send_log = Mock()
            MockClient.send_log.side_effect = [
                Response(status_code=201, payload={}).to_dict(),
                Response(status_code=200, payload={}).to_dict(),
            ]
        yield MockClient


@pytest.fixture
async def mock_request():
    mock = AsyncMock()
    mock.json = AsyncMock()
    return mock


@pytest.fixture
def sample_action():
    def action(input_data):
        return {"result": input_data}

    return action
