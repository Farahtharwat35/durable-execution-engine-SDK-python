from app.types import LogStatus, RetryMechanism, Response
import pytest
from unittest.mock import patch
from fastapi import status, HTTPException
import time
from pydantic import ValidationError, BaseModel
import requests


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
    """Test action that fails with a generic Exception
    (not ValueError/ValidationError) and succeeds after retry."""
    input_data = {"input": "data"}
    action_result = {"result": "processed data"}
    attempt_count = 0

    class CustomException(Exception):
        pass

    def failing_action(input_data):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            raise CustomException("First attempt fails")
        return action_result

    retry_time = time.time()
    mock_responses = [
        Response(status_code=status.HTTP_201_CREATED, payload={}),
        Response(
            status_code=status.HTTP_200_OK, payload={"retry_at": retry_time}
        ),
        Response(status_code=status.HTTP_200_OK, payload={}),
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


def test_action_with_http_exception(workflow_context, sample_action):
    """Test that HTTPException from the engine is re-raised immediately (not retried)."""
    with patch(
        "app._internal.internal_client.InternalEndureClient.send_log"
    ) as mock_send_log:
        mock_send_log.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request"
        )
        with pytest.raises(HTTPException) as exc_info:
            workflow_context.execute_action(
                action=sample_action,
                input_data={"test": "data"},
                max_retries=3,
                retry_mechanism=RetryMechanism.EXPONENTIAL,
            )
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Bad request"


