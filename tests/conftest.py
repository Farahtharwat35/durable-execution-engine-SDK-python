import pytest
from app import DurableApp, Service, WorkflowContext


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
