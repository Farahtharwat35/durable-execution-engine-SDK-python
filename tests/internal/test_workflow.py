import pytest
from unittest.mock import patch
from typing import Any
from app._internal.workflow import Workflow
from app._internal.types import EndureException
from app.workflow_context import WorkflowContext
from starlette.responses import Response

class InputModel:
    name: str
    age: int
    tags: list[str]

class OutputModel:
    success: bool
    data: dict[str, Any]
    timestamps: list[int]
    def __init__(self, success=True, data=None, timestamps=None):
        self.success = success
        self.data = data or {}
        self.timestamps = timestamps or []
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

    @staticmethod
    def list_workflow(ctx: WorkflowContext, input: list[str]) -> tuple[int, str]:
        return (1, "test")

    @staticmethod
    def complex_workflow(ctx: WorkflowContext, input: dict[str, list[int]]) -> dict[str, Any]:
        return {"result": [1, 2, 3]}

    @staticmethod
    def class_workflow(ctx: WorkflowContext, input: InputModel) -> OutputModel:
        return OutputModel()

    @staticmethod
    def nested_class_workflow(ctx: WorkflowContext, input: InputModel) -> dict[str, OutputModel]:
        return {"result": OutputModel()}

    class DefaultValueModel:
        name: str = "default_name"
        count: int = 0
        items: list[str] = []
        options: dict[str, bool] | None = None

    @staticmethod
    def default_value_workflow(ctx: WorkflowContext, input: 'TestWorkflow.DefaultValueModel') -> str:
        return f"Processed {input.name}"

    def test_workflow_initialization(self):
        workflow = Workflow(self.sync_workflow)
        assert workflow.name == "sync_workflow"
        assert workflow.func == self.sync_workflow
        assert workflow.retention_period is None

        # Testing with retention period
        workflow_with_retention = Workflow(
            self.sync_workflow, retention_period=7
        )
        assert workflow_with_retention.retention_period == 7

    def test_get_io_types(self):
        # Test 1: Basic types (dict)
        workflow = Workflow(self.typed_workflow)
        assert workflow.input == "dict"
        assert workflow.output == "dict"

        # Test 2: Untyped workflow
        def untyped_workflow(ctx, input):
            return input
        workflow_untyped = Workflow(untyped_workflow)
        assert workflow_untyped.input == "Any"
        assert workflow_untyped.output == "Any"

        # Test 3: Simple type (int)
        workflow_async = Workflow(self.async_workflow)
        assert workflow_async.input == "int"
        assert workflow_async.output == "int"

        # Test 4: Generic types (list and tuple)
        workflow_list = Workflow(self.list_workflow)
        assert workflow_list.input == "list[str]"
        assert workflow_list.output == "tuple[int, str]"

        # Test 5: Nested generic types
        workflow_complex = Workflow(self.complex_workflow)
        assert workflow_complex.input == "dict[str, list[int]]"
        assert workflow_complex.output == "dict[str, Any]"

        # Test 6: Optional types
        def optional_workflow(ctx: WorkflowContext, input: str | None) -> list[int] | None:
            return [1, 2, 3] if input else None
        workflow_optional = Workflow(optional_workflow)
        assert workflow_optional.input == "str | None"
        assert workflow_optional.output == "list[int] | None"

    def test_get_io_types_with_classes(self):
        # Test 7: Class types
        workflow = Workflow(self.class_workflow)
        assert workflow.input == {
            'name': 'str',
            'age': 'int',
            'tags': 'list[str]'
        }
        assert workflow.output == {
            'success': 'bool',
            'data': 'dict[str, Any]',
            'timestamps': 'list[int]'
        }

        # Test 8: Nested class types
        workflow_nested = Workflow(self.nested_class_workflow)
        assert workflow_nested.input == {
            'name': 'str',
            'age': 'int',
            'tags': 'list[str]'
        }
        assert workflow_nested.output == "dict[str, {'success': 'bool', 'data': 'dict[str, Any]', 'timestamps': 'list[int]'}]"

    def test_get_io_types_with_defaults(self):
        # Test 9: Default values in class
        workflow = Workflow(self.default_value_workflow)
        assert workflow.input == {
            'name': 'str',
            'count': 'int',
            'items': 'list[str]',
            'options': 'dict[str, bool] | None'
        }
        assert workflow.output == 'str'

      
        ctx = WorkflowContext(execution_id="test-id")
        result = self.default_value_workflow(ctx, self.DefaultValueModel())
        assert result == "Processed default_name"

    @pytest.mark.asyncio
    async def test_handler_route_successful_execution(
        self, mock_request, mock_internal_client
    ):
        with patch(
            "app._internal.workflow.InternalEndureClient.mark_execution_as_running"
        ) as mock_mark_running:
            workflow = Workflow(self.sync_workflow)
            handler = workflow.get_handler_route()

            execution_id = "test-execution-id"
            input_data = {"name": "Farah", "age": 30}
            mock_request.json.return_value = {
                "execution_id": execution_id,
                "input": input_data,
            }
            
            result = await handler(mock_request)

            assert result == {"output": "Hello, Farah!"}
            mock_mark_running.assert_called_once_with(execution_id)

    @pytest.mark.asyncio
    async def test_handler_route_async_workflow(
        self, mock_request, mock_internal_client
    ):
        with patch(
            "app._internal.workflow.InternalEndureClient.mark_execution_as_running"
        ) as mock_mark_running:
            mock_mark_running.return_value = Response(status_code=200)
            workflow = Workflow(self.async_workflow)
            handler = workflow.get_handler_route()

            mock_request.json.return_value = {
                "execution_id": "test-execution-id",
                "input": 5,
            }

            result = await handler(mock_request)

            assert result == {"output": 10}
            mock_mark_running.assert_called_once_with("test-execution-id")

    @pytest.mark.asyncio
    async def test_handler_route_execution_error(self, mock_request):
        def failing_workflow(ctx: WorkflowContext, input: Any):
            raise ValueError("Workflow execution failed")

        workflow = Workflow(failing_workflow)
        handler = workflow.get_handler_route()

        mock_request.json.return_value = {
            "execution_id": "test-execution-id",
            "input": "test-input",
        }

        with pytest.raises(EndureException) as exc_info:
            await handler(mock_request)

        assert exc_info.value.status_code == 500
        assert "Internal server error" == str(exc_info.value.output["error"])
