import time

from fastapi import HTTPException, status

from app._internal.internal_client import (
    InternalEndureClient,
)
from app._internal.types import (
    Log,
    LogStatus,
    RetryMechanism,
)


class WorkflowContext:
    """
    Provides context for workflow execution and durable action management.

    This class serves as the bridge between workflow functions and the durable execution
    engine. It provides mechanisms for executing actions with durability guarantees,
    including automatic retry logic and execution state tracking.

    Attributes:
        execution_id (str): The unique identifier for the workflow execution.
    """

    def __init__(self, execution_id: str):
        """
        Initialize a new workflow context.

        Args:
            execution_id (str): The unique identifier for this workflow execution.
                               Used for tracking and correlating actions.
        """  # noqa: E501
        self.execution_id = execution_id

    def execute_action(
        self,
        action: callable,
        input_data,
        max_retries: int,
        retry_mechanism: RetryMechanism,
    ) -> any:
        """
        Execute an action with durability guarantees.

        This method provides durability by tracking action execution state in the
        durable execution engine. It handles automatic retries based on the configured
        retry mechanism and ensures exactly-once execution semantics.

        Execution Flow:
        1. Logs the start of the action execution to the engine
        2. Executes the action with the provided input
        3. Logs success/failure of the action
        4. Handles retries according to the retry mechanism if failures occur
        5. Returns the action result or cached result from previous execution

        Args:
            action (callable): The function to execute.
            input_data: The input data to pass to the action function.
            max_retries (int): Maximum number of retry attempts for the action.
            retry_mechanism (RetryMechanism): Strategy to use for retrying failed actions.
                                             Controls backoff timing and behavior.

        Returns:
            any: The result of the action execution, or the cached result if the
                 action was already executed successfully.

        Raises:
            RuntimeError: If the action execution fails and cannot be retried,
                         or if there are issues with the execution engine.

        Notes:
            - The method communicates with the durable execution engine to ensure
              the action is executed exactly once, even across process restarts.
            - If the action was already successfully executed (idempotency), the
              cached result is returned without re-executing the action.
            - For failed actions, retry timing is controlled by the execution engine
              based on the specified retry mechanism.
        """  # noqa: E501
        try:
            log = Log(
                status=LogStatus.STARTED,
                input=input_data,
                retry_mechanism=retry_mechanism,
                max_retries=max_retries,
            )
            engine_response = InternalEndureClient.send_log(
                self.execution_id, log, action.__name__
            )
            if not engine_response:
                raise RuntimeError("Failed to mark execution as running.")
            status_code = engine_response["status_code"]
            match status_code:
                case status.HTTP_201_CREATED | status.HTTP_200_OK:
                    result = action(input_data)
                    log = Log(
                        status=LogStatus.COMPLETED,
                        output=result,
                    )
                    InternalEndureClient.send_log(
                        self.execution_id,
                        log,
                        action.__name__,
                    )
                    return result
                case status.HTTP_208_ALREADY_REPORTED:
                    output = engine_response.get("payload", {}).get("output")
                    return output if output else {}

        except HTTPException as e:
            raise RuntimeError(
                f"Action execution failed: {str(e)} , status code: {e.status_code}"
            )

        except Exception as e:
            log = Log(
                status=LogStatus.FAILED,
                output={"error": str(e)},
            )
            engine_response = InternalEndureClient.send_log(
                self.execution_id, log, action.__name__
            )
            status_code = engine_response["status_code"]
            # Retry logic based on the retry mechanism
            while status_code == status.HTTP_200_OK:
                try:
                    retry_at_unix = engine_response.get("payload", {}).get(
                        "retry_at"
                    )
                    if not retry_at_unix:
                        raise RuntimeError(
                            "Missing retry_at in response payload"
                        )
                    sleep_seconds = retry_at_unix - time.time()
                    if sleep_seconds > 0:
                        time.sleep(sleep_seconds)
                    result = action(input_data)
                    log = Log(
                        status=LogStatus.COMPLETED,
                        output=result,
                    )
                    InternalEndureClient.send_log(
                        self.execution_id,
                        log,
                        action.__name__,
                    )
                    return result
                except Exception as e:
                    log = Log(
                        status=LogStatus.FAILED,
                        output={"error": str(e)},
                    )
                    engine_response = InternalEndureClient.send_log(
                        self.execution_id,
                        log,
                        action.__name__,
                    )
                    status_code = engine_response["status_code"]
                    if status_code != status.HTTP_200_OK:
                        raise RuntimeError(
                            f"Action execution failed: {str(e)}"
                        )
