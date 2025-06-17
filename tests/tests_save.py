import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import mock_open, patch
from typing import List
import tempfile


from src.save import _write_analysis_file

class TestWriteAnalysisFile(unittest.TestCase):
    """Tests for the _write_analysis_file function"""
    
    def setUp(self):
        """Initial configuration for tests"""
        # Basic test data
        self.basic_blueprint_ids = [1, 2, 3]
        self.basic_final_results = [10, 5, 8]
        
        # Complex test data
        self.complex_blueprint_ids = [1, 2, 3, 4, 5]
        self.complex_final_results = [12, 8, 15, 6, 20]
        
        # Test data with a single element
        self.single_blueprint_ids = [7]
        self.single_final_results = [3]
        
    def test_write_analysis_file_basic_case(self):
        """Test the basic case with multiple blueprints"""
        expected_output = (
            "Blueprint 1: 10\n"
            "Blueprint 2: 10\n"
            "Blueprint 3: 24\n"
            "\nBest blueprint is the blueprint 3.\n"
        )
        
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            _write_analysis_file("test_output.txt", self.basic_blueprint_ids, self.basic_final_results)
        
        # Verify that the file was opened correctly
        mock_file.assert_called_once_with("test_output.txt", 'w', encoding='utf-8')
        
        # Retrieve the written content
        handle = mock_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        
        self.assertEqual(written_content, expected_output)
        
    def test_write_analysis_file_empty_lists(self):
        """Test with empty lists"""
        blueprint_ids = []
        final_results = []
        expected_output = ""
        
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            _write_analysis_file("empty_test.txt", blueprint_ids, final_results)
        
        mock_file.assert_called_once_with("empty_test.txt", 'w', encoding='utf-8')
        
        handle = mock_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        
        self.assertEqual(written_content, expected_output)
        
    def test_write_analysis_file_single_blueprint(self):
        """Test with a single blueprint"""
        expected_output = (
            "Blueprint 7: 21\n"
            "\nBest blueprint is the blueprint 7.\n"
        )
        
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            _write_analysis_file("single_test.txt", self.single_blueprint_ids, self.single_final_results)
        
        mock_file.assert_called_once_with("single_test.txt", 'w', encoding='utf-8')
        
        handle = mock_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        
        self.assertEqual(written_content, expected_output)
        
    def test_write_analysis_file_complex_case(self):
        """Test with a more complex case (5 blueprints)"""
        expected_output = (
            "Blueprint 1: 12\n"
            "Blueprint 2: 16\n"
            "Blueprint 3: 45\n"
            "Blueprint 4: 24\n"
            "Blueprint 5: 100\n"
            "\nBest blueprint is the blueprint 5.\n"
        )
        
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            _write_analysis_file("complex_test.txt", self.complex_blueprint_ids, self.complex_final_results)
        
        mock_file.assert_called_once_with("complex_test.txt", 'w', encoding='utf-8')
        
        handle = mock_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        
        self.assertEqual(written_content, expected_output)
        
    def test_write_analysis_file_zero_values(self):
        """Test with zero values"""
        blueprint_ids = [1, 2, 3]
        final_results = [0, 5, 0]
        expected_output = (
            "Blueprint 1: 0\n"
            "Blueprint 2: 10\n"
            "Blueprint 3: 0\n"
            "\nBest blueprint is the blueprint 2.\n"
        )
        
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            _write_analysis_file("zero_test.txt", blueprint_ids, final_results)
        
        handle = mock_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        
        self.assertEqual(written_content, expected_output)
        
    def test_write_analysis_file_negative_values(self):
        """Test with negative values"""
        blueprint_ids = [1, 2, 3]
        final_results = [-2, 5, -1]
        expected_output = (
            "Blueprint 1: -2\n"
            "Blueprint 2: 10\n"
            "Blueprint 3: -3\n"
            "\nBest blueprint is the blueprint 2.\n"
        )
        
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            _write_analysis_file("negative_test.txt", blueprint_ids, final_results)
        
        handle = mock_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        
        self.assertEqual(written_content, expected_output)
        
    def test_write_analysis_file_identical_qualities(self):
        """Test with identical qualities (first found will be the best)"""
        blueprint_ids = [1, 2, 3]
        final_results = [5, 5, 5]
        expected_output = (
            "Blueprint 1: 5\n"
            "Blueprint 2: 10\n"
            "Blueprint 3: 15\n"
            "\nBest blueprint is the blueprint 3.\n"
        )
        
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            _write_analysis_file("identical_test.txt", blueprint_ids, final_results)
        
        handle = mock_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        
        self.assertEqual(written_content, expected_output)
        
    def test_write_analysis_file_large_numbers(self):
        """Test with large numbers"""
        blueprint_ids = [100, 200]
        final_results = [1000, 500]
        expected_output = (
            "Blueprint 100: 100000\n"
            "Blueprint 200: 100000\n"
            "\nBest blueprint is the blueprint 100.\n"
        )
        
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            _write_analysis_file("large_test.txt", blueprint_ids, final_results)
        
        handle = mock_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        
        self.assertEqual(written_content, expected_output)
        
    def test_file_encoding_parameter(self):
        """Test that the file is opened with the correct encoding"""
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            _write_analysis_file("encoding_test.txt", [1], [5])
        
        # Verify that UTF-8 encoding is used
        mock_file.assert_called_once_with("encoding_test.txt", 'w', encoding='utf-8')
        
    def test_file_path_parameter(self):
        """Test that the correct file path is used"""
        test_path = "/path/to/test/analysis.txt"
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            _write_analysis_file(test_path, [1], [5])
        
        mock_file.assert_called_once_with(test_path, 'w', encoding='utf-8')


class TestWriteAnalysisFileIntegration(unittest.TestCase):
    """Integration tests for _write_analysis_file with real files"""
    
    def setUp(self):
        """Configuration for integration tests"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Cleanup after tests"""
        import shutil
        shutil.rmtree(self.test_dir)
        
    def test_real_file_writing(self):
        """Integration test with a real file"""
        test_file = os.path.join(self.test_dir, "real_test.txt")
        blueprint_ids = [1, 2, 3]
        final_results = [10, 5, 8]
        
        _write_analysis_file(test_file, blueprint_ids, final_results)
        
        # Verify that the file exists
        self.assertTrue(os.path.exists(test_file))
        
        # Read and verify the content
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        expected_content = (
            "Blueprint 1: 10\n"
            "Blueprint 2: 10\n"
            "Blueprint 3: 24\n"
            "\nBest blueprint is the blueprint 3.\n"
        )
        
        self.assertEqual(content, expected_content)


if __name__ == '__main__':
    # Run tests with higher verbosity
    unittest.main(verbosity=2)
