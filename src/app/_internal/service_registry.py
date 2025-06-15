from typing import Dict, List

from fastapi import APIRouter

from .workflow import Workflow


class ServiceRegistry:
    """
    Singleton class for managing workflow services and their API routes.
    Attributes:
        _instance (ServiceRegistry): The singleton instance of the registry.
        _services (Dict[str, List[Workflow]]): Mapping of service names to lists of registered workflows.
        _router (APIRouter): FastAPI router for dynamically registered workflow routes.
    Methods:
        __new__(cls):
            Ensures only one instance of ServiceRegistry exists (singleton pattern).
        register_workflow(service_name: str, workflow: Workflow):
            Registers a workflow under the specified service name.
        register_workflow_in_router(service_name: str, workflow: Workflow):
            Adds an API route for the workflow under the given service name to the router.
        get_services() -> Dict[str, List[Workflow]]:
            Returns the dictionary of registered services and their workflows.
        get_router() -> APIRouter:
            Returns the FastAPI router containing all registered workflow routes.
    """  # noqa: E501

    _instance = None
    _services: Dict[str, List[Workflow]]
    _router: APIRouter

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceRegistry, cls).__new__(cls)
            cls._instance._services = {}
            cls._instance._router = APIRouter()
        return cls._instance

    def register_workflow(self, service_name: str, workflow: Workflow):
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
        self._router.add_api_route(
            f"/execute/{service_name}/{workflow.name}",
            workflow.get_handler_route(),
            methods=["POST"],
        )

    def get_services(self) -> Dict[str, List[Workflow]]:
        return self._services.copy()

    def get_router(self) -> APIRouter:
        return self._router

    def clear(self):
        """Clear all registered services and routes"""
        self._services.clear()
        self._router = APIRouter()
