import pytest
from typing import Any
from app._internal.workflow import Workflow
from app._internal.types import EndureException
from app.workflow_context import WorkflowContext
from starlette.responses import Response

class TestWorkflow:
    @staticmethod
    def sync_workflow(ctx: WorkflowContext, input: dict) -> str:
        return f"Hello, {input['name']}!"

    @staticmethod
    def typed_workflow(ctx: WorkflowContext, input: dict) -> dict:
        return {"message": input["name"]}

    @staticmethod
    async def async_workflow(ctx: WorkflowContext, input: int) -> int:
        return input * 2

    def test_workflow_initialization(self):
        workflow = Workflow(self.sync_workflow)
        assert workflow.name == "sync_workflow"
        assert workflow.func == self.sync_workflow
        assert workflow.retention_period is None

        # testing with retention period
        workflow_with_retention = Workflow(self.sync_workflow, retention_period=7)
        assert workflow_with_retention.retention_period == 7

    def test_get_io_types(self):
        # testing with typed workflow
        workflow = Workflow(self.typed_workflow)
        assert workflow.input == dict
        assert workflow.output == dict

        # testing with untyped workflow
        def untyped_workflow(ctx, input):
            return input
        
        workflow_untyped = Workflow(untyped_workflow)
        assert workflow_untyped.input == Any
        assert workflow_untyped.output == Any

    @pytest.mark.asyncio
    async def test_handler_route_successful_execution(self, mock_request, mock_internal_client):
        workflow = Workflow(self.sync_workflow)
        handler = workflow.get_handler_route()
        
        execution_id = "test-execution-id"
        input_data = {"name": "Farah", "age": 30}
        mock_request.json.return_value = {
            "execution_id": execution_id,
            "input": input_data
        }

        # executing the handler
        result = await handler(mock_request)

        assert result == {"output": "Hello, Farah!"}
        mock_internal_client.mark_execution_as_running.assert_called_once_with(execution_id)

    @pytest.mark.asyncio
    async def test_handler_route_async_workflow(self, mock_request, mock_internal_client):
        mock_internal_client.mark_execution_as_running.return_value = Response(status_code=200)
        workflow = Workflow(self.async_workflow)
        handler = workflow.get_handler_route()
        
        mock_request.json.return_value = {
            "execution_id": "test-execution-id",
            "input": 5
        }

        result = await handler(mock_request)

        assert result == {"output": 10}

    @pytest.mark.asyncio
    async def test_handler_route_validation_error(self, mock_request):
        workflow = Workflow(self.typed_workflow)
        handler = workflow.get_handler_route()
        
        # setup request data with invalid input type
        mock_request.json.return_value = {
            "execution_id": "test-execution-id",
            "input": "invalid-input"  # this should be a dict
        }

        # executing handler and expect validation error
        with pytest.raises(EndureException) as exc_info:
            await handler(mock_request)
        
        assert exc_info.value.status_code == 400
        assert "Validation error" in str(exc_info.value.output["error"])

    @pytest.mark.asyncio
    async def test_handler_route_execution_error(self, mock_request):
        def failing_workflow(ctx: WorkflowContext, input: Any):
            raise ValueError("Workflow execution failed")

        workflow = Workflow(failing_workflow)
        handler = workflow.get_handler_route()
        
        mock_request.json.return_value = {
            "execution_id": "test-execution-id",
            "input": "test-input"
        }

        with pytest.raises(EndureException) as exc_info:
            await handler(mock_request)
        
        assert exc_info.value.status_code == 500
        assert "Internal server error" == str(exc_info.value.output["error"])