def test_action_exhausts_retries(workflow_context):
    """Test that a generic Exception (not ValueError/ValidationError) after all retries raises EndureException."""

    class CustomException(Exception):
        pass

    def failing_action(input_data):
        raise CustomException("Always fails")

    retry_time = time.time()
    mock_responses = [
        Response(status_code=status.HTTP_201_CREATED, payload={}),
        Response(
            status_code=status.HTTP_200_OK, payload={"retry_at": retry_time}
        ),
        Response(
            status_code=status.HTTP_200_OK, payload={"retry_at": retry_time}
        ),
        Response(status_code=status.HTTP_400_BAD_REQUEST, payload={}),
    ]
    with patch(
        "app._internal.internal_client.InternalEndureClient.send_log"
    ) as mock_send_log:
        mock_send_log.side_effect = [r.to_dict() for r in mock_responses]
        with pytest.raises(Exception) as exc_info:
            workflow_context.execute_action(
                action=failing_action,
                input_data={"test": "data"},
                max_retries=3,
                retry_mechanism=RetryMechanism.EXPONENTIAL,
            )
        assert (
            exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        assert (
            exc_info.value.output["error"]
            == "Action failed after reaching max retries"
        )


def test_retry_respects_timing(workflow_context):
    """Test that retry mechanism respects the timing specified by the engine."""
    input_data = {"test": "data"}
    future_retry_time = time.time() + 5

    class CustomException(Exception):
        pass

    def failing_action(input_data):
        raise CustomException("Action fails")

    mock_responses = [
        Response(status_code=status.HTTP_201_CREATED, payload={}),
        Response(
            status_code=status.HTTP_200_OK,
            payload={"retry_at": future_retry_time},
        ),
        Response(
            status_code=status.HTTP_200_OK,
            payload={"retry_at": future_retry_time},
        ),
        Response(
            status_code=status.HTTP_200_OK,
            payload={"retry_at": future_retry_time},
        ),
        Response(status_code=status.HTTP_400_BAD_REQUEST, payload={}),
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
            except Exception:
                pass
            assert mock_sleep.call_count == 3
            sleep_duration = mock_sleep.call_args[0][0]
            assert sleep_duration > 0 and sleep_duration <= 5
            assert mock_send_log.call_count == 4


def test_action_with_value_error(workflow_context):
    """Test that ValueError from the action is re-raised immediately (not retried) and logs FAILED."""

    def action_raises_value_error(input_data):
        raise ValueError("Immediate failure")

    mock_responses = [
        Response(status_code=status.HTTP_201_CREATED, payload={}),
        Response(status_code=status.HTTP_200_OK, payload={}),
    ]
    with patch(
        "app._internal.internal_client.InternalEndureClient.send_log"
    ) as mock_send_log:
        mock_send_log.side_effect = [r.to_dict() for r in mock_responses]
        with pytest.raises(ValueError):
            workflow_context.execute_action(
                action=action_raises_value_error,
                input_data={},
                max_retries=3,
                retry_mechanism=RetryMechanism.EXPONENTIAL,
            )
        assert mock_send_log.call_count == 2
        call_args_list = mock_send_log.call_args_list
        assert call_args_list[0][0][1].status == LogStatus.STARTED
        assert call_args_list[1][0][1].status == LogStatus.FAILED
        assert "Immediate failure" in call_args_list[1][0][1].output["error"]


def test_action_with_validation_error(workflow_context):
    """Test that ValidationError from the action is re-raised immediately (not retried) and logs FAILED."""

    class DummyModel(BaseModel):
        x: int

    def action_raises_validation_error(input_data):
        raise ValidationError([], model=DummyModel)

    mock_started_response = Response(
        status_code=status.HTTP_201_CREATED, payload={}
    )
    mock_failed_response = Response(status_code=status.HTTP_200_OK, payload={})

    with patch(
        "app._internal.internal_client.InternalEndureClient.send_log"
    ) as mock_send_log:
        mock_send_log.side_effect = [
            mock_started_response.to_dict(),
            mock_failed_response.to_dict(),
        ]

        with pytest.raises(ValidationError):
            workflow_context.execute_action(
                action=action_raises_validation_error,
                input_data={},
                max_retries=3,
                retry_mechanism=RetryMechanism.EXPONENTIAL,
            )

        assert mock_send_log.call_count == 2
        started_log = mock_send_log.call_args_list[0][0][1]
        failed_log = mock_send_log.call_args_list[1][0][1]
        assert hasattr(started_log, "status")
        assert hasattr(failed_log, "status")
        assert started_log.status == LogStatus.STARTED
        assert failed_log.status == LogStatus.FAILED
        assert "validation error" in failed_log.output["error"].lower()


def test_action_with_requests_exception(workflow_context):
    """Test that requests.exceptions.RequestException
    is re-raised immediately (not retried) and only logs STARTED."""

    def action_raises_requests_exception(input_data):
        raise requests.exceptions.RequestException("Request failed")

    mock_response = Response(status_code=status.HTTP_201_CREATED, payload={})
    with patch(
        "app._internal.internal_client.InternalEndureClient.send_log"
    ) as mock_send_log:
        mock_send_log.return_value = mock_response.to_dict()
        with pytest.raises(requests.exceptions.RequestException):
            workflow_context.execute_action(
                action=action_raises_requests_exception,
                input_data={},
                max_retries=3,
                retry_mechanism=RetryMechanism.EXPONENTIAL,
            )
        assert mock_send_log.call_count == 1
        call_args_list = mock_send_log.call_args_list
        assert call_args_list[0][0][1].status == LogStatus.STARTED


def test_value_error_in_first_send_log(workflow_context):
    """Test that ValueError in the first send_log is raised and not logged as FAILED."""

    def dummy_action(input_data):
        return "should not be called"

    with patch(
        "app._internal.internal_client.InternalEndureClient.send_log"
    ) as mock_send_log:
        mock_send_log.side_effect = ValueError("First log error")
        with pytest.raises(ValueError) as exc_info:
            workflow_context.execute_action(
                action=dummy_action,
                input_data={},
                max_retries=3,
                retry_mechanism=RetryMechanism.EXPONENTIAL,
            )
        assert "First log error" in str(exc_info.value)
        assert mock_send_log.call_count == 1
