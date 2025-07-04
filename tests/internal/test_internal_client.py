import os
from unittest.mock import patch

import pytest
from fastapi import status

from app._internal.internal_client import InternalEndureClient
from app.types import Log, LogStatus, Response


class TestInternalClient:

    @pytest.fixture
    def mock_response(self):
        return Response(
            status_code=status.HTTP_201_CREATED,
            payload={"message": "Log sent successfully"},
        )

    def test_send_log_success(self, sample_log, mock_response):
        """Test successful log sending with proper response handling"""
        with patch("requests.patch") as mock_patch:
            mock_patch.return_value.status_code = status.HTTP_201_CREATED
            mock_patch.return_value.json.return_value = mock_response.payload

            result = InternalEndureClient.send_log(
                execution_id="test-execution-id",
                log=sample_log,
                action_name="test_action",
            )

            mock_patch.assert_called_once()
            call_args = mock_patch.call_args
            assert (
                call_args[0][0]
                == f"{InternalEndureClient._base_url}/executions/test-execution-id/log/test_action"
            )
            assert call_args[1]["headers"] == {
                "Content-Type": "application/json"
            }
            assert call_args[1]["json"] == sample_log.to_dict()

            assert result["status_code"] == status.HTTP_201_CREATED
            assert result["payload"] == mock_response.payload

    def test_send_log_missing_env_var(self):
        """Test error handling when DURABLE_ENGINE_BASE_URL is not set"""
        # temporarily remove the environment variable for this test
        original_url = os.environ.pop("DURABLE_ENGINE_BASE_URL", None)
        original_base_url = InternalEndureClient._base_url
        InternalEndureClient._base_url = None

        try:
            with pytest.raises(ValueError) as exc_info:
                InternalEndureClient.send_log(
                    execution_id="test-execution-id",
                    log=Log(status=LogStatus.STARTED),
                    action_name="test_action",
                )
            assert "DURABLE_ENGINE_BASE_URL is not set" in str(exc_info.value)
        finally:
            # restoring the environment variable and base_url
            if original_url:
                os.environ["DURABLE_ENGINE_BASE_URL"] = original_url
            InternalEndureClient._base_url = original_base_url

    def test_send_log_invalid_inputs(self):
        """Test error handling for invalid input parameters"""
        # none log
        with pytest.raises(ValueError) as exc_info:
            InternalEndureClient.send_log(
                execution_id="test-execution-id",
                log=None,
                action_name="test_action",
            )
        assert "log and action_name must be provided" in str(exc_info.value)

        # empty action_name
        with pytest.raises(ValueError) as exc_info:
            InternalEndureClient.send_log(
                execution_id="test-execution-id",
                log=Log(status=LogStatus.STARTED),
                action_name="",
            )
        assert "log and action_name must be provided" in str(exc_info.value)

    def test_send_log_http_error(self, sample_log):
        """Test handling of HTTP errors from the engine"""
        with patch("requests.patch") as mock_patch:
            mock_patch.side_effect = Exception("HTTP Error")

            with pytest.raises(Exception) as exc_info:
                InternalEndureClient.send_log(
                    execution_id="test-execution-id",
                    log=sample_log,
                    action_name="test_action",
                )
            assert "HTTP Error" in str(exc_info.value)

    def test_mark_execution_as_running_success(self):
        """Test successful execution marking"""
        with patch("requests.patch") as mock_patch:
            mock_patch.return_value.status_code = status.HTTP_200_OK
            mock_patch.return_value.json.return_value = {}

            result = InternalEndureClient.mark_execution_as_running(
                "test-execution-id"
            )

            mock_patch.assert_called_once()
            call_args = mock_patch.call_args
            assert (
                call_args[0][0]
                == f"{InternalEndureClient._base_url}/executions/test-execution-id/started"
            )
            assert call_args[1]["headers"] == {
                "Content-Type": "application/json"
            }

            assert result["status_code"] == status.HTTP_200_OK
            assert result["payload"] == {}

    def test_send_log_empty_body(self, sample_log):
        """Test handling of 200 OK with empty body (non-JSON)."""

        class MockResponse:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                raise ValueError("No JSON")

        with patch("requests.patch", return_value=MockResponse()):
            result = InternalEndureClient.send_log(
                execution_id="test-execution-id",
                log=sample_log,
                action_name="test_action",
            )
            assert result["status_code"] == 200
            assert result["payload"] == {}
