from typing import List, Callable, Dict #module and allows specifying the types of the keys and values in the dictionary.
from datetime import datetime
import uuid

class Action:
    def __init__(self, name: str, action: Callable, params: Dict = None, 
                 dependencies: List['Action'] = None, max_retries: int = 0, 
                 retry_behavior: str = "skip", on_retry_failure: Callable = None, 
                 timeout: int = 60):
        # by default max_reteries is 0 and the retry_behavior is to skip however user can and should change both, defaukt timeout is 60s can be reconfigures
        self.id = str(uuid.uuid4())  # Generate a unique ID for each Action
        self.name = f"{name}_{self.id}" #****to insure  that the name is unique the id will bw appended to it, tmm wala eh security wise
        self.description = "" #at instentiation empty but set by the user later
        self.dependencies = dependencies if dependencies is not None else [] #if the action is a dependancy and something that depends on it is provoced then this action is triggred (using a dependant triggers the dependency)
        self.params = params if params is not None else {} #if one of the parmaters of the action are needed an instance of the action is created
        self.status = "not_started" #initial state not_started till the workflow itself is started
        self.retry_count = 0
        self.max_retries = max_retries 
        self.retry_behavior = retry_behavior
        self.on_retry_failure = on_retry_failure
        self.timeout = timeout #allows for changing the timeout
        self.action = action
        self.created_at = datetime.now()
        self.updated_at = self.created_at #****do we want this one? if i remember correctly when we were designing it was not taken intoo account
        self.error_message = ""

    def execute(self):
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

    
    def handle_creation_response(self, response_code: int):
        """Handle the response code from the action creation."""
        if response_code == 201:
            self.status = "created"
            return "Successful operation"
        elif response_code == 400:
            self.status = "failed"
            return "400, Bad request"
            #****should we detect the reason for faliure and add it to the msg
        elif response_code == 500:
            self.status = "failed"
            return "500, Internal server error"
        else:
            self.status = "unknown"
            return "Unknown response code."

    def __repr__(self):
        return f"Action(id={self.id}, name={self.name}, status={self.status}, timeout={self.timeout})"