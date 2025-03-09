import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from client.workflow_manager import WorkflowManager

class TestWorkflowManager(unittest.TestCase):
  