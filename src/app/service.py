from app._internal import (
    ServiceRegistry,
    Workflow,
    validate_retention_period,
)
from app.workflow_context import WorkflowContext


class Service:
    def __init__(self, name: str):
        self.name = name
        self.registry = ServiceRegistry()

    def workflow(self, **config):
        """
        Decorator that registers a function as a workflow in the service registry.

        This decorator validates the workflow function signature, creates a Workflow
        instance, and registers it with the ServiceRegistry for execution through
        the API router.

        Args:
            **config: Configuration options for the workflow.
                - retention (int, optional): Number of days to retain workflow
                execution history and state. Must be a non-negative integer.
                Default: 7 days.

        Returns:
            callable: The original function (unmodified), which can now be executed
                    as a registered workflow.

        Raises:
            ValueError: If the retention period is invalid (not a non-negative integer).
            ValueError: If the workflow function doesn't have exactly two parameters
                    named 'input' and 'ctx'.
            ValueError: If the 'ctx' parameter isn't annotated with WorkflowContext type.

        Requirements:
            - Workflow function must have exactly two parameters: 'input' and 'ctx'
            - The 'ctx' parameter must be type-annotated as WorkflowContext

        Example:
            from my_app import Service
            from app.workflow_context import WorkflowContext
            from typing import Dict, Any

            service = Service("my_service")

            @service.workflow(retention=30)
            def process_order(input: dict, ctx: WorkflowContext):
        Notes:
            Once registered, the workflow can be invoked via the API endpoint:
            POST /execute/{service_name}/{workflow_name}
        """  # noqa: E501

        def decorator(func):
            retention_period = config.get("retention", 7)
            validate_retention_period(retention_period)
            input_keys = func.__code__.co_varnames[: func.__code__.co_argcount]
            if ("input" and "ctx" not in input_keys) or len(input_keys) != 2:
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
