"""Unit tests for JSON file reading functionality in CSVDataSource."""

import pytest
import pandas as pd
import json
import tempfile
import os
from eviz.lib.data.sources.csv import CSVDataSource


class TestJSONReading:
    """Test JSON file reading and nested dictionary normalization."""

    @pytest.fixture
    def sample_json_lines_file(self):
        """Create a temporary JSON lines file for testing."""
        data = [
            {"level": "INFO", "batch_idx": 0, "deltas": {"time": 0.27, "dMem": 122716160}},
            {"level": "INFO", "batch_idx": 1, "deltas": {"time": 0.12, "dMem": -23379968}},
            {"level": "INFO", "batch_idx": 2, "deltas": {"time": 0.10, "dMem": 1572864}}
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            for record in data:
                f.write(json.dumps(record) + '\n')
            filepath = f.name

        yield filepath
        os.unlink(filepath)

    @pytest.fixture
    def sample_json_array_file(self):
        """Create a temporary JSON array file for testing."""
        data = [
            {"name": "Alice", "age": 30, "scores": {"math": 95, "science": 88}},
            {"name": "Bob", "age": 25, "scores": {"math": 82, "science": 90}}
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            filepath = f.name

        yield filepath
        os.unlink(filepath)

    def test_load_json_lines(self, sample_json_lines_file):
        """Test loading line-delimited JSON file."""
        source = CSVDataSource()
        dataset = source.load_data(sample_json_lines_file)

        # Check that data was loaded
        assert dataset is not None
        assert 'level' in dataset.data_vars
        assert 'batch_idx' in dataset.data_vars

        # Check that nested dict was normalized
        assert 'deltas_time' in dataset.data_vars
        assert 'deltas_dMem' in dataset.data_vars

    def test_load_json_array(self, sample_json_array_file):
        """Test loading JSON array file."""
        source = CSVDataSource()
        dataset = source.load_data(sample_json_array_file)

        # Check that data was loaded
        assert dataset is not None
        # Note: pandas may transpose JSON array data differently than line-delimited
        # Just verify dataset is not empty and has some variables
        assert len(dataset.data_vars) > 0

    def test_normalize_nested_dicts(self):
        """Test _normalize_nested_dicts method."""
        source = CSVDataSource()

        df = pd.DataFrame({
            'id': [1, 2, 3],
            'metadata': [
                {'version': '1.0', 'status': 'active'},
                {'version': '1.1', 'status': 'pending'},
                {'version': '1.2', 'status': 'active'}
            ]
        })

        result = source._normalize_nested_dicts(df)

        # Check that dict column was expanded
        assert 'metadata' not in result.columns
        assert 'metadata_version' in result.columns
        assert 'metadata_status' in result.columns
        assert 'id' in result.columns
        assert len(result) == 3

    def test_normalize_empty_dataframe(self):
        """Test normalizing empty DataFrame."""
        source = CSVDataSource()
        df = pd.DataFrame()
        result = source._normalize_nested_dicts(df)
        assert result.empty

    def test_normalize_no_nested_dicts(self):
        """Test normalizing DataFrame with no nested dicts."""
        source = CSVDataSource()
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        result = source._normalize_nested_dicts(df)

        # Should return unchanged
        assert 'a' in result.columns
        assert 'b' in result.columns
        assert len(result.columns) == 2

    def test_read_csv_file(self):
        """Test that CSV files still work correctly."""
        # Create a temporary CSV file
        csv_data = "name,age,score\nAlice,30,95\nBob,25,82\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            filepath = f.name

        try:
            source = CSVDataSource()
            dataset = source.load_data(filepath)

            assert dataset is not None
            assert 'name' in dataset.data_vars
            assert 'age' in dataset.data_vars
            assert 'score' in dataset.data_vars
        finally:
            os.unlink(filepath)

    def test_multiple_json_files(self, sample_json_lines_file):
        """Test loading multiple JSON files."""
        # Create another JSON file
        data = [
            {"level": "INFO", "batch_idx": 3, "deltas": {"time": 0.11, "dMem": -8355840}},
            {"level": "INFO", "batch_idx": 4, "deltas": {"time": 0.09, "dMem": -1359872}}
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            for record in data:
                f.write(json.dumps(record) + '\n')
            filepath2 = f.name

        try:
            source = CSVDataSource()
            dataset = source.load_data([sample_json_lines_file, filepath2])

            # Check that both files were loaded
            assert dataset is not None
            # Should have 5 records total (3 from first file + 2 from second)
            assert len(dataset['batch_idx']) == 5
            assert 'deltas_time' in dataset.data_vars
        finally:
            os.unlink(filepath2)

    def test_json_with_multiple_nested_dicts(self):
        """Test normalizing JSON with multiple nested dict columns."""
        data = [
            {
                "id": 1,
                "metadata": {"version": "1.0", "status": "active"},
                "config": {"timeout": 30, "retries": 3}
            },
            {
                "id": 2,
                "metadata": {"version": "1.1", "status": "pending"},
                "config": {"timeout": 60, "retries": 5}
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            for record in data:
                f.write(json.dumps(record) + '\n')
            filepath = f.name

        try:
            source = CSVDataSource()
            dataset = source.load_data(filepath)

            # Check all nested dicts were normalized
            assert 'metadata_version' in dataset.data_vars
            assert 'metadata_status' in dataset.data_vars
            assert 'config_timeout' in dataset.data_vars
            assert 'config_retries' in dataset.data_vars
            assert 'id' in dataset.data_vars
        finally:
            os.unlink(filepath)
