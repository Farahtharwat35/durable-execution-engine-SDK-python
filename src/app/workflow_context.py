import time
import logging
import asyncio
from fastapi import status
import requests
from app._internal.internal_client import (
    InternalEndureClient,
)
from app.types import (
    Log,
    LogStatus,
    RetryMechanism,
    EndureException,
)
from pydantic import ValidationError


class WorkflowContext:
    """
    Provides context for workflow execution and durable action management.

    This class serves as the bridge between workflow functions and the durable execution
    engine, providing exactly-once execution semantics for workflow actions. It manages:
    - Action execution state tracking
    - Automatic retries with configurable mechanisms
    - Idempotency through result caching
    - Communication with the durable execution engine

    Attributes:
        execution_id (str): The unique identifier for the workflow execution,
                          used to correlate all actions within a workflow.

    Example:
        ```python
        @service.workflow()
        def process_order(input: dict, ctx: WorkflowContext):
            # Execute an action with retry capability
            result = ctx.execute_action(
                action=process_payment,
                input_data={"amount": 100},
                max_retries=3,
                retry_mechanism=RetryMechanism.EXPONENTIAL_BACKOFF
            )
            return result
        ```
    """

    def __init__(self, execution_id: str):
        """
        Initialize a new workflow context.

        Args:
            execution_id (str): The unique identifier for this workflow execution.
                              This ID is used to:
                              - Track action execution states
                              - Correlate logs in the durable engine
                              - Enable idempotent execution
                              - Manage retries across process restarts
        """
        self.execution_id = execution_id

    async def execute_action(
        self,
        action: callable,
        input_data,
        max_retries: int,
        retry_mechanism: RetryMechanism,
        action_name: str = None,
    ) -> any:
        """
        Execute an action with durability guarantees and automatic retry capabilities.

        This method ensures exactly-once execution semantics by:
        1. Logging action state to the durable engine
        2. Handling idempotency checks
        3. Managing retries with configurable backoff
        4. Preserving execution results

        Execution States:
        - STARTED: Initial action execution attempt
        - COMPLETED: Successful execution
        - FAILED: Failed attempt, may trigger retry

        Retry Behavior:
        - Retries are managed by the durable engine
        - Sleep duration between retries is determined by retry_mechanism
        - Retries continue until success or max_retries is reached

        Args:
            action (callable): The function to execute. Must accept input_data as its only parameter.
            input_data: The input to pass to the action function. Will be preserved for retries.
            max_retries (int): Maximum number of retry attempts after initial failure.
            retry_mechanism (RetryMechanism): Strategy for timing retries:
                                            - LINEAR_BACKOFF
                                            - EXPONENTIAL_BACKOFF
                                            etc.
            action_name (str, optional): Custom name for the action in logs. If not provided,
                                       uses action.__name__.

        Returns:
            any: Either:
                - The result of a successful action execution
                - The cached result if action was previously completed
                - Empty dict if no result available but marked complete

        Raises:
            RuntimeError: If:
                - Engine communication fails
                - Action fails and max retries are exhausted
                - retry_at time is missing from engine response
                - Any unhandled exception during execution

        Communication with Engine:
        - Uses InternalEndureClient.send_log for state updates
        - Recognizes response codes:
            - 201/200: Continue execution
            - 208: Return cached result
            - Other: Error condition

        Example:
            ```python
            def process_payment(input_data: dict) -> dict:
                # Process payment logic
                return {"status": "success"}

            # In a workflow function:
            result = ctx.execute_action(
                action=process_payment,
                input_data={"amount": 100},
                max_retries=3,
                retry_mechanism=RetryMechanism.EXPONENTIAL_BACKOFF
            )
            ```
        """
        log = Log(
            status=LogStatus.STARTED,
            input=input_data,
            retry_mechanism=retry_mechanism,
            max_retries=max_retries,
        )
        name = action_name if action_name is not None else action.__name__
        engine_response = InternalEndureClient.send_log(
            self.execution_id, log, name
        )
        if not engine_response:
            raise ValueError(
                "Base URL is not set in environment variables or missing required parameters (log or action_name)."
            )
        status_code = engine_response["status_code"]
        match status_code:
            case status.HTTP_201_CREATED | status.HTTP_200_OK:
                attempt = 0
                while attempt <= max_retries:
                    try:
                        try:
                            if asyncio.iscoroutinefunction(action):
                                result = await action(input_data)
                            else:
                                result = action(input_data)
                        except (ValueError, ValidationError) as e:
                            InternalEndureClient.send_log(
                                self.execution_id,
                                Log(
                                    status=LogStatus.FAILED,
                                    output={"error": str(e)},
                                ),
                                name,
                            )
                            logging.info(
                                f"WORKFLOW DEBUG: About to raise exception of type {type(e)}: {e}"
                            )
                            raise
                        log = Log(
                            status=LogStatus.COMPLETED,
                            output=result,
                        )
                        InternalEndureClient.send_log(
                            self.execution_id,
                            log,
                            name,
                        )
                        return result
                    except (
                        ValueError,
                        ValidationError,
                        requests.exceptions.RequestException,
                    ) as e:
                        logging.debug(
                            f"DEBUG: Caught exception of type {type(e)}: {e}"
                        )
                        raise
                    except Exception as e:
                        if attempt == max_retries:
                            raise EndureException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                output={
                                    "error": str(
                                        "Action failed after reaching max retries"
                                    )
                                },
                            )
                        log = Log(
                            status=LogStatus.FAILED,
                            output={"error": str(e)},
                        )
                        engine_response = InternalEndureClient.send_log(
                            self.execution_id, log, name
                        )
                        attempt += 1
                        retry_at_unix = engine_response.get("payload", {}).get(
                            "retry_at"
                        )
                        if retry_at_unix:
                            sleep_seconds = retry_at_unix - time.time()
                            if sleep_seconds > 0:
                                time.sleep(sleep_seconds)
            case status.HTTP_208_ALREADY_REPORTED:
                output = engine_response.get("payload", {}).get("output")
                return output if output else {}
