import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
from dataclasses import dataclass
from typing import List
import tempfile

from src.solver import (
    ResultCalculator, 
    QualityCalculator, 
    ProductCalculator, 
    SolverConfig, 
    solve_blueprints, 
    calculate_and_write_analysis
)


class TestResultCalculators(unittest.TestCase):
    """Tests for the ResultCalculator implementations"""
    
    def setUp(self):
        """Initial configuration for calculator tests"""
        self.quality_calculator = QualityCalculator()
        self.product_calculator = ProductCalculator()
        
        # Test data
        self.final_resources = [10, 5, 8]
        self.blueprint_ids = [1, 2, 3]
        
    def test_quality_calculator_basic_case(self):
        """Test QualityCalculator with basic data"""
        expected_result = 44
        result = self.quality_calculator.calculate(self.final_resources, self.blueprint_ids)
        self.assertEqual(result, expected_result)
        
    def test_quality_calculator_empty_lists(self):
        """Test QualityCalculator with empty lists"""
        result = self.quality_calculator.calculate([], [])
        self.assertEqual(result, 0)
        
    def test_product_calculator_basic_case(self):
        """Test ProductCalculator with basic data"""
        expected_result = 400
        result = self.product_calculator.calculate(self.final_resources, self.blueprint_ids)
        self.assertEqual(result, expected_result)
        
    def test_product_calculator_empty_list(self):
        """Test ProductCalculator with empty list"""
        result = self.product_calculator.calculate([], [1, 2, 3])
        self.assertEqual(result, 0)


class TestSolveBlueprints(unittest.TestCase):
    """Tests for the solve_blueprints function"""
    
    def setUp(self):
        """Setup for solve_blueprints tests"""
        self.mock_blueprint1 = Mock()
        self.mock_blueprint2 = Mock()
        self.mock_blueprint3 = Mock()
        self.mock_blueprints = [self.mock_blueprint1, self.mock_blueprint2, self.mock_blueprint3]
        
    @patch('src.solver.BlueprintLoader')
    @patch('src.solver.OptimizedRobotFactory')
    def test_solve_blueprints_with_custom_final_resource(self, mock_factory_class, mock_loader_class):
        """Test solve_blueprints with custom final resource"""
        # Setup mocks
        mock_loader = Mock()
        mock_loader.load.return_value = [self.mock_blueprint1]
        mock_loader_class.return_value = mock_loader
        
        mock_factory = Mock()
        mock_factory.max_final_resource.return_value = 15
        mock_factory_class.return_value = mock_factory
        
        config = SolverConfig(filename="test.txt", final_resource="obsidian")
        
        # Execute
        solve_blueprints(config)
        
        # Verify factory was created with correct final_resource
        mock_factory_class.assert_called_once_with(self.mock_blueprint1, final_resource="obsidian")


class TestCalculateAndWriteAnalysis(unittest.TestCase):
    """Tests for the calculate_and_write_analysis function"""
    
    @patch('src.solver.solve_blueprints')
    @patch('src.solver._write_analysis_file')
    def test_calculate_and_write_analysis_basic(self, mock_write_file, mock_solve):
        """Test calculate_and_write_analysis basic functionality"""
        # Setup mocks
        mock_solve.return_value = ([10, 5, 8], [1, 2, 3])
        
        calculator = QualityCalculator()
        config = SolverConfig(
            filename="test.txt",
            calculator=calculator,
            output_file="analysis.txt"
        )
        
        # Execute
        result = calculate_and_write_analysis(config)
        
        # Verify
        mock_solve.assert_called_once_with(config)
        mock_write_file.assert_called_once_with("analysis.txt", [1, 2, 3], [10, 5, 8])
        
        # Verify calculation
        expected_result = 44
        self.assertEqual(result, expected_result)


class TestIntegration(unittest.TestCase):
    """Integration tests for the solver module"""
    
    def setUp(self):
        """Setup for integration tests"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Cleanup after integration tests"""
        import shutil
        shutil.rmtree(self.test_dir)
        
    @patch('src.solver.BlueprintLoader')
    @patch('src.solver.OptimizedRobotFactory')
    def test_full_integration_with_file_output(self, mock_factory_class, mock_loader_class):
        """Integration test with real file output"""
        # Setup mocks
        mock_blueprint = Mock()
        mock_loader = Mock()
        mock_loader.load.return_value = [mock_blueprint]
        mock_loader_class.return_value = mock_loader
        
        mock_factory = Mock()
        mock_factory.max_final_resource.return_value = 12
        mock_factory_class.return_value = mock_factory
        
        # Setup config with real file path
        output_file = os.path.join(self.test_dir, "integration_test.txt")
        config = SolverConfig(
            filename="test_blueprints.txt",
            calculator=QualityCalculator(),
            output_file=output_file
        )
        
        # Execute
        result = calculate_and_write_analysis(config)
        
        # Verify result calculation 
        self.assertEqual(result, 12)
        
        # Verify file was created and contains expected content
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        expected_content = (
            "Blueprint 1: 12\n"
            "\nBest blueprint is the blueprint 1.\n"
        )
        self.assertEqual(content, expected_content)


class TestCustomResultCalculator(unittest.TestCase):
    """Tests for custom ResultCalculator implementations"""
    
    def test_custom_calculator_implementation(self):
        """Test that custom calculators can be implemented"""
        
        class MaxCalculator(ResultCalculator):
            """Custom calculator that returns the maximum final resource"""
            def calculate(self, final_resource: List[int], blueprint_ids: List[int]) -> int:
                return max(final_resource) if final_resource else 0
        
        calculator = MaxCalculator()
        result = calculator.calculate([10, 5, 8], [1, 2, 3])
        self.assertEqual(result, 10)
        
    def test_custom_calculator_with_blueprint_ids(self):
        """Test custom calculator that uses blueprint IDs"""
        
        class WeightedCalculator(ResultCalculator):
            """Custom calculator with weighted blueprint IDs"""
            def calculate(self, final_resource: List[int], blueprint_ids: List[int]) -> int:
                return sum(resource * (blueprint_id ** 2) 
                          for resource, blueprint_id in zip(final_resource, blueprint_ids))
        
        calculator = WeightedCalculator()
        result = calculator.calculate([10, 5, 8], [1, 2, 3])
        self.assertEqual(result, 102)


if __name__ == '__main__':
    # Run tests with higher verbosity
    unittest.main(verbosity=2)
