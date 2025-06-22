import logging
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
        try:
            logging.info(
                f"Attempting to send log to engine - Execution ID: {execution_id}, Action: {action_name}"
            )
            logging.info(f"Base URL: {self._base_url}")

            if not self._base_url:
                logging.error(
                    "DURABLE_ENGINE_BASE_URL is not set in environment variables."
                )
                raise ValueError(
                    "DURABLE_ENGINE_BASE_URL is not set in environment variables."
                )

            if not log or not action_name:
                logging.error("log and action_name must be provided.")
                raise ValueError("log and action_name must be provided.")

            url = (
                f"{self._base_url}/executions/{execution_id}/log/{action_name}"
            )
            headers = {"Content-Type": "application/json"}
            payload = log.to_dict()

            logging.info(f"Making request to: {url}")
            logging.info(f"Request headers: {headers}")
            logging.info(f"Request payload: {payload}")

            response = requests.patch(url, headers=headers, json=payload)
            logging.info(
                "Log sent to the Durable Execution Engine: {}".format(log)
            )
            logging.info(f"Response status code: {response.status_code}")
            # Safety check for headers attribute (for MockResponse in tests)
            if hasattr(response, 'headers'):
                logging.info(f"Response headers: {dict(response.headers)}")
            else:
                logging.info("Response headers: Not available (MockResponse)")
            logging.info("Response after sending log: {}".format(response))

            response.raise_for_status()
            try:
                response_payload = response.json()
                logging.info("Response payload: {}".format(response_payload))
            except ValueError as e:
                logging.error("Error parsing response payload: {}".format(e))
                if hasattr(response, 'text'):
                    logging.error(f"Raw response text: {response.text}")
                else:
                    logging.error("Raw response text: Not available (MockResponse)")
                response_payload = {}
            response = Response(
                status_code=response.status_code,
                payload=response_payload,
            )
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP ERROR: Status {e.response.status_code}")
            logging.error(f"HTTP ERROR: URL {e.response.url}")
            # Safety check for headers attribute (for MockResponse in tests)
            if hasattr(e.response, 'headers'):
                logging.error(f"HTTP ERROR: Headers {dict(e.response.headers)}")
            else:
                logging.error("HTTP ERROR: Headers Not available (MockResponse)")
            # Safety check for text attribute (for MockResponse in tests)
            if hasattr(e.response, 'text'):
                logging.error(f"HTTP ERROR: Text {e.response.text}")
            else:
                logging.error("HTTP ERROR: Text Not available (MockResponse)")
            try:
                error_payload = e.response.json()
                logging.info(
                    "Error payload: {}".format(error_payload)
                )
            except Exception as parse_error:
                error_payload = {}
                # Safety check for text attribute (for MockResponse in tests)
                if hasattr(e.response, 'text'):
                    logging.error(
                        f"Error parsing error payload: {parse_error}. Raw text: {e.response.text}"
                    )
                else:
                    logging.error(
                        f"Error parsing error payload: {parse_error}. Raw text: Not available (MockResponse)"
                    )
            response = Response(
                status_code=e.response.status_code,
                payload=error_payload,
            )
        except requests.exceptions.RequestException as e:
            logging.error(
                f"NETWORK ERROR: Engine is unreachable. Error type: {type(e).__name__}"
            )
            logging.error(f"NETWORK ERROR: Error details: {e}")
            raise e
        except Exception as e:
            logging.error(
                f"UNEXPECTED ERROR in send_log: {type(e).__name__}: {e}"
            )
            raise e

        logging.info(f"Returning response: {response.to_dict()}")
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
            logging.info(
                f"Attempting to mark execution as running - Execution ID: {execution_id}"
            )
            logging.info(f"Base URL: {self._base_url}")

            if not self._base_url:
                logging.error(
                    "DURABLE_ENGINE_BASE_URL is not set in environment variables."
                )
                raise ValueError(
                    "DURABLE_ENGINE_BASE_URL is not set in environment variables."
                )
            url = f"{self._base_url}/executions/{execution_id}/started"
            headers = {"Content-Type": "application/json"}

            logging.info(f"Making request to: {url}")
            logging.info(f"Request headers: {headers}")

            response = requests.patch(url, headers=headers)
            logging.info(
                "Execution marked as running: {}".format(response)
            )
            logging.info(f"Response status code: {response.status_code}")
            if hasattr(response, 'headers'):
                logging.info(f"Response headers: {dict(response.headers)}")
            else:
                logging.info("Response headers: Not available (MockResponse)")
            logging.info(
                "Response after marking execution as running: {}".format(response)
            )
            response.raise_for_status()
            response = Response(
                status_code=response.status_code,
            )
        except requests.exceptions.HTTPError as e:
            logging.error(
                f"HTTP ERROR marking execution as running: Status {e.response.status_code}"
            )
            logging.error(f"HTTP ERROR: URL {e.response.url}")
            logging.error(f"HTTP ERROR: Text {e.response.text}")
            response = Response(
                status_code=e.response.status_code,
            )
        except requests.exceptions.RequestException as e:
            logging.error(
                f"NETWORK ERROR: Engine is unreachable. Error type: {type(e).__name__}"
            )
            logging.error(f"NETWORK ERROR: Error details: {e}")
            raise e
        except Exception as e:
            logging.error(
                f"UNEXPECTED ERROR in mark_execution_as_running: {type(e).__name__}: {e}"
            )
            raise e

        logging.info(f"Returning response: {response.to_dict()}")
        return response.to_dict()
