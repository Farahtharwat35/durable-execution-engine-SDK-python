from typing import List, Callable, Dict #module and allows specifying the types of the keys and values in the dictionary.
from datetime import datetime
import uuid
from typing import Optional, Tuple, Union #for the dependancy of the action on the work flow on the project
from enum import Enum

#*** will be removed only here temoprarely till there actual classes are created
class Project:
    def __init__(self, project_id: int, project_name: str):
        self.project_id = project_id
        self.project_name = project_name

class Workflow:
    def __init__(self, workflow_id: int, workflow_name: str, project: Project):
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.project = project

#*** end of what will be seprated ****rember to include the classes here to avoid errors***#

#retry package, spacify el type of the package
class ActionStatus(Enum):
    #i think it's good practice to use an enum for the status, *******anything more needed in the enum
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CREATED = "created"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"
    # nesenaha fel excution
class Action:
    def __init__(self, name: str, action: Callable, params: Dict = None, 
                 dependencies: List['Action'] = None, max_retries: int = 0, 
                 retry_behavior: str = "skip", on_retry_failure: Callable = None, 
                 timeout: int = 60, workflow: Workflow = None, project: Project = None):
        # by default max_reteries is 0 and the retry_behavior is to skip however user can and should change both, defaukt timeout is 60s can be reconfigures

        # Validate that the workflow belongs to the specified project
        if workflow and project and workflow.project != project:
            raise ValueError("The specified workflow does not belong to the specified project.")

        self.name = name #database will handle uniquness
        self.description = "" #at instentiation empty but set by the user later
        self.dependencies = dependencies if dependencies is not None else [] #if the action is a dependancy and something that depends on it is provoced then this action is triggred (using a dependant triggers the dependency)
        self.params = params if params is not None else {} #if one of the parmaters of the action are needed an instance of the action is created
        self.status = ActionStatus.NOT_STARTED #initial state not_started till the workflow itself is started
        self.retry_count = 0
        self.max_retries = max_retries 
        self.retry_behavior = retry_behavior
        self.on_retry_failure = on_retry_failure
        self.timeout = timeout #allows for changing the timeout
        self.action = action
        self.error_message = ""
        self.project = project    # Reference to the Project ###project ID only

    
    def execute(self): #***gets called inside the excute of the workflow***#
        """Execute the action with retry logic."""
        while self.retry_count <= self.max_retries:
            try:
                # Attempt to execute the action
                result = self.action(**self.params)
                self.status = "completed"
                return result
            except Exception as e:
                self.retry_count += 1
                self.error_message = str(e)
                self.status = "failed"
                
                if self.retry_count > self.max_retries:
                    # Call the on_retry_failure callback if provided
                    if self.on_retry_failure:
                        self.on_retry_failure(self)
                    if self.retry_behavior == "skip":
                        break
                else:
                    # Log the retry attempt (optional)
                    print(f"Retrying {self.name}, attempt {self.retry_count}...")
                    
        return "Action has falied"  # if the task ultimately fails


    def update_timeout(self, new_timeout: int):
        """Update the timeout value for the Action."""
        self.timeout = new_timeout

    def update_max_retries(self, new_max_retries: int):
        """Update the maximum number of retries for the Action."""
        self.max_retries = new_max_retries

    def update_retry_behavior(self, new_retry_behavior: str):
        """Update the retry behavior for the Action."""
        if new_retry_behavior in ["skip", "retry"]:
            self.retry_behavior = new_retry_behavior
        else:
            raise ValueError("Invalid retry behavior. Use 'skip' or 'retry'.")

    def set_retry_failure_action(self, new_on_retry_failure: Callable):
        """Set the action to take on retry failure."""
        self.on_retry_failure = new_on_retry_failure

    def get_workflow_info(self) -> Union[Tuple[str, str], str]:
        """Return the workflow name and ID."""
        if self.workflow:
            return self.workflow.workflow_name, self.workflow.workflow_id
        else:
            return "Error: The action cannot be created without belonging to a workflow that belongs to a project."


    def get_project_info(self) -> Union[Tuple[str, str], str]:
        """Return the project name and ID."""
        if self.project:
            return self.project.project_name, self.project.project_id
        else:
            return "Error: The project does not exist."


    def handle_creation_response(self, response_code: int): #create will return, create lama ta5od el response hat7ot l nafsaha el id
        """Handle the response code from the action creation."""
        if response_code == 201:
            #*****ha5od el id bat3 el action w a7oto fell self.id*****# 
            self.status = "created"
            return f"Successful operation. Workflow ID: {self.workflow.workflow_id}, Workflow Name: {self.workflow.workflow_name}"
        elif response_code == 400:
            self.status = "failed"
            return "400, Bad request"
            #****should we detect the reason for faliure and add it to the msg
            # msg sent you descide you want to show or not
        elif response_code == 500:
            self.status = "failed"
            return "500, Internal server error"

        else:
            self.status = "unknown"
            return "Unknown response code."

    def __repr__(self):
        return f"Action(id={self.id}, name={self.name}, status={self.status}, timeout={self.timeout})"


### add create function and will send the created object to the backend & SDK