from typing import Callable, get_type_hints, Any
from fastapi import Request, HTTPException, status
from pydantic.typing import create_model
import asyncio
from pydantic import ValidationError, create_model
from .workflow_context import WorkflowContext
class Workflow:
    def __init__(self, func: Callable):
        self.func = func
        self.name = func.__name__
        self.input , self.output = self._get_io(func)

    def _get_io(self, func):
        hints = get_type_hints(func)
        return hints.get('input', Any) , hints.get('return', Any)

    def get_handler_route(self):
        This method generates a route handler that can be used in a FastAPI application.
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
                return result
            
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
       