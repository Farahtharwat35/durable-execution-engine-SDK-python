import os
import requests
from ..types import Log, Response


class InternalEndureClient:

    _base_url = os.getenv("DURABLE_ENGINE_BASE_URL")

    @classmethod
    def send_log(self, execution_id: str, log: Log, action_name: str):
        """
        Sends a log message to the Durable Execution Engine.

        Args:
            execution_id (str): The ID of the execution context.
            log (Log): The log message object to send.
            action_name (str): The name of the action.

        Returns:
            dict: A dictionary containing the response from the Durable Execution Engine.

        Raises:
            ValueError: If DURABLE_ENGINE_BASE_URL is not set or if required parameters are missing.
            requests.exceptions.HTTPError: If the request fails.
        """  # noqa: E501
        if not self._base_url:
            raise ValueError(
                "DURABLE_ENGINE_BASE_URL is not set in environment variables."
            )

        if not execution_id or not log or not action_name:
            raise ValueError(
                "execution_id, log, and action_name must be provided."
            )

        url = f"{self._base_url}/executions/execution/{execution_id}/log/{action_name}"
        headers = {"Content-Type": "application/json"}
        payload = log.to_dict()
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        response = Response(
            status_code=response.status_code,
            payload=response.json(),
        )
        return response.to_dict()

    @classmethod
    def mark_execution_as_running(self, execution_id: str):
        """
        Marks an execution as running in the Durable Execution Engine.

        Args:
            execution_id (str): The ID of the execution context.

        Returns:
            dict: A dictionary containing the response from the Durable Execution Engine.

        Raises:
            ValueError: If DURABLE_ENGINE_BASE_URL is not set or if execution_id is missing.
            requests.exceptions.HTTPError: If the request fails.
        """
        if not self._base_url:
            raise ValueError(
                "DURABLE_ENGINE_BASE_URL is not set in environment variables."
            )

        if not execution_id:
            raise ValueError("execution_id must be provided.")

        url = f"{self._base_url}/executions/{execution_id}/started"
        headers = {"Content-Type": "application/json"}
        response = requests.patch(url, headers=headers)
        response.raise_for_status()
        response = Response(
            status_code=response.status_code,
        )
        return response.to_dict()
