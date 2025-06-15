from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app._internal import EndureException, ErrorResponse, ServiceRegistry
from dataclasses import asdict
class DurableApp:
    """
    DurableApp is a wrapper class for a FastAPI application that integrates a service discovery endpoint.
    Args:
        app (FastAPI): The FastAPI application instance to be wrapped.
    Attributes:
        app (FastAPI): The FastAPI application instance.
    Methods:
        _discover():
            Handles GET requests to the "/discover" endpoint.
            Returns a dictionary containing all registered services and their workflows.
            Each service includes its name and a list of workflows, where each workflow contains:
                - name: The workflow's name.
                - input: The expected input schema or parameters for the workflow.
                - output: The output schema or result type of the workflow.
                - idem_retention: The retention policy for idempotency.
    Usage:
        Instantiate DurableApp with a FastAPI app to automatically register the "/discover" endpoint for service discovery and add the registered services to the FastAPI router.
    """
    def __init__(self, app):
        self.app: FastAPI = app
        serviceRegistry = ServiceRegistry.get_instance()
        serviceRegistry.get_router().add_api_route(
            "/discover",
            self._discover,
            methods=["GET"],
        )
        self.app.include_router(serviceRegistry.get_router())
        self.app.add_exception_handler(
            EndureException,
            self.raise_exception
        )
        
    def _discover(self):
        services = self.serviceRegistry.get_services()
        return {
            "services": [
                {
                    "name": service_name,
                    "workflows": [
                        {
                            "name": workflow.name,
                            "input": workflow.input,
                            "output": workflow.output,
                            "idem_retention": workflow.retention,
                        }
                        for workflow in workflows
                    ],
                }
                for service_name, workflows in services.items()
            ]
        }
    
    async def raise_exception(request: Request, exc: EndureException):
        return JSONResponse(
            status_code=exc.status_code,
            content=asdict(ErrorResponse(output=exc.output))
        )
    