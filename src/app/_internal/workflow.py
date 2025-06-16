import asyncio
from typing import Any, Callable, Union, get_type_hints , get_origin, get_args

from fastapi import Request, status, HTTPException, types
from pydantic import ValidationError, create_model

from app.workflow_context import WorkflowContext

from .internal_client import InternalEndureClient
from .types import EndureException


class Workflow:
    """
    Represents a workflow function that can be executed through a FastAPI endpoint.

    A Workflow encapsulates a function and manages its execution through the durable
    execution engine. It extracts type information from the function signature
    and provides a FastAPI-compatible handler route.

    Attributes:
        func (Callable): The workflow function to be executed.
        name (str): The name of the workflow (derived from function name).
        retention_period (int, optional): Number of days to retain workflow execution history.
        input (Any): The input type of the workflow function (from type hints).
        output (Any): The return type of the workflow function (from type hints).
    """  # noqa: E501

    def __init__(self, func: Callable, retention_period: int = None):
        """
        Initialize a new Workflow instance.

        Args:
            func (Callable): The workflow function to wrap. Must have parameters
                             'input' and 'ctx' where 'ctx' is a WorkflowContext.
            retention_period (int, optional): Number of days to retain workflow execution
                                            history and state. Default is None.
        """  # noqa: E501
        self.func = func
        self.name = func.__name__
        self.retention_period = retention_period
        self.input, self.output = self._get_io(func)

    def _get_type_description(self, typ):
        if typ is Any:
            return "Any"
        # Normalize NoneType to "None"
        if typ is type(None):
            return "None"

        origin = get_origin(typ)
        args = get_args(typ)

        # Handle Union and | (UnionType in Python 3.10+)
        if origin in (Union, types.UnionType):
            type_names = [self._get_type_description(arg) for arg in args]
            return " | ".join(sorted(type_names, key=lambda x: (x == "None", x)))
        
        # Case: User-defined class
        if hasattr(typ, '__annotations__') and not origin:
            fields = getattr(typ, '__annotations__', {})
            return {
                name: self._get_type_description(t)
                for name, t in fields.items()
            }

        # Case: Generic container like list[Class], dict[str, Class], etc.
        if origin:
            origin_name = origin.__name__ if hasattr(origin, '__name__') else str(origin)

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
        Extract input and output type information from the function's type hints.

        Args:
            func (Callable): The workflow function to analyze.

        Returns:
            tuple: A tuple containing (input_type, output_type). If type hints
                  aren't provided, Any is used as a fallback.
        """  # noqa: E501
        hints = get_type_hints(func)
        input_type = hints.get("input", Any)
        output_type = hints.get("return", Any)

        return self._get_type_description(input_type), self._get_type_description(output_type)
    
   
    def get_handler_route(self):
        """
        Generate a FastAPI-compatible route handler for the workflow function.

        Creates a dynamic Pydantic model for request validation and an async handler
        that processes incoming requests, sets up the workflow context, executes
        the workflow function, and returns the result.

        Returns:
            Callable: An async function that can be registered as a FastAPI route handler.

        Raises:
            HTTPException: With status code 400 for validation errors or 500 for
                          other exceptions during handler creation or execution.

        Notes:
            - The handler expects a JSON request with 'execution_id' and 'input' fields.
            - Both synchronous and asynchronous workflow functions are supported.
        """  # noqa: E501
      
        async def handler(request: Request):
            try:
                body = await request.json()
                ctx = WorkflowContext(execution_id=body['execution_id'])
                InternalEndureClient.mark_execution_as_running(
                    body['execution_id']
                )
                result = self.func(ctx, body['input'])
                if asyncio.iscoroutine(result):
                    result = await result
                return {"output": result}
            except HTTPException as he:
                raise EndureException(
                    status_code=he.status_code,
                    output={
                        "error":  he.detail,
                        "details": he.errors(),
                    },
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
