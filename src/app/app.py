from dataclasses import asdict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app._internal import (
    ServiceRegistry,
)
from app.types import EndureException, ErrorResponse


class DurableApp:
    """
    A wrapper for FastAPI applications that integrates durable workflow execution capabilities.

    This class provides:
    1. Service discovery via the "/discover" endpoint
    2. Automatic workflow route registration
    3. Centralized error handling for EndureException

    Args:
        app (FastAPI): The FastAPI application instance to be wrapped.

    Attributes:
        app (FastAPI): The FastAPI application instance.
        serviceRegistry (ServiceRegistry): Registry managing workflow services and routes.

    Features:
        - Service Discovery: The "/discover" endpoint returns metadata about all registered
          services and their workflows, including input/output schemas and retention policies.
        - Error Handling: Converts EndureException to consistent JSON responses.
        - Route Management: Automatically registers workflow routes from ServiceRegistry.

    Example Response from /discover:
        {
            "services": [
                {
                    "name": "data_service",
                    "workflows": [
                        {
                            "name": "process_data",
                            "input": "dict[str, int]",
                            "output": "list[str]",
                            "idem_retention": 7
                        }
                    ]
                }
            ]
        }
    """  # noqa: E501

    def __init__(self, app):
        """
        Initialize the DurableApp wrapper.

        Args:
            app (FastAPI): The FastAPI application to wrap.

        This method:
        1. Stores the FastAPI app instance
        2. Creates a ServiceRegistry instance
        3. Registers the /discover endpoint
        4. Includes all workflow routes in the app
        5. Sets up EndureException handling
        """
        self.app: FastAPI = app
        self.serviceRegistry = ServiceRegistry()
        self.serviceRegistry.get_router().add_api_route(
            "/discover",
            self._discover,
            methods=["GET"],
        )
        self.app.include_router(self.serviceRegistry.get_router())
        self.app.add_exception_handler(EndureException, self.raise_exception)

    def _discover(self):
        """
        Handle GET requests to the "/discover" endpoint.

        Returns:
            dict: A dictionary containing all registered services and their workflows.
        """
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
                            "idem_retention": workflow.retention_period,
                        }
                        for workflow in workflows
                    ],
                }
                for service_name, workflows in services.items()
            ]
        }

    async def raise_exception(
        self, request: Request, exc: EndureException, _=None
    ):
        """
        FastAPI exception handler for EndureException.

        This handler converts EndureException instances into consistent JSON responses
        using the ErrorResponse model.

        Args:
            request (Request): The FastAPI request object (required by FastAPI).
            exc (EndureException): The exception to handle. Contains:
                - status_code: HTTP status code to return
                - output: Error details to include in response
            _ (Any, optional): Unused parameter that may be provided by FastAPI.

        Returns:
            JSONResponse: An error response with:
                - status_code: From the exception
                - content: Dict from ErrorResponse including the exception's output

        Example:
            For an EndureException(status_code=400, output={"error": "Invalid input"}),
            returns a 400 response with body:
            {
                "output": {
                    "error": "Invalid input"
                }
            }
        """
        return JSONResponse(
            status_code=exc.status_code,
            content=asdict(ErrorResponse(output=exc.output)),
        )
