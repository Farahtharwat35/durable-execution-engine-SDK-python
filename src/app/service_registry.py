from typing import Dict, List
from fastapi import APIRouter
from .workflow import Workflow

class ServiceRegistry:
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
        if service_name not in self._services:
            self._services[service_name] = []
        self._services[service_name].append(workflow)

    def register_workflow_in_router(self, service_name: str, workflow: Workflow):
        self._router.add_api_route(
            f"execute/{service_name}/{workflow.name}",
            workflow.get_handler_route(),
            methods=["POST"],
        )
            
    def get_services(self) -> Dict[str, List[Workflow]]:
        return self._services

    def get_router(self) -> APIRouter:
        return self._router

