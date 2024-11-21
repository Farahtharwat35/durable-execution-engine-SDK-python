#dummy imports till merge
#******will be changed please don't forget
from project import Project
from workflow import Workflow
from action import Action

#this is passing the whole instance
class actionSDK:
    def __init__(self):
        self.actions = []  # List to store created actions

    def create_action(self, action_name: str, workflow: Workflow, project: Project) -> Action:
        # Validate that the workflow belongs to the specified project
        if workflow.project != project:
            raise ValueError("The specified workflow does not belong to the specified project.")

        # Create the action instance with a placeholder callable
        action_instance = Action(
            name=action_name,
            action=lambda: None,  # Placeholder action; replace with actual callable logic
            workflow=workflow,
            project=project
        )

        # Add the action to the workflow
        workflow.add_action(action_instance)  # Assuming Workflow has an add_action method

        # Store the action in the SDK for later reference if needed
        self.actions.append(action_instance)

        # Return the action instance for further configuration,  if needed furthur confugrations will happen through the class

        return action_instance
    


##this is passing only the name
class SDK:
    def __init__(self):
        self.workflows = []  # List to store created workflows
        self.projects = []   # List to store created projects
        self.actions = []    # List to store created actions

    def add_workflow(self, workflow: Workflow):
        self.workflows.append(workflow)

    def add_project(self, project: Project):
        self.projects.append(project)

    def create_action(self, action_name: str, workflow_name: str, project_name: str) -> Action:
        # Find the workflow by name
        workflow = next((w for w in self.workflows if w.workflow_name == workflow_name), None)
        if not workflow:
            raise ValueError(f"Workflow with name '{workflow_name}' not found.")

        # Find the project by name
        project = next((p for p in self.projects if p.project_name == project_name), None)
        if not project:
            raise ValueError(f"Project with name '{project_name}' not found.")

        # Validate that the workflow belongs to the specified project
        if workflow.project != project:
            raise ValueError("The specified workflow does not belong to the specified project.")

        # Create the action instance with a placeholder callable
        action_instance = Action(
            name=action_name,
            action=lambda: None,  # Placeholder action; replace with actual callable logic
            workflow=workflow,
            project=project
        )

        # Add the action to the workflow
        workflow.add_action(action_instance)  # Assuming Workflow has an add_action method

        # Store the action in the SDK for later reference if needed
        self.actions.append(action_instance)

        # Return the action instance for further configuration
        return action_instance