from typing import List, Dict
from datetime import datetime
import requests
from enum import Enum

## Do we want project status?
class ProjectStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"

class Project:
    def __init__(self, project_id: int, project_name: str):
        self.project_name = project_name
        self.description: str = "" # A string for project details, initialized as an empty string.
        self.status: ProjectStatus = ProjectStatus.ACTIVE
        self.workflows: List = []
        self.actions: List = []

    def add_workflow(self, workflow) -> None:
        """Add a workflow to the project"""
        self.workflows.append(workflow)

    def add_action(self, action) -> None:
        """Add an action to the project"""
        self.actions.append(action)

    def update_status(self, new_status: ProjectStatus) -> None:
        """Update the project status"""
        self.status = new_status

    def update_description(self, description: str) -> None:
        """Update the project description"""
        self.description = description


    def get_workflows(self) -> List:
        """Return all workflows in the project"""
        return self.workflows

    def get_actions(self) -> List:
        """Return all actions in the project"""
        return self.actions

    def create(self) -> Dict:
        """Send project creation request to backend"""
        project_data = {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "description": self.description,
            "status": self.status.value,
        }

        try:

            ####update el link DON'T FORGET
            response = requests.post('https://backend_url/api/projects', json=project_data)
            if response.status_code == 201:
                return {"status": "success", "message": "Project created successfully"}
            else:
                return {"status": "error", "message": f"Failed to create project: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to create project: {str(e)}"}

    def __repr__(self) -> str:
        return f"Project(id={self.project_id}, name={self.project_name}, status={self.status.value})"
