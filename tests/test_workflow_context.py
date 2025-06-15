from app._internal.types import LogStatus, RetryMechanism, Response
import pytest
from unittest.mock import patch
from fastapi import status, HTTPException
import time


def test_successful_action_execution(workflow_context, sample_action):
    """Test successful execution of an action with proper logging"""
    input_data = {"input": "data"}
    retry_mechanism = RetryMechanism.EXPONENTIAL
    max_retries = 3

    mock_started_response = Response(status_code=201, payload={})
    mock_completed_response = Response(status_code=200, payload={})

    with patch(
        "app._internal.internal_client.InternalEndureClient.send_log"
    ) as mock_send_log:
        mock_send_log.side_effect = [
            mock_started_response.to_dict(),
            mock_completed_response.to_dict(),
        ]

        workflow_context.execute_action(
            action=sample_action,
            input_data=input_data,
            max_retries=max_retries,
            retry_mechanism=retry_mechanism,
        )

        assert mock_send_log.call_count == 2

        # Verifying the STARTED log
        started_log_call = mock_send_log.call_args_list[0]
        assert started_log_call[0][0] == "test-execution-id"
        assert started_log_call[0][1].status == LogStatus.STARTED
        assert started_log_call[0][1].input == input_data
        assert started_log_call[0][1].retry_mechanism == retry_mechanism
        assert started_log_call[0][1].max_retries == max_retries
        assert started_log_call[0][2] == sample_action.__name__

        # Verifying the COMPLETED log
        completed_log_call = mock_send_log.call_args_list[1]
        assert completed_log_call[0][0] == "test-execution-id"
        assert completed_log_call[0][1].status == LogStatus.COMPLETED
        assert completed_log_call[0][1].output == {"result": input_data}
        assert completed_log_call[0][2] == sample_action.__name__


def test_already_executed_action(workflow_context, sample_action):
    """Test handling of already executed actions"""
    input_data = {"input": "data"}
    idempotent_result = {"output": "result"}

    mock_response = Response(
        status_code=status.HTTP_208_ALREADY_REPORTED, payload=idempotent_result
    )
    with patch(
        "app._internal.internal_client.InternalEndureClient.send_log"
    ) as mock_send_log:
        mock_send_log.return_value = mock_response.to_dict()
        result = workflow_context.execute_action(
            action=sample_action,
            input_data=input_data,
            max_retries=3,
            retry_mechanism=RetryMechanism.EXPONENTIAL,
        )
        assert result == idempotent_result["output"]
        assert mock_send_log.call_count == 1


def test_action_with_retry_success(workflow_context):
    """Test action that fails initially but succeeds after retry"""
    input_data = {"input": "data"}
    action_result = {"result": "processed data"}
    attempt_count = 0

    def failing_action(input_data):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            raise ValueError("First attempt fails")
        return action_result

    retry_time = time.time()
    mock_responses = [
        Response(
            status_code=status.HTTP_201_CREATED, payload={}
        ),  # Initial STARTED log
        Response(
            status_code=status.HTTP_200_OK, payload={"retry_at": retry_time}
        ),  # First failure log
        Response(status_code=status.HTTP_200_OK, payload={}),  # Success log
    ]
    with patch(
        "app._internal.internal_client.InternalEndureClient.send_log"
    ) as mock_send_log:
        mock_send_log.side_effect = [r.to_dict() for r in mock_responses]
        result = workflow_context.execute_action(
            action=failing_action,
            input_data=input_data,
            max_retries=3,
            retry_mechanism=RetryMechanism.EXPONENTIAL,
        )
        assert result == action_result
        assert attempt_count == 2
        assert mock_send_log.call_count == 3
        failure_log_call = mock_send_log.call_args_list[1]
        assert failure_log_call[0][1].status == LogStatus.FAILED
        assert "First attempt fails" in failure_log_call[0][1].output["error"]
        success_log_call = mock_send_log.call_args_list[2]
        assert success_log_call[0][1].status == LogStatus.COMPLETED
        assert success_log_call[0][1].output == action_result


def test_action_with_http_exception(workflow_context, sample_action):
    """Test handling of HTTPException from the engine"""
    with patch(
        "app._internal.internal_client.InternalEndureClient.send_log"
    ) as mock_send_log:
        mock_send_log.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request"
        )
        with pytest.raises(RuntimeError) as exc_info:
            workflow_context.execute_action(
                action=sample_action,
                input_data={"test": "data"},
                max_retries=3,
                retry_mechanism=RetryMechanism.EXPONENTIAL,
            )
        assert "Action execution failed" in str(exc_info.value)
        assert "400" in str(exc_info.value)


def test_action_exhausts_retries(workflow_context):
    """Test action that fails and exhausts all retries"""

    def failing_action(input_data):
        raise ValueError("Action always fails")

    retry_time = time.time()
    mock_responses = [
        Response(
            status_code=status.HTTP_201_CREATED, payload={}
        ),  # Initial STARTED log
        Response(
            status_code=status.HTTP_200_OK, payload={"retry_at": retry_time}
        ),  # First failure
        Response(
            status_code=status.HTTP_200_OK, payload={"retry_at": retry_time}
        ),  # Second failure
        Response(
            status_code=status.HTTP_400_BAD_REQUEST, payload={}
        ),  # Final failure - no more retries
    ]
    with patch(
        "app._internal.internal_client.InternalEndureClient.send_log"
    ) as mock_send_log:
        mock_send_log.side_effect = [r.to_dict() for r in mock_responses]
        with pytest.raises(RuntimeError) as exc_info:
            workflow_context.execute_action(
                action=failing_action,
                input_data={"test": "data"},
                max_retries=3,
                retry_mechanism=RetryMechanism.EXPONENTIAL,
            )
        assert "Action execution failed" in str(exc_info.value)
        assert mock_send_log.call_count == 4


def test_retry_respects_timing(workflow_context):
    """Test that retry mechanism respects the timing specified by the engine"""
    input_data = {"test": "data"}
    future_retry_time = time.time() + 5

    def failing_action(input_data):
        raise ValueError("Action fails")

    mock_responses = [
        Response(
            status_code=status.HTTP_201_CREATED, payload={}
        ),  # Initial STARTED log
        Response(
            status_code=status.HTTP_200_OK,
            payload={"retry_at": future_retry_time},
        ),  # Failure with future retry time
        Response(
            status_code=status.HTTP_400_BAD_REQUEST, payload={}
        ),  # Final failure
    ]
    with patch(
        "app._internal.internal_client.InternalEndureClient.send_log"
    ) as mock_send_log:
        mock_send_log.side_effect = [r.to_dict() for r in mock_responses]
        with patch("time.sleep") as mock_sleep:
            try:
                workflow_context.execute_action(
                    action=failing_action,
                    input_data=input_data,
                    max_retries=3,
                    retry_mechanism=RetryMechanism.EXPONENTIAL,
                )
            except RuntimeError:
                pass
            mock_sleep.assert_called_once()
            sleep_duration = mock_sleep.call_args[0][0]
            assert sleep_duration > 0 and sleep_duration <= 5
            assert mock_send_log.call_count == 3
