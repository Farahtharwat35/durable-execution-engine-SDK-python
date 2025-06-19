import os
import logging
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
        try:
            if not self._base_url:
                raise ValueError(
                    "DURABLE_ENGINE_BASE_URL is not set in environment variables."
                )

            if not log or not action_name:
                raise ValueError("log and action_name must be provided.")

            url = (
                f"{self._base_url}/executions/{execution_id}/log/{action_name}"
            )
            headers = {"Content-Type": "application/json"}
            payload = log.to_dict()
            response = requests.patch(url, headers=headers, json=payload)
            response.raise_for_status()
            try:
                response_payload = response.json()
            except ValueError:
                response_payload = {}
            response = Response(
                status_code=response.status_code,
                payload=response_payload,
            )
        except requests.exceptions.HTTPError as e:
            try:
                error_payload = e.response.json()
            except Exception:
                error_payload = {}
            response = Response(
                status_code=e.response.status_code,
                payload=error_payload,
            )
        except requests.exceptions.RequestException as e:
            logging.error(
                "Engine is unreachable. Aborting retries: {}".format(e)
            )
            raise e
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
        try:
            if not self._base_url:
                raise ValueError(
                    "DURABLE_ENGINE_BASE_URL is not set in environment variables."
                )
            url = f"{self._base_url}/executions/{execution_id}/started"
            headers = {"Content-Type": "application/json"}
            response = requests.patch(url, headers=headers)
            response.raise_for_status()
            response = Response(
                status_code=response.status_code,
            )
        except requests.exceptions.HTTPError as e:
            response = Response(
                status_code=e.response.status_code,
            )
        except requests.exceptions.RequestException as e:
            logging.error(
                "Engine is unreachable. Aborting retries: {}".format(e)
            )
            raise e
        return response.to_dict()
