#@TODO: add the max retry and the retry mechanism in the execute_action method

class WorkflowContext:
    def __init__(self, execution_id: str):
        self.execution_id = execution_id