import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import json

# Imports nécessaires ajoutés
from src.solver import ProductCalculator
from src.blueprint import DefaultBlueprintParser

# Import your FastAPI app
from api.api import app


class TestBlueprintAnalyzerAPI(unittest.TestCase):
    """Tests for the FastAPI blueprint analyzer endpoint"""
    
    def setUp(self):
        """Initial configuration for API tests"""
        self.client = TestClient(app)
        self.endpoint = "/blueprints/analyze"
        
        # Mock data for successful responses
        self.mock_blueprints = [Mock(), Mock(), Mock()]
        self.mock_final_resources = [10, 15, 8]
        self.mock_blueprint_ids = [1, 2, 3]
        
    @patch('api.api.solve_blueprints')
    @patch('api.api.BlueprintLoader')
    def test_analyze_blueprints_success(self, mock_loader_class, mock_solve):
        """Test successful blueprint analysis"""
        # Setup mocks
        mock_loader = Mock()
        mock_loader.load.return_value = self.mock_blueprints
        mock_loader_class.return_value = mock_loader
        
        mock_solve.return_value = (self.mock_final_resources, self.mock_blueprint_ids)
        
        # Execute request
        response = self.client.get(self.endpoint)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertIn("bestBlueprint", response_data)
        self.assertIn("blueprints", response_data)
        
        # Verify best blueprint (15 * 2 = 30 is highest quality)
        self.assertEqual(response_data["bestBlueprint"], "2")
        
        # Verify blueprint results
        expected_blueprints = [
            {"id": "1", "quality": 10},  # 10 * 1
            {"id": "2", "quality": 30},  # 15 * 2
            {"id": "3", "quality": 24}   # 8 * 3
        ]
        self.assertEqual(response_data["blueprints"], expected_blueprints)
        
    @patch('api.api.solve_blueprints')
    @patch('api.api.BlueprintLoader')
    def test_analyze_blueprints_single_blueprint(self, mock_loader_class, mock_solve):
        """Test analysis with single blueprint"""
        # Setup mocks
        mock_loader = Mock()
        mock_loader.load.return_value = [Mock()]
        mock_loader_class.return_value = mock_loader
        
        mock_solve.return_value = ([12], [1])
        
        # Execute request
        response = self.client.get(self.endpoint)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertEqual(response_data["bestBlueprint"], "1")
        self.assertEqual(response_data["blueprints"], [{"id": "1", "quality": 12}])
        
    @patch('api.api.solve_blueprints')
    @patch('api.api.BlueprintLoader')
    def test_analyze_blueprints_zero_quality(self, mock_loader_class, mock_solve):
        """Test analysis with zero quality blueprints"""
        # Setup mocks
        mock_loader = Mock()
        mock_loader.load.return_value = [Mock(), Mock()]
        mock_loader_class.return_value = mock_loader
        
        mock_solve.return_value = ([0, 5], [1, 2])
        
        # Execute request
        response = self.client.get(self.endpoint)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertEqual(response_data["bestBlueprint"], "2")  # 5 * 2 = 10 > 0 * 1 = 0
        
        expected_blueprints = [
            {"id": "1", "quality": 0},
            {"id": "2", "quality": 10}
        ]
        self.assertEqual(response_data["blueprints"], expected_blueprints)
        
    @patch('api.api.BlueprintLoader')
    def test_analyze_blueprints_file_not_found(self, mock_loader_class):
        """Test handling of file not found error"""
        # Setup mock to raise FileNotFoundError
        mock_loader = Mock()
        mock_loader.load.side_effect = FileNotFoundError("File not found")
        mock_loader_class.return_value = mock_loader
        
        # Execute request
        response = self.client.get(self.endpoint)
        
        # Verify error response
        self.assertEqual(response.status_code, 500)
        
        response_data = response.json()
        self.assertIn("detail", response_data)
        self.assertIn("Erreur lors du chargement des blueprints", response_data["detail"])
        self.assertIn("File not found", response_data["detail"])
        
    @patch('api.api.BlueprintLoader')
    def test_analyze_blueprints_parsing_error(self, mock_loader_class):
        """Test handling of blueprint parsing error"""
        # Setup mock to raise parsing error
        mock_loader = Mock()
        mock_loader.load.side_effect = ValueError("Invalid blueprint format")
        mock_loader_class.return_value = mock_loader
        
        # Execute request
        response = self.client.get(self.endpoint)
        
        # Verify error response
        self.assertEqual(response.status_code, 500)
        
        response_data = response.json()
        self.assertIn("detail", response_data)
        self.assertIn("Erreur lors du chargement des blueprints", response_data["detail"])
        self.assertIn("Invalid blueprint format", response_data["detail"])
        
    @patch('api.api.BlueprintLoader')
    def test_analyze_blueprints_empty_file(self, mock_loader_class):
        """Test handling of empty blueprint file"""
        # Setup mock to return empty list
        mock_loader = Mock()
        mock_loader.load.return_value = []
        mock_loader_class.return_value = mock_loader
        
        # Execute request
        response = self.client.get(self.endpoint)
        
        # Verify error response
        self.assertEqual(response.status_code, 404)
        
        response_data = response.json()
        self.assertIn("detail", response_data)
        self.assertEqual(response_data["detail"], "Aucun blueprint trouvé dans le fichier.")
        
        
    @patch('api.api.solve_blueprints')
    @patch('api.api.BlueprintLoader')
    def test_analyze_blueprints_config_verification(self, mock_loader_class, mock_solve):
        """Test that SolverConfig is created with correct parameters"""
        # Setup mocks
        mock_loader = Mock()
        mock_loader.load.return_value = self.mock_blueprints
        mock_loader_class.return_value = mock_loader
        
        mock_solve.return_value = ([5], [1])
        
        # Execute request
        response = self.client.get(self.endpoint)
        
        # Verify solve_blueprints was called with correct config
        self.assertEqual(response.status_code, 200)
        mock_solve.assert_called_once()
        
        # Get the config argument passed to solve_blueprints
        config_arg = mock_solve.call_args[0][0]
        self.assertEqual(config_arg.filename, "diamond.txt")
        self.assertEqual(config_arg.time_limit, 24)
        self.assertEqual(config_arg.final_resource, "diamond")
        self.assertIsInstance(config_arg.calculator, ProductCalculator)
        
    @patch('api.api.solve_blueprints')
    @patch('api.api.BlueprintLoader')
    def test_analyze_blueprints_identical_qualities(self, mock_loader_class, mock_solve):
        """Test handling of identical qualities (first one should be best)"""
        # Setup mocks
        mock_loader = Mock()
        mock_loader.load.return_value = [Mock(), Mock(), Mock()]
        mock_loader_class.return_value = mock_loader
        
        # All blueprints have same quality: 10*1=10, 5*2=10, 10*1=10
        mock_solve.return_value = ([10, 5, 10], [1, 2, 1])
        
        # Execute request
        response = self.client.get(self.endpoint)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        # First occurrence should be the best (quality 10 appears first)
        self.assertEqual(response_data["bestBlueprint"], "1")
        
    @patch('api.api.solve_blueprints')
    @patch('api.api.BlueprintLoader')
    def test_analyze_blueprints_large_numbers(self, mock_loader_class, mock_solve):
        """Test handling of large numbers"""
        # Setup mocks
        mock_loader = Mock()
        mock_loader.load.return_value = [Mock(), Mock()]
        mock_loader_class.return_value = mock_loader
        
        mock_solve.return_value = ([1000, 2000], [100, 200])
        
        # Execute request
        response = self.client.get(self.endpoint)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertEqual(response_data["bestBlueprint"], "200")  # 2000 * 200 = 400000
        
        expected_blueprints = [
            {"id": "100", "quality": 100000},  # 1000 * 100
            {"id": "200", "quality": 400000}   # 2000 * 200
        ]
        self.assertEqual(response_data["blueprints"], expected_blueprints)


class TestAPIResponseFormat(unittest.TestCase):
    """Tests for API response format validation"""
    
    def setUp(self):
        """Setup for response format tests"""
        self.client = TestClient(app)
        self.endpoint = "/blueprints/analyze"
        
    @patch('api.api.solve_blueprints')
    @patch('api.api.BlueprintLoader')
    def test_response_json_structure(self, mock_loader_class, mock_solve):
        """Test that response has correct JSON structure"""
        # Setup mocks
        mock_loader = Mock()
        mock_loader.load.return_value = [Mock()]
        mock_loader_class.return_value = mock_loader
        
        mock_solve.return_value = ([5], [1])
        
        # Execute request
        response = self.client.get(self.endpoint)
        
        # Verify response structure
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
        
        response_data = response.json()
        
        # Verify required fields exist
        self.assertIn("bestBlueprint", response_data)
        self.assertIn("blueprints", response_data)
        
        # Verify data types
        self.assertIsInstance(response_data["bestBlueprint"], str)
        self.assertIsInstance(response_data["blueprints"], list)
        
        # Verify blueprint structure
        for blueprint in response_data["blueprints"]:
            self.assertIn("id", blueprint)
            self.assertIn("quality", blueprint)
            self.assertIsInstance(blueprint["id"], str)
            self.assertIsInstance(blueprint["quality"], int)
            
    @patch('api.api.solve_blueprints')
    @patch('api.api.BlueprintLoader')
    def test_response_content_type(self, mock_loader_class, mock_solve):
        """Test that response has correct content type"""
        # Setup mocks
        mock_loader = Mock()
        mock_loader.load.return_value = [Mock()]
        mock_loader_class.return_value = mock_loader
        
        mock_solve.return_value = ([5], [1])
        
        # Execute request
        response = self.client.get(self.endpoint)
        
        # Verify content type
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response.headers["content-type"])


class TestAPIErrorHandling(unittest.TestCase):
    """Tests for API error handling"""
    
    def setUp(self):
        """Setup for error handling tests"""
        self.client = TestClient(app)
        self.endpoint = "/blueprints/analyze"
        
    @patch('api.api.BlueprintLoader')
    def test_http_exception_format(self, mock_loader_class):
        """Test that HTTPExceptions are properly formatted"""
        # Setup mock to raise exception
        mock_loader = Mock()
        mock_loader.load.side_effect = Exception("Test error")
        mock_loader_class.return_value = mock_loader
        
        # Execute request
        response = self.client.get(self.endpoint)
        
        # Verify error response format
        self.assertEqual(response.status_code, 500)
        
        response_data = response.json()
        self.assertIn("detail", response_data)
        self.assertIsInstance(response_data["detail"], str)
        self.assertIn("Erreur lors du chargement des blueprints", response_data["detail"])
        
    def test_endpoint_exists(self):
        """Test that the endpoint exists and is accessible"""
        # This will fail with our mocks, but verifies the endpoint is defined
        response = self.client.get(self.endpoint)
        
        # Should not be 404 (endpoint exists)
        self.assertNotEqual(response.status_code, 404)
        
    def test_method_not_allowed(self):
        """Test that only GET method is allowed"""
        # Test POST method
        response = self.client.post(self.endpoint)
        self.assertEqual(response.status_code, 405)
        
        # Test PUT method
        response = self.client.put(self.endpoint)
        self.assertEqual(response.status_code, 405)
        
        # Test DELETE method
        response = self.client.delete(self.endpoint)
        self.assertEqual(response.status_code, 405)


class TestAPIIntegration(unittest.TestCase):
    """Integration tests for the API"""
    
    def setUp(self):
        """Setup for integration tests"""
        self.client = TestClient(app)
        self.endpoint = "/blueprints/analyze"
        
    @patch('api.api.solve_blueprints')
    @patch('api.api.BlueprintLoader')
    def test_full_workflow_integration(self, mock_loader_class, mock_solve):
        """Test the complete workflow from request to response"""
        # Setup realistic mock data
        mock_blueprints = [Mock() for _ in range(3)]
        mock_loader = Mock()
        mock_loader.load.return_value = mock_blueprints
        mock_loader_class.return_value = mock_loader
        
        # Simulate realistic solver results
        mock_solve.return_value = ([12, 8, 15], [1, 2, 3])
        
        # Execute request
        response = self.client.get(self.endpoint)
        
        # Comprehensive verification
        self.assertEqual(response.status_code, 200)
        
        # Verify loader was called correctly
        mock_loader_class.assert_called_once()
        mock_loader.load.assert_called_once_with("diamond.txt")
        
        # Verify solver was called correctly
        mock_solve.assert_called_once()
        config = mock_solve.call_args[0][0]
        self.assertEqual(config.filename, "diamond.txt")
        self.assertEqual(config.time_limit, 24)
        self.assertEqual(config.final_resource, "diamond")
        
        # Verify response data
        response_data = response.json()
        self.assertEqual(response_data["bestBlueprint"], "3")  # 15 * 3 = 45 is highest
        
        expected_blueprints = [
            {"id": "1", "quality": 12},   # 12 * 1
            {"id": "2", "quality": 16},   # 8 * 2
            {"id": "3", "quality": 45}    # 15 * 3
        ]
        self.assertEqual(response_data["blueprints"], expected_blueprints)


if __name__ == '__main__':
    # Run tests with higher verbosity
    unittest.main(verbosity=2)
