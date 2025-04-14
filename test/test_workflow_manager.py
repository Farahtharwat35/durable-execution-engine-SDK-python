import pytest
import httpx
from unittest.mock import patch
from src.models.execution_model import Execution
from src.client.workflow_manager import WorkflowManager

MOCK_EXECUTION_DATA = {
    "execution_id": "exec123",
    "status": "running",
    "output": {
    "order_id": "ORD-12345",
    "status": "completed",
    "total": 45.99,
    "items_count": 3
  },
    "message": "Execution is already running"
}

@pytest.fixture
def workflow_manager():
    return WorkflowManager(base_url="http://test-server")

class TestWorkflowManager:
    def test_execute_success(self, workflow_manager):
        with patch("httpx.Client.post") as mock_post:
            mock_post.return_value = httpx.Response(
                status_code=201,
                json=MOCK_EXECUTION_DATA
            )
            
            result = workflow_manager.execute(
                workflow_name="test_workflow",
                service_name="test_service",
                input_data={"key": "value"}
            )
            
            assert isinstance(result, Execution)
            assert result.execution_id == "exec123"
            mock_post.assert_called_once_with(
                "http://test-server/services/test_service/workflows/test_workflow/executions",
                json={"input": {"key": "value"}}
            )

    def test_execute_failure(self, workflow_manager):
        with patch("httpx.Client.post") as mock_post:
            mock_post.return_value = httpx.Response(
                status_code=400,
                json={"message": "Invalid input"}
            )
            
            with pytest.raises(Exception) as exc_info:
                workflow_manager.execute(
                    workflow_name="test_workflow",
                    service_name="test_service",
                    input_data={"key": "value"}
                )
            
            assert "Error: 400 - Invalid input" in str(exc_info.value)

    def test_get_success(self, workflow_manager):
        with patch("httpx.Client.get") as mock_get:
            mock_get.return_value = httpx.Response(
                status_code=200,
                json=MOCK_EXECUTION_DATA
            )
            
            result = workflow_manager.get("exec123")
            
            assert isinstance(result, Execution)
            assert result.execution_id == "exec123"
            mock_get.assert_called_once_with(
                "http://test-server/executions/exec123"
            )


    def test_get_failure(self, workflow_manager):
        with patch("httpx.Client.get") as mock_get:
            mock_get.return_value = httpx.Response(
                status_code=404,
                json={"message": "Not found"}
            )
            
            with pytest.raises(Exception) as exc_info:
                workflow_manager.get("exec123")
            
            assert "Error: 404 - Not found" in str(exc_info.value)

    @pytest.mark.parametrize("method,status", [
        ("resume", "resumed"),
        ("pause", "paused"),
        ("terminate", "terminated")
    ])
    def test_status_methods(self, workflow_manager, method, status):
        with patch("httpx.Client.patch") as mock_patch:
            mock_patch.return_value = httpx.Response(status_code=204)
            
            getattr(workflow_manager, method)("exec123", status)
            
            mock_patch.assert_called_once_with(
                "http://test-server/executions/exec123",
                json={"status": status}
            )

    def test_update_status_failure(self, workflow_manager):
        with patch("httpx.Client.patch") as mock_patch:
            mock_patch.return_value = httpx.Response(
                status_code=400,
                json={"message": "Invalid status"}
            )
            
            with pytest.raises(Exception) as exc_info:
                workflow_manager._update_status("exec123", "invalid_status")
            
            assert "Error: 400 - Invalid status" in str(exc_info.value)