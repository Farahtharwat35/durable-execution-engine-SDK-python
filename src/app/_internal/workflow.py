import asyncio
import json
from typing import Any, Callable, Union, get_type_hints, get_origin, get_args

from fastapi import Request, status, HTTPException, types
from pydantic import ValidationError

from app.workflow_context import WorkflowContext

from .internal_client import InternalEndureClient
from ..types import EndureException


class Workflow:
    """
    Represents a workflow function that can be executed through a FastAPI endpoint.

    A Workflow encapsulates a Python function and manages its execution through the durable
    execution engine. It extracts detailed type information from the function signature,
    including support for complex types like Unions, generics, and user-defined classes,
    and provides a FastAPI-compatible handler route with comprehensive error handling.

    Attributes:
        func (Callable): The workflow function to be executed.
        name (str): The name of the workflow (derived from function name).
        retention_period (int, optional): Number of days to retain workflow execution history.
        input (Any): Structured description of the input type (derived from type hints).
        output (Any): Structured description of the return type (derived from type hints).

    Example:
        @workflow
        def process_data(ctx: WorkflowContext, input: dict[str, int]) -> list[str]:
            # This will be wrapped in a Workflow instance with:
            # - name: "process_data"
            # - input: "dict[str, int]"
            # - output: "list[str]"
    """  # noqa: E501

    def __init__(self, func: Callable, retention_period: int = None):
        """
        Initialize a new Workflow instance.

        Args:
            func (Callable): The workflow function to wrap. Must have exactly two parameters:
                          - ctx: WorkflowContext - The workflow execution context
                          - input: Any - The input parameter with optional type annotation
                          The function can be either synchronous or asynchronous.
            retention_period (int, optional): Number of days to retain workflow execution
                                            history and state. Default is None.

        Note:
            The function's type hints are used to generate input/output type descriptions,
            falling back to Any if no type hints are provided.
        """  # noqa: E501
        self.func = func
        self.name = func.__name__
        self.retention_period = retention_period
        self.input, self.output = self._get_io(func)

    def _get_type_description(self, typ):
        """
        Recursively analyze a type annotation and convert it to a structured description.
        Handles complex Python type hints including:
        - Basic types (int, str, etc.)
        - Unions (Union[A, B] or A | B)
        - Optional types (Optional[T] or T | None)
        - Generic containers (list[T], dict[K, V])
        - User-defined classes (converted to field dictionaries)

        Args:
            typ: The type to analyze (can be a type hint, class, or Any)

        Returns:
            Union[str, dict]: A string for simple types or a dict for complex types,
                            representing the structure of the type.

        Example:
            >>> _get_type_description(dict[str, list[int]])
            "dict[str, list[int]]"
            >>> _get_type_description(Optional[MyClass])
            "MyClass | None"
        """
        if typ is Any:
            return "Any"

        if typ is type(None):
            return "None"

        origin = get_origin(typ)
        args = get_args(typ)

        # Union and | (UnionType in Python 3.10+)
        if origin in (Union, types.UnionType):
            type_names = [self._get_type_description(arg) for arg in args]
            return " | ".join(
                sorted(type_names, key=lambda x: (x == "None", x))
            )

        # Case: User-defined class
        if hasattr(typ, "__annotations__") and not origin:
            fields = getattr(typ, "__annotations__", {})
            return {
                name: self._get_type_description(t)
                for name, t in fields.items()
            }

        # Case: Generic container like list[Class], dict[str, Class], etc.
        if origin:
            origin_name = (
                origin.__name__ if hasattr(origin, "__name__") else str(origin)
            )

            # Special case: dict[str, SomeClass]
            if origin is dict and len(args) == 2:
                key_type = self._get_type_description(args[0])
                value_type = self._get_type_description(args[1])
                return f"{origin_name}[{key_type}, {value_type}]"

            # Case: list[SomeClass] or other single-arg generics
            elif len(args) == 1:
                inner_type = self._get_type_description(args[0])
                return f"{origin_name}[{inner_type}]"

            # Fallback for multi-arg generics like tuple[int, str]
            else:
                inner_types = [self._get_type_description(arg) for arg in args]
                return f"{origin_name}[{', '.join(inner_types)}]"

        # Case: Primitive or normal class
        if isinstance(typ, type):
            return typ.__name__

        # Fallback: stringify (removes "typing." prefix)
        return str(typ).replace("typing.", "")

    def _get_io(self, func):
        """
        Extracts and analyze input and output type information from the function's type hints.

        Args:
            func (Callable): The workflow function to analyze.

        Returns:
            tuple: A tuple containing (input_type, output_type), where each is either:
                  - A string representing a simple type (e.g., "int", "str")
                  - A string representing a complex type (e.g., "list[int]", "dict[str, MyClass]")
                  - A dict representing the structure of a user-defined class
                  If type hints aren't provided, "Any" is used as a fallback.

        Note:
            Uses _get_type_description to convert raw type hints into structured descriptions.
        """  # noqa: E501
        hints = get_type_hints(func)
        input_type = hints.get("input", Any)
        output_type = hints.get("return", Any)

        return self._get_type_description(
            input_type
        ), self._get_type_description(output_type)

    def get_handler_route(self):
        """
        Generate a FastAPI-compatible route handler for the workflow function.

        Creates an async handler that processes incoming requests, sets up the workflow context,
        marks the execution as running, executes the workflow function, and returns the result.

        Returns:
            Callable: An async function that can be registered as a FastAPI route handler.

        Request Format:
            Expects a JSON object with:
            - execution_id (str): Unique identifier for the workflow execution
            - input (Any): Input data matching the workflow's input type

        Response Format:
            Returns a JSON object with:
            - output (Any): The workflow function's return value

        Error Handling:
            - HTTP 400: Invalid JSON, missing required fields
            - HTTP 422: Input validation errors
            - HTTP 500: Internal server errors
            - Preserves status codes from EndureException and HTTPException
            All errors return JSON with 'error' and optional 'details' fields.

        Notes:
            - Supports both synchronous and asynchronous workflow functions
            - Automatically marks execution as running via InternalEndureClient
            - Converts HTTPException to EndureException for consistent error format
        """  # noqa: E501

        async def handler(request: Request):
            try:
                body = await request.json()
                if not isinstance(body, dict):
                    raise EndureException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        output={"error": "Request body must be a JSON object"},
                    )
                if "execution_id" not in body or "input" not in body:
                    raise EndureException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        output={
                            "error": "Request must include 'execution_id' and 'input' fields"
                        },
                    )
                ctx = WorkflowContext(execution_id=body["execution_id"])
                InternalEndureClient.mark_execution_as_running(
                    body["execution_id"]
                )
                output = self.func(ctx, body["input"])
                if asyncio.iscoroutine(output):
                    output = await output
                return {"output": output}
            except ValueError as ve:
                raise EndureException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    output={"error": "Value error", "details": str(ve)},
                )    
            # except EndureException:
            #     # re-raising EndureException to preserve its status code
            #     raise
            except HTTPException as he:
                raise EndureException(
                    status_code=he.status_code, output={"error": he.detail}
                )
            except ValidationError as ve:
                raise EndureException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    output={"error": "Validation error", "details": str(ve)},
                )
            except Exception as e:
                raise EndureException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    output={
                        "error": "Internal server error",
                        "details": str(e),
                    },
                )

        return handler
