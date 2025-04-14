import httpx
from typing import Dict
from pydantic import ValidationError
from src.models.execution_model import Execution

class WorkflowManager:

    def __init__(self, base_url: str):
        self.base_url = base_url

    def execute(self, workflow_name: str, service_name: str, input_data: Dict) -> str:
        url = f"{self.base_url}/services/{service_name}/workflows/{workflow_name}/executions"
        with httpx.Client() as client:
            response = client.post(url, json={"input": input_data})
            if response.status_code == 201 or response.status_code == 202:
                try:
                    data = response.json()
                    return Execution(**data)
                except ValidationError as e:
                    raise Exception(f"Validation error: {e}")
            else:
                raise Exception(f"Error: {response.status_code} - {response.json().get('message', '')}")

        
    def get(self, execution_id: str) -> Execution:
        url = f"{self.base_url}/executions/{execution_id}"
        with httpx.Client() as client:
            response = client.get(url)
            if response.status_code == 200:
                try:
                    data = response.json()
                    return Execution(**data)
                except ValidationError as e:
                    raise Exception(f"Validation error: {e}")
            else:
                raise Exception(f"Error: {response.status_code} - {response.json().get('message', '')}")

    def resume(self, execution_id: str, status:str) -> None:
        return self._update_status(execution_id, status)
    
    def pause(self, execution_id: str, status:str) -> None:
        return self._update_status(execution_id, status)

    def terminate(self, execution_id: str, status:str) -> None:
        return self._update_status(execution_id, status)
    
    def _update_status(self, execution_id: str, status: str) -> None:
        url = f"{self.base_url}/executions/{execution_id}"
        payload = {"status": status}
        with httpx.Client() as client:
            response = client.patch(url, json=payload)
            if response.status_code == 204:
                return
            else:
                raise Exception(f"Error: {response.status_code} - {response.json().get('message', '')}")