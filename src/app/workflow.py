from typing import Callable, get_type_hints, Any
from fastapi import Request, HTTPException, status
from pydantic.typing import create_model
import asyncio
from pydantic import ValidationError, create_model
from .workflow_context import WorkflowContext
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
    """
    def __init__(self, func: Callable, retention_period: int = None):
        """
        Initialize a new Workflow instance.
        
        Args:
            func (Callable): The workflow function to wrap. Must have parameters
                             'input' and 'ctx' where 'ctx' is a WorkflowContext.
            retention_period (int, optional): Number of days to retain workflow execution
                                            history and state. Default is None.
        """
        self.func = func
        self.name = func.__name__
        self.retention_period = retention_period
        self.input, self.output = self._get_io(func)

    def _get_io(self, func):
        """
        Extract input and output type information from the function's type hints.
        
        Args:
            func (Callable): The workflow function to analyze.
            
        Returns:
            tuple: A tuple containing (input_type, output_type). If type hints
                  aren't provided, Any is used as a fallback.
        """
        hints = get_type_hints(func)
        return hints.get('input', Any) , hints.get('return', Any)

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
            - TODO: Integration with the durable execution engine for workflow state tracking.
        """
        try:
            FullRequest = create_model(
                f"{self.name}Request",
                execution_id=(str, ...),
                input=(self.input, ...)
            )
            async def handler(request: Request):
                body = await request.json()
                full = FullRequest(**body)
                ctx = WorkflowContext(execution_id=full.execution_id)
                #TODO: hit started endpoint in engine (log in a util file) ,  ALSO URL OF THE ENGINE WILL BE NEEDED , NEED TO FIND A WAY
                result = self.func(ctx, full.input)
                if asyncio.iscoroutine(result):
                    result = await result
                return {"output": result}
            
        except ValidationError as ve:
            print(f"Validation error: {ve}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ve.errors()
            )

        except Exception as e:
            print(f"Error creating handler route: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        return handler
       