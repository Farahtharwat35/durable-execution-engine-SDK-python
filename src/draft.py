# Assuming Project and Workflow classes are already defined and available

# Create instances of Project and Workflow outside of the SDK
project = Project(project_id=1, project_name="Project Alpha")
workflow = Workflow(workflow_id=1, workflow_name="Workflow 1", project=project)

# Create an SDK instance
sdk = SDK()

# Create an action with the action name, workflow, and project instances
action = sdk.create_action(action_name="Action 1", workflow=workflow, project=project)

# Now configure the action attributes as needed
action.action = lambda: print("Executing Action 1")  # Set the actual callable
action.params = {"param1": "value1", "param2": "value2"}  # Set parameters
action.max_retries = 3  # Set max retries
action.retry_behavior = "retry"  # Set retry behavior
action.timeout = 120  # Set timeout

# Optionally, you can also set dependencies, on_retry_failure, etc.
# action.dependencies = [other_action_instance]  # Example of setting dependencies

# Print the configured action
print(action)