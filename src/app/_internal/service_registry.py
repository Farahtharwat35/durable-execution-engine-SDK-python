from typing import Dict, List

from fastapi import APIRouter

from .workflow import Workflow


class ServiceRegistry:
    """
    Singleton class for managing durable workflow services and their API routes in FastAPI.
    Each service can contain multiple workflows, and each workflow gets its own API endpoint
    for execution.

    Attributes:
        _instance (ServiceRegistry): The singleton instance of the registry.
        _services (Dict[str, List[Workflow]]): Mapping of service names to lists of registered workflows.
        _router (APIRouter): FastAPI router containing dynamically registered workflow endpoints.

    Methods:
        __new__(cls): Creates or returns the singleton instance.
        register_workflow(service_name: str, workflow: Workflow): Registers a workflow under a service.
        register_workflow_in_router(service_name: str, workflow: Workflow): Creates an API endpoint for the workflow.
        get_services() -> Dict[str, List[Workflow]]: Returns a copy of registered services and workflows.
        get_router() -> APIRouter: Returns the router with all workflow endpoints.
        clear(): Resets the registry to its initial state.
    """  # noqa: E501

    _instance = None
    _services: Dict[str, List[Workflow]]
    _router: APIRouter

    def __new__(cls):
        """
        Implements the singleton pattern, ensuring only one instance of ServiceRegistry exists.
        Creates and initializes the instance if it doesn't exist, otherwise returns the existing instance.

        Returns:
            ServiceRegistry: The singleton instance of the registry.
        """
        if cls._instance is None:
            cls._instance = super(ServiceRegistry, cls).__new__(cls)
            cls._instance._services = {}
            cls._instance._router = APIRouter()
        return cls._instance

    def register_workflow(self, service_name: str, workflow: Workflow):
        """
        Registers a workflow under the specified service name. If the service doesn't exist,
        it will be created. Prevents duplicate workflow names within the same service.

        Args:
            service_name (str): Name of the service to register the workflow under.
            workflow (Workflow): The workflow instance to register.

        Raises:
            ValueError: If service_name is empty or not a string,
                       if workflow is None or not a Workflow instance,
                       or if a workflow with the same name already exists in the service.
        """
        if not service_name or not isinstance(service_name, str):
            raise ValueError("Service name must be a non-empty string")
        if not workflow or not isinstance(workflow, Workflow):
            raise ValueError("Workflow must be a valid Workflow instance")

        if service_name not in self._services:
            self._services[service_name] = []

        # checks for duplicate workflow names within the service
        if any(w.name == workflow.name for w in self._services[service_name]):
            raise ValueError(
                f"Workflow with name '{workflow.name}' already exists in service '{service_name}'"
            )

        self._services[service_name].append(workflow)

    def register_workflow_in_router(
        self, service_name: str, workflow: Workflow
    ):
        """
        Creates an API endpoint for the workflow under the given service name.
        The endpoint will be available at /execute/{service_name}/{workflow.name}
        and will accept POST requests.

        Args:
            service_name (str): The service name to use in the endpoint path.
            workflow (Workflow): The workflow whose handler will be registered.
        """
        self._router.add_api_route(
            f"/execute/{service_name}/{workflow.name}",
            workflow.get_handler_route(),
            methods=["POST"],
        )

    def get_services(self) -> Dict[str, List[Workflow]]:
        """
        Returns a shallow copy of the services dictionary to prevent direct modification
        of the internal state.

        Returns:
            Dict[str, List[Workflow]]: A copy of the mapping between service names and their workflows.
        """
        return self._services.copy()

    def get_router(self) -> APIRouter:
        """
        Returns the FastAPI router containing all registered workflow endpoints.

        Returns:
            APIRouter: The router with all workflow endpoints.
        """
        return self._router

    def clear(self):
        """
        Resets the registry to its initial state by:
        - Clearing all registered services
        - Creating a new empty router
        - Resetting the singleton instance
        - Creating a new instance

        This is primarily useful for testing purposes.
        """
        self._services.clear()
        self._router = APIRouter()
        self.__class__._instance = None
        self.__class__()
