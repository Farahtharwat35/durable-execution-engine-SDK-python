import pytest
from app import WorkflowContext, Service
from app._internal import ServiceRegistry, Workflow


class TestService:
    @pytest.fixture
    def service(self):
        """Create a test service instance"""
        return Service("test_service")

    @pytest.fixture
    def valid_workflow(self):
        """Create a valid workflow function"""

        def valid_workflow(input: dict, ctx: WorkflowContext):
            return {"result": input}

        return valid_workflow

    @pytest.fixture
    def invalid_workflow_missing_ctx(self):
        """Create an invalid workflow function missing ctx parameter"""

        def invalid_workflow_1(input: dict):
            return {"result": input}

        return invalid_workflow_1

    @pytest.fixture
    def invalid_workflow_wrong_ctx_type(self):
        """Create an invalid workflow function with wrong ctx type"""

        def invalid_workflow_2(input: any, ctx: dict):
            return {"result": input}

        return invalid_workflow_2

    def test_workflow_decorator_valid_signature(self, service, valid_workflow):
        """Test that a workflow with valid signature is properly registered"""

        service.workflow(retention=30)(valid_workflow)

        registry = ServiceRegistry()
        services = registry.get_services()

        assert service.name in services
        workflow_instances = services[service.name]
        assert len(workflow_instances) == 1
        workflow_instance = workflow_instances[0]
        assert isinstance(workflow_instance, Workflow)
        assert workflow_instance.name == valid_workflow.__name__
        assert workflow_instance.retention_period == 30
        assert workflow_instance.func == valid_workflow

    def test_workflow_decorator_default_retention(
        self, service, valid_workflow
    ):
        """Test that default retention period is set when not specified"""

        service.workflow()(valid_workflow)

        registry = ServiceRegistry()
        services = registry.get_services()

        workflow_instances = services[service.name]
        assert len(workflow_instances) == 1
        workflow_instance = workflow_instances[0]
        assert workflow_instance.retention_period == 7

    def test_workflow_decorator_invalid_retention(
        self, service, valid_workflow
    ):
        """Test that invalid retention period raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            service.workflow(retention=-1)(valid_workflow)
        assert "Retention period must be a non-negative integer" in str(
            exc_info.value
        )

    def test_workflow_decorator_invalid_signature_missing_ctx(
        self, service, invalid_workflow_missing_ctx
    ):
        """Test that workflow without ctx parameter raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            service.workflow()(invalid_workflow_missing_ctx)
        assert (
            "The workflow function must have an 'input' and 'ctx' argument"
            in str(exc_info.value)
        )

    def test_workflow_decorator_invalid_signature_wrong_ctx_type(
        self, service, invalid_workflow_wrong_ctx_type
    ):
        """Test that workflow with wrong ctx type raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            service.workflow()(invalid_workflow_wrong_ctx_type)
        assert "The 'ctx' argument must be of type WorkflowContext" in str(
            exc_info.value
        )

    def test_workflow_decorator_multiple_workflows(self, service):
        """Test registering multiple workflows for the same service"""

        def workflow1(input: dict, ctx: WorkflowContext):
            return {"result": input}

        workflow1.__name__ = "test_workflow_1"

        def workflow2(input: dict, ctx: WorkflowContext):
            return {"result": input}

        workflow2.__name__ = "test_workflow_2"

        service.workflow(retention=0)(workflow1)
        service.workflow(retention=20)(workflow2)

        registry = ServiceRegistry()
        services = registry.get_services()

        assert service.name in services
        workflow_instances = services[service.name]
        assert len(workflow_instances) == 2

        workflow_info = [
            (w.name, w.retention_period) for w in workflow_instances
        ]
        assert (workflow1.__name__, 0) in workflow_info
        assert (workflow2.__name__, 20) in workflow_info

    def test_workflow_decorator_preserves_function(
        self, service, valid_workflow
    ):
        """Test that the decorator preserves the original function"""
        decorated_workflow = service.workflow()(valid_workflow)

        assert decorated_workflow == valid_workflow

        result = decorated_workflow(
            {"test": "data"}, WorkflowContext("test-execution-id")
        )
        assert result == {"result": {"test": "data"}}

    def test_workflow_decorator_invalid_signature_missing_input(self, service):
        """Test that workflow without 'input' parameter raises ValueError"""

        def wf_missing_input(foo: dict, ctx: WorkflowContext):
            return {"result": foo}

        with pytest.raises(ValueError) as exc_info:
            service.workflow()(wf_missing_input)
        assert (
            "The workflow function must have an 'input' and 'ctx' argument"
            in str(exc_info.value)
        )

    def test_workflow_decorator_invalid_signature_too_many_args(self, service):
        """Test that workflow with too many arguments raises ValueError"""

        def wf_too_many_args(input: dict, ctx: WorkflowContext, extra: int):
            return {"result": input}

        with pytest.raises(ValueError) as exc_info:
            service.workflow()(wf_too_many_args)
        assert (
            "The workflow function must have an 'input' and 'ctx' argument"
            in str(exc_info.value)
        )
