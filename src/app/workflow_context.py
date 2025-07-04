import asyncio
import logging
import time

import requests
from fastapi import status
from pydantic import ValidationError

from app._internal.internal_client import InternalEndureClient
from app._internal.utils import serialize_data
from app.types import EndureException, Log, LogStatus, RetryMechanism


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
            input=serialize_data(input_data),
            retry_mechanism=retry_mechanism,
            max_retries=max_retries,
        )
        name = action_name if action_name is not None else action.__name__
        logging.info("Sending log for action: {}".format(log))
        engine_response = InternalEndureClient.send_log(
            self.execution_id, log, name
        )
        logging.info("Engine response: {}".format(engine_response))
        if not engine_response:
            logging.error(
                "CRITICAL ERROR: Engine response is None or empty. "
                "This indicates a communication failure with the durable engine."
            )
            raise ValueError(
                "Base URL is not set in environment variables or missing required parameters (log or action_name)."
            )

        logging.info(
            f"Detailed engine response - Status: {engine_response.get('status_code')}, "
            f"Payload: {engine_response.get('payload')}, "
            f"Headers: {engine_response.get('headers', {})}"
        )

        status_code = engine_response["status_code"]
        logging.info(f"Processing status code: {status_code}")

        match status_code:
            case status.HTTP_201_CREATED | status.HTTP_200_OK:
                logging.info(
                    f"Status {status_code} - Proceeding with action execution"
                )
                while True:
                    try:
                        try:
                            logging.info(
                                "Executing action: {}".format(action.__name__)
                            )
                            if asyncio.iscoroutinefunction(action):
                                result = await action(input_data)
                            else:
                                result = action(input_data)
                            logging.info("Action result: {}".format(result))
                        except (ValueError, ValidationError) as e:
                            logging.error(
                                f"VALIDATION ERROR in action {action.__name__}: {type(e).__name__}: {e}"
                            )
                            engine_response = InternalEndureClient.send_log(
                                self.execution_id,
                                Log(
                                    status=LogStatus.FAILED,
                                    output=serialize_data({"error": str(e)}),
                                ),
                                name,
                            )
                            logging.info(
                                "Engine response after validation error: {}".format(
                                    engine_response
                                )
                            )
                            logging.error(
                                f"WORKFLOW DEBUG: About to raise exception of type {type(e)}: {e}"
                            )
                            raise
                        log = Log(
                            status=LogStatus.COMPLETED,
                            output=serialize_data(result),
                        )
                        logging.info(
                            "Sending log for completed action: {}".format(log)
                        )
                        engine_response = InternalEndureClient.send_log(
                            self.execution_id,
                            log,
                            name,
                        )
                        logging.info(
                            "Engine response after completion: {}".format(
                                engine_response
                            )
                        )
                        logging.info("Returning result: {}".format(result))
                        return result
                    except (
                        ValueError,
                        ValidationError,
                        requests.exceptions.RequestException,
                    ) as e:
                        logging.error(
                            f"CRITICAL ERROR: Caught exception of type {type(e)}: {e}"
                        )
                        logging.error(
                            f"Exception details - Args: {e.args}, Traceback: {type(e).__name__}"
                        )
                        raise
                    except Exception as e:
                        logging.error(
                            f"UNEXPECTED ERROR in action {action.__name__}: {type(e).__name__}: {e}"
                        )
                        logging.error(
                            f"Error details - Args: {e.args}, Traceback: {type(e).__name__}"
                        )
                        log = Log(
                            status=LogStatus.FAILED,
                            output=serialize_data({"error": str(e)}),
                        )
                        logging.info(
                            "Sending log for failed action: {}".format(log)
                        )
                        engine_response = InternalEndureClient.send_log(
                            self.execution_id, log, name
                        )
                        logging.info(
                            "Engine response after failure: {}".format(
                                engine_response
                            )
                        )
                        engine_status = engine_response.get("status_code")
                        logging.info(
                            f"Engine status after failure: {engine_status}"
                        )

                        if engine_status in [
                            status.HTTP_400_BAD_REQUEST,
                            status.HTTP_404_NOT_FOUND,
                            status.HTTP_409_CONFLICT,
                        ]:
                            logging.error(
                                f"ENGINE ERROR: Received {engine_status} from engine. "
                                f"Original error: {type(e).__name__}: {e}"
                            )
                            if engine_status == status.HTTP_409_CONFLICT:
                                logging.error(
                                    "Execution Paused or Terminated , no retries will be attempted."
                                )
                                raise EndureException(
                                    status_code=engine_status,
                                    output=serialize_data(
                                        {
                                            "error": str(
                                                "Execution Paused or Terminated"
                                            )
                                        }
                                    ),
                                )
                            raise EndureException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                output=serialize_data(
                                    {
                                        "error": str(
                                            "Action failed after reaching max retries"
                                        )
                                    }
                                ),
                            )
                        retry_at_unix = engine_response.get("payload", {}).get(
                            "retry_at"
                        )
                        logging.info("Retry at unix: {}".format(retry_at_unix))
                        if retry_at_unix:
                            sleep_seconds = retry_at_unix - time.time()
                            if sleep_seconds > 0:
                                logging.info(
                                    "Sleeping for {} seconds".format(
                                        sleep_seconds
                                    )
                                )
                                time.sleep(sleep_seconds)
                            else:
                                logging.warning(
                                    f"Retry time {retry_at_unix} is in the past. "
                                    f"Current time: {time.time()}"
                                )
                        else:
                            logging.error(
                                f"CRITICAL ERROR: No retry_at time provided by "
                                f"engine for retryable status {engine_status}. "
                                f"Engine response: {engine_response}"
                            )
                            raise RuntimeError(
                                f"Engine did not provide retry_at time for retryable status {engine_status}. "
                                f"Response: {engine_response}"
                            )
            case status.HTTP_208_ALREADY_REPORTED:
                logging.info(
                    "Returning cached result: {}".format(engine_response)
                )
                output = engine_response.get("payload", {}).get("output")
                return output if output else {}
            case _:
                logging.error(
                    f"UNEXPECTED STATUS CODE: {status_code}. "
                    f"Full response: {engine_response}"
                )
                raise RuntimeError(
                    f"Unexpected status code {status_code} from engine: {engine_response}"
                )
