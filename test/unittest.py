# test_actionClass.py
import unittest
from src.classes.actionClass import Action, ActionStatus

class TestActionClass(unittest.TestCase):
    def test_action_creation(self):
        action = Action("Test Action")
        self.assertEqual(action.name, "Test Action")

    def test_action_status(self):
        action = Action("Test Action")
        action.set_status(ActionStatus.RUNNING)
        self.assertEqual(action.get_status(), ActionStatus.RUNNING)

if __name__ == '__main__':
    unittest.main()