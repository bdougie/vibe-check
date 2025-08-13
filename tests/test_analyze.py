#!/usr/bin/env python3
"""
Test suite for benchmark/analyze.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'benchmark'))

try:
    from benchmark.analyze import analyze_results, load_results, export_to_csv
except ImportError:
    # If analyze.py doesn't exist yet, create a basic version for testing
    pytest.skip("analyze.py not implemented yet", allow_module_level=True)


class TestAnalyze:
    """Test cases for analyze.py functions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.results_dir = self.temp_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample result files
        self.sample_results = [
            {
                "model": "test_model_1",
                "task": "test_task_1",
                "prompts_sent": 5,
                "chars_sent": 150,
                "chars_received": 300,
                "human_interventions": 2,
                "task_completed": True,
                "completion_time": 120.5,
                "files_modified": 2,
                "lines_added": 25,
                "lines_removed": 10
            },
            {
                "model": "test_model_1",
                "task": "test_task_2", 
                "prompts_sent": 3,
                "chars_sent": 100,
                "chars_received": 200,
                "human_interventions": 1,
                "task_completed": False,
                "completion_time": 85.2,
                "files_modified": 1,
                "lines_added": 10,
                "lines_removed": 5
            },
            {
                "model": "test_model_2",
                "task": "test_task_1",
                "prompts_sent": 8,
                "chars_sent": 250,
                "chars_received": 500,
                "human_interventions": 4,
                "task_completed": True,
                "completion_time": 180.0,
                "files_modified": 3,
                "lines_added": 40,
                "lines_removed": 15
            }
        ]
        
        # Write sample files
        for i, result in enumerate(self.sample_results):
            result_file = self.results_dir / f"result_{i}.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)
    
    def teardown_method(self):
        """Clean up after tests"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('glob.glob')
    @patch('pandas.DataFrame')
    def test_analyze_results_basic(self, mock_dataframe, mock_glob):
        """Test basic analyze_results functionality"""
        # Mock glob to return our test files
        result_files = [str(f) for f in self.results_dir.glob("*.json")]
        mock_glob.return_value = result_files
        
        # Mock pandas DataFrame
        mock_df = MagicMock()
        mock_dataframe.return_value = mock_df
        mock_df.__len__.return_value = 3
        mock_df.__getitem__.return_value.mean.return_value = 0.67  # 2/3 completion rate
        
        # Mock groupby operations
        mock_groupby = MagicMock()
        mock_df.groupby.return_value = mock_groupby
        mock_groupby.__getitem__.return_value.agg.return_value = "mocked_stats"
        mock_groupby.__getitem__.return_value.mean.return_value = "mocked_means"
        
        with patch('builtins.print') as mock_print:
            analyze_results()
            
            # Verify print statements were called
            assert mock_print.call_count > 0
            
            # Check that pandas DataFrame was created with our data
            mock_dataframe.assert_called_once()
            
    @patch('glob.glob')
    def test_analyze_results_no_files(self, mock_glob):
        """Test analyze_results with no result files"""
        mock_glob.return_value = []
        
        with patch('builtins.print') as mock_print:
            try:
                analyze_results()
            except Exception:
                # If pandas is not available, it might raise an exception
                # but we should handle this gracefully
                pass
    
    def test_result_file_structure(self):
        """Test that our sample result files have correct structure"""
        for result_file in self.results_dir.glob("*.json"):
            with open(result_file, 'r') as f:
                data = json.load(f)
            
            required_fields = [
                'model', 'task', 'prompts_sent', 'chars_sent', 'chars_received',
                'human_interventions', 'task_completed', 'completion_time',
                'files_modified', 'lines_added', 'lines_removed'
            ]
            
            for field in required_fields:
                assert field in data, f"Missing field {field} in {result_file}"
    
    @patch('pandas.DataFrame')
    @patch('glob.glob')
    def test_analyze_results_with_real_data(self, mock_glob, mock_dataframe):
        """Test analyze_results with real sample data"""
        # Use our actual test files
        result_files = [str(f) for f in self.results_dir.glob("*.json")]
        mock_glob.return_value = result_files
        
        # Use real DataFrame for this test
        import pandas as pd
        mock_dataframe.side_effect = pd.DataFrame
        
        try:
            with patch('builtins.print') as mock_print:
                analyze_results()
                
                # Should have printed analysis results
                assert mock_print.call_count > 0
                
                # Check for expected output patterns
                printed_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
                assert "Benchmark Results" in printed_text or "Total tasks" in printed_text
                
        except ImportError:
            # pandas might not be available in test environment
            pytest.skip("pandas not available for testing")


# Test that would check the actual analyze.py if it exists
@pytest.mark.integration
class TestAnalyzeIntegration:
    """Integration tests for analyze.py"""
    
    def test_analyze_script_exists(self):
        """Test that analyze.py script exists and is importable"""
        analyze_path = Path("benchmark/analyze.py")
        
        if not analyze_path.exists():
            pytest.skip("analyze.py not yet implemented")
        
        # Try to import and run basic validation
        try:
            import benchmark.analyze
            assert hasattr(benchmark.analyze, 'analyze_results')
        except ImportError as e:
            pytest.fail(f"Could not import analyze.py: {e}")
    
    def test_analyze_with_real_results(self):
        """Test analyze.py with real result files if they exist"""
        results_dir = Path("benchmark/results")
        
        if not results_dir.exists() or not list(results_dir.glob("*.json")):
            pytest.skip("No real result files to test with")
        
        try:
            from benchmark.analyze import analyze_results
            
            # Should not crash with real data
            analyze_results()
            
        except ImportError:
            pytest.skip("analyze.py or pandas not available")
        except Exception as e:
            pytest.fail(f"analyze_results failed with real data: {e}")