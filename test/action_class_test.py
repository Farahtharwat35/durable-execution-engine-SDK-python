import unittest
from unittest.mock import patch, Mock
import requests

import sys
sys.path.append('C:/Users/noura/Documents/ASU/GraduationProject/Fall/durable-execution-engine-SDK-python/src/classes/actionClass.py')

# Assuming Action is defined in action_module.py
from src.classes.actionClass import Action, ActionStatus

class TestAction(unittest.TestCase):

    @patch('action_module.requests.post')
    def test_create_success(self, mock_post):
        # Arrange
        action = Action(name="Test Action", params={"key": "value"}, max_retries=3, retry_behavior="exponential", timeout=30, project="project_id")
        
        # Mock the response from the requests.post call
        mock_response = Mock()
        mock_response.status_code = 201  # HTTP status code for created
        mock_post.return_value = mock_response
        
        # Act
        result = action.create()
        
        # Assert
        self.assertEqual(action.status, ActionStatus.SUCCESS)
        self.assertIsNone(action.error_message)
        ##update URL with actual lama ne3raf el endpoint
        mock_post.assert_called_once_with('https://backend_url/api/actions', json={
            "name": "Test Action",
            "params": {"key": "value"},
            "max_retries": 3,
            "retry_behavior": "exponential",
            "timeout": 30,
            "project_id": "project_id",
        })
        self.assertEqual(result, None)

    @patch('action_module.requests.post')
    def test_create_failure(self, mock_post):
        # Arrange
        action = Action(name="Test Action", params={"key": "value"}, max_retries=3, retry_behavior="exponential", timeout=30, project="project_id")
        
        # Mock the response from the requests.post call
        mock_post.side_effect = Exception("Network error")
        
        # Act
        result = action.create()
        
        # Assert
        self.assertEqual(action.status, ActionStatus.FAILED)
        self.assertEqual(action.error_message, "Network error")
        self.assertIn("Failed to create action:", result)

    @patch('action_module.requests.post')
    def test_create_invalid_response(self, mock_post):
        # Arrange
        action = Action(name="Test Action", params={"key": "value"}, max_retries=3, retry_behavior="exponential", timeout=30, project="project_id")
        
        # Mock the response from the requests.post call
        mock_response = Mock()
        mock_response.status_code = 400  # Bad Request
        mock_post.return_value = mock_response
        
        # Act
        result = action.create()
        
        # Assert
        self.assertEqual(action.status, ActionStatus.FAILED)
        self.assertIsNotNone(action.error_message)
        self.assertIn("Failed to create action:", result)

if __name__ == '__main__':
    unittest.main()