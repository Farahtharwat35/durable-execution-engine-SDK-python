import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app import DurableApp, Service, WorkflowContext , EndureException
from app._internal import ServiceRegistry


class TestApp:
    @pytest.fixture(autouse=True)
    def setup(self):
        ServiceRegistry().clear()
        self.app = FastAPI()
        self.client = TestClient(self.app)
        
        self.mark_running_patcher = patch('app._internal.internal_client.InternalEndureClient.mark_execution_as_running')
        self.send_log_patcher = patch('app._internal.internal_client.InternalEndureClient.send_log')
        
        self.mock_mark_running = self.mark_running_patcher.start()
        self.mock_send_log = self.send_log_patcher.start()
        self.mock_send_log.return_value = {"status_code": 200}
        
        yield
        
        self.mark_running_patcher.stop()
        self.send_log_patcher.stop()
        ServiceRegistry().clear()
        self.app = None
        self.durable_app = None
        self.client = None

    def test_discover_endpoint_returns_correct_format(self):
    
        test_service = Service("test_service")

        @test_service.workflow(retention=7)
        def test_workflow(input: dict, ctx: WorkflowContext):
            return {"result": "test"}

        self.durable_app = DurableApp(self.app)
  
        response = self.client.get("/discover")
        assert response.status_code == 200

      
        data = response.json()
        assert "services" in data
        assert len(data["services"]) == 1

        service = data["services"][0]
        assert service["name"] == "test_service"
        assert len(service["workflows"]) == 1

        workflow = service["workflows"][0]
        assert workflow["name"] == "test_workflow"
        assert workflow["input"] == 'dict'
        assert workflow["output"] == 'Any'
        assert workflow["idem_retention"] == 7

    def test_router_registration(self):
       
        test_service = Service("test_service")

        @test_service.workflow(retention=7)
        def test_workflow(input: dict, ctx: WorkflowContext):
            return {"result": "test"}

        # creating DurableApp instance after registering workflows
        self.durable_app = DurableApp(self.app)

      
        response = self.client.post(
            "/execute/test_service/test_workflow",
            json={"execution_id": "test-123", "input": {"test": "data"}},
        )
        assert response.status_code == 200
        assert response.json() == {"output": {"result": "test"}}

    def test_exception_handling(self):
        test_service = Service("test_service")

        @test_service.workflow(retention=7)
        def failing_workflow(input: dict, ctx: WorkflowContext):
            raise EndureException(
                status_code=400,
                output={"error": "Test error", "details": "Test details"},
            )

       
        self.durable_app = DurableApp(self.app)

   
        response = self.client.post(
            "/execute/test_service/failing_workflow",
            json={"execution_id": "test-123", "input": {"test": "data"}},
        )
        assert response.status_code == 400
        assert response.json() == {
            "output": {"error": "Test error", "details": "Test details"}
        }

    def test_multiple_services_and_workflows(self):
        
        service1 = Service("service1")
        service2 = Service("service2")

        @service1.workflow(retention=7)
        def workflow1(input: dict, ctx: WorkflowContext):
            return {"result": "workflow1"}

        @service1.workflow(retention=14)
        def workflow2(input: dict, ctx: WorkflowContext):
            return {"result": "workflow2"}

        @service2.workflow(retention=30)
        def workflow3(input: dict, ctx: WorkflowContext):
            return {"result": "workflow3"}

   
        self.durable_app = DurableApp(self.app)

       
        response = self.client.get("/discover")
        assert response.status_code == 200

        data = response.json()
        assert len(data["services"]) == 2

       
        service1_data = next(s for s in data["services"] if s["name"] == "service1")
        assert len(service1_data["workflows"]) == 2
        workflow_names = {w["name"] for w in service1_data["workflows"]}
        assert workflow_names == {"workflow1", "workflow2"}

       
        service2_data = next(s for s in data["services"] if s["name"] == "service2")
        assert len(service2_data["workflows"]) == 1
        assert service2_data["workflows"][0]["name"] == "workflow3"
    