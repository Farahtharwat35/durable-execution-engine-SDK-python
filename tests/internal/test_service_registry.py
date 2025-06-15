import pytest
from fastapi import APIRouter
from typing import Dict, List
from app._internal import ServiceRegistry
from app._internal import Workflow
from app import WorkflowContext


class TestServiceRegistry:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.registry = ServiceRegistry()
        yield
        self.registry._services.clear()
        self.registry._router = APIRouter()

    def test_register_workflow(self):
        registry = ServiceRegistry()
        service_name = "test_service"

        def mock_workflow(ctx: WorkflowContext, input: Dict) -> Dict:
            return {"result": "success"}

        workflow = Workflow(mock_workflow)

        registry.register_workflow(service_name, workflow)

        services = registry.get_services()
        assert service_name in services
        assert len(services[service_name]) == 1
        assert services[service_name][0].name == mock_workflow.__name__

    def test_register_workflow_in_router(self):

        registry = ServiceRegistry()
        service_name = "test_service"

        def mock_workflow(ctx: WorkflowContext, input: Dict) -> Dict:
            return {"result": "success"}

        workflow = Workflow(mock_workflow)

        registry.register_workflow_in_router(service_name, workflow)

        router = registry.get_router()
        routes = router.routes
        assert len(routes) == 1
        assert routes[0].path == f"/execute/{service_name}/{workflow.name}"
        assert "POST" in routes[0].methods

    def test_get_services(self):

        registry = ServiceRegistry()
        service_name1 = "service1"
        service_name2 = "service2"

        def workflow1(ctx: WorkflowContext, input: Dict) -> Dict:
            return {"result": "success1"}

        def workflow2(ctx: WorkflowContext, input: Dict) -> Dict:
            return {"result": "success2"}

        w1 = Workflow(workflow1)
        w2 = Workflow(workflow2)

        registry.register_workflow(service_name1, w1)
        registry.register_workflow(service_name2, w2)

        services = registry.get_services()
        assert len(services) == 2
        assert service_name1 in services
        assert service_name2 in services
        assert services[service_name1][0].name == workflow1.__name__
        assert services[service_name2][0].name == workflow2.__name__

    def test_get_router(self):

        registry = ServiceRegistry()
        router = registry.get_router()

        assert isinstance(router, APIRouter)
        assert router == registry._router
