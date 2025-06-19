from app._internal import (
    ServiceRegistry,
    Workflow,
    validate_retention_period,
)
from app.workflow_context import WorkflowContext


class Service:
    """
    A service container for registering and managing durable workflows.

    The Service class acts as a namespace for grouping related workflows and provides
    a decorator interface for registering workflow functions. It integrates with the
    ServiceRegistry to manage workflow registration and route creation.

    Attributes:
        name (str): The unique name of the service, used in API endpoint paths.
        registry (ServiceRegistry): The singleton registry instance managing all services.

    Example:
        ```python
        from app import Service
        from app.workflow_context import WorkflowContext

        # Create a service named "order_processing"
        service = Service("order_processing")

        # Register a workflow in this service
        @service.workflow(retention=30)
        def process_order(input: dict, ctx: WorkflowContext):
            # workflow implementation
            pass

        # The workflow is now available at:
        # POST /execute/order_processing/process_order
        ```
    """

    def __init__(self, name: str):
        """
        Initialize a new service with the given name.

        Args:
            name (str): The unique name for this service. This name will be used:
                       - In the API endpoint paths (/execute/{name}/{workflow})
                       - In the service discovery endpoint response
                       - For grouping related workflows

        Note:
            All services share the same ServiceRegistry instance, ensuring
            consistent workflow registration across the application.
        """
        self.name = name
        self.registry = ServiceRegistry()

    def workflow(self, **config):
        """
        Decorator that registers a function as a workflow in the service registry.

        This decorator:
        1. Validates the workflow configuration (e.g., retention period)
        2. Validates the function signature requirements
        3. Creates a Workflow instance to wrap the function
        4. Registers the workflow with the ServiceRegistry
        5. Creates an API endpoint for the workflow

        Args:
            **config: Configuration options for the workflow.
                - retention (int, optional): Number of days to retain workflow
                  execution history and state. Must be a non-negative integer.
                  Default: 7 days.

        Returns:
            callable: The original function (unmodified). The function can still
                    be called directly, but is now also available via HTTP endpoint.

        Raises:
            ValueError: If:
                - retention period is not a non-negative integer
                - function doesn't have exactly two parameters named 'input' and 'ctx'
                - 'ctx' parameter isn't annotated with WorkflowContext type

        Function Requirements:
            The decorated function must:
            1. Have exactly two parameters:
               - input: Any type (with optional type annotation)
               - ctx: WorkflowContext (must include type annotation)
            2. Return a value (any type, with optional type annotation)
            3. Can be sync or async

        API Endpoint:
            The workflow will be available at:
            POST /execute/{service_name}/{workflow_name}

            With request body:
            {
                "execution_id": str,
                "input": Any  # Must match the function's input type
            }

        Example:
            ```python
            service = Service("data_processing")

            @service.workflow(retention=30)
            def process_data(input: dict[str, int], ctx: WorkflowContext) -> list[str]:
                results = []
                for key, value in input.items():
                    # Process data...
                    results.append(f"{key}: {value}")
                return results
            ```
        """  # noqa: E501

        def decorator(func):
            retention_period = config.get("retention", 7)
            validate_retention_period(retention_period)
            input_keys = func.__code__.co_varnames[: func.__code__.co_argcount]
            if (
                not ("input" in input_keys and "ctx" in input_keys)
                or len(input_keys) != 2
            ):
                raise ValueError(
                    "The workflow function must have an 'input' and 'ctx' argument."
                )
            if func.__annotations__.get("ctx") != WorkflowContext:
                raise ValueError(
                    "The 'ctx' argument must be of type WorkflowContext."
                )
            workflow = Workflow(func, retention_period)
            self.registry.register_workflow(self.name, workflow)
            self.registry.register_workflow_in_router(self.name, workflow)
            return func

        return decorator
