import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from eviz.lib.config.yaml_parser import YAMLParser


@pytest.fixture
def temp_yaml_files():
    """Create temporary YAML files for testing."""
    temp_dir = tempfile.mkdtemp()

    # Create a basic YAML config file
    basic_yaml = os.path.join(temp_dir, "test_config.yaml")
    with open(basic_yaml, 'w') as f:
        f.write("""
inputs:
- name: test_data.csv
  location: /data
  to_plot:
    metric_name: bar,pie,hist

outputs:
  output_dir: /output
  print_to_file: yes
""")

    # Create a YAML with dict-style plot options
    dict_yaml = os.path.join(temp_dir, "test_dict_config.yaml")
    with open(dict_yaml, 'w') as f:
        f.write("""
inputs:
- name: test_data.csv
  location: /data
  to_plot:
    metric_name:
      bar:
        color: blue
        width: 0.8
      pie:
        explode: [0.1, 0]
      hist:
        bins: 20

outputs:
  output_dir: /output
""")

    # Create a YAML with list-style plot types
    list_yaml = os.path.join(temp_dir, "test_list_config.yaml")
    with open(list_yaml, 'w') as f:
        f.write("""
inputs:
- name: test_data.csv
  location: /data
  to_plot:
    metric_name: ['bar', 'pie', 'hist']

outputs:
  output_dir: /output
""")

    yield {
        'basic': basic_yaml,
        'dict': dict_yaml,
        'list': list_yaml,
        'dir': temp_dir
    }

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


class TestYAMLParser:
    """Test suite for YAMLParser class."""

    def test_plot_type_constants(self):
        """Test that plot type constants are defined correctly."""
        assert 'bar' in YAMLParser.CSV_PLOT_TYPES
        assert 'pie' in YAMLParser.CSV_PLOT_TYPES
        assert 'hist' in YAMLParser.CSV_PLOT_TYPES
        assert 'scatter' in YAMLParser.CSV_PLOT_TYPES
        assert 'line' in YAMLParser.CSV_PLOT_TYPES

        assert 'xy' in YAMLParser.GRIDDED_PLOT_TYPES
        assert 'xt' in YAMLParser.GRIDDED_PLOT_TYPES
        assert 'yz' in YAMLParser.GRIDDED_PLOT_TYPES

        assert 'bar' in YAMLParser.ALL_PLOT_TYPES
        assert 'xy' in YAMLParser.ALL_PLOT_TYPES

    @patch('eviz.lib.utils.load_yaml_simple')
    @patch('eviz.lib.utils.read_meta_coords')
    @patch('eviz.lib.utils.read_meta_attrs')
    @patch('eviz.lib.utils.read_species_db')
    def test_parse_string_plot_types(self, mock_species, mock_attrs, mock_coords, mock_load):
        """Test parsing comma-separated string plot types."""
        mock_load.return_value = {
            'inputs': [{
                'name': 'test.csv',
                'location': '/data',
                'to_plot': {
                    'metric_name': 'bar,pie,hist'
                }
            }],
            'outputs': {'output_dir': '/output'}
        }
        mock_coords.return_value = {}
        mock_attrs.return_value = {}
        mock_species.return_value = {}

        parser = YAMLParser(
            config_files=['test.yaml'],
            source_names=['test']
        )
        parser.parse()

        # Check that plot types were parsed correctly
        assert len(parser.map_params) > 0
        map_entry = parser.map_params[0]
        assert map_entry['to_plot'] == ['bar', 'pie', 'hist']
        assert map_entry['field'] == 'metric_name'

    @patch('eviz.lib.utils.load_yaml_simple')
    @patch('eviz.lib.utils.read_meta_coords')
    @patch('eviz.lib.utils.read_meta_attrs')
    @patch('eviz.lib.utils.read_species_db')
    def test_parse_dict_plot_types_with_options(self, mock_species, mock_attrs, mock_coords, mock_load):
        """Test parsing dict-style plot types with options."""
        mock_load.return_value = {
            'inputs': [{
                'name': 'test.csv',
                'location': '/data',
                'to_plot': {
                    'metric_name': {
                        'bar': {'color': 'blue', 'width': 0.8},
                        'pie': {'explode': [0.1, 0]},
                        'hist': {'bins': 20}
                    }
                }
            }],
            'outputs': {'output_dir': '/output'}
        }
        mock_coords.return_value = {}
        mock_attrs.return_value = {}
        mock_species.return_value = {}

        parser = YAMLParser(
            config_files=['test.yaml'],
            source_names=['test']
        )
        parser.parse()

        # Check that plot types and options were parsed correctly
        map_entry = parser.map_params[0]
        assert set(map_entry['to_plot']) == {'bar', 'pie', 'hist'}
        assert 'plot_options' in map_entry
        assert map_entry['plot_options']['bar']['color'] == 'blue'
        assert map_entry['plot_options']['bar']['width'] == 0.8
        assert map_entry['plot_options']['pie']['explode'] == [0.1, 0]
        assert map_entry['plot_options']['hist']['bins'] == 20

    @patch('eviz.lib.utils.load_yaml_simple')
    @patch('eviz.lib.utils.read_meta_coords')
    @patch('eviz.lib.utils.read_meta_attrs')
    @patch('eviz.lib.utils.read_species_db')
    def test_parse_list_plot_types(self, mock_species, mock_attrs, mock_coords, mock_load):
        """Test parsing list-style plot types."""
        mock_load.return_value = {
            'inputs': [{
                'name': 'test.csv',
                'location': '/data',
                'to_plot': {
                    'metric_name': ['bar', 'pie', 'hist']
                }
            }],
            'outputs': {'output_dir': '/output'}
        }
        mock_coords.return_value = {}
        mock_attrs.return_value = {}
        mock_species.return_value = {}

        parser = YAMLParser(
            config_files=['test.yaml'],
            source_names=['test']
        )
        parser.parse()

        # Check that plot types were parsed correctly
        map_entry = parser.map_params[0]
        assert map_entry['to_plot'] == ['bar', 'pie', 'hist']

    @patch('eviz.lib.utils.load_yaml_simple')
    @patch('eviz.lib.utils.read_meta_coords')
    @patch('eviz.lib.utils.read_meta_attrs')
    @patch('eviz.lib.utils.read_species_db')
    def test_parse_ccm_format(self, mock_species, mock_attrs, mock_coords, mock_load):
        """Test parsing CCM format with plot_type key."""
        mock_load.return_value = {
            'inputs': [{
                'name': 'test.nc',
                'location': '/data',
                'to_plot': {
                    'field1': {'plot_type': 'xy'}
                }
            }],
            'outputs': {'output_dir': '/output'}
        }
        mock_coords.return_value = {}
        mock_attrs.return_value = {}
        mock_species.return_value = {}

        parser = YAMLParser(
            config_files=['test.yaml'],
            source_names=['test']
        )
        parser.parse()

        # Check that plot type was parsed correctly
        map_entry = parser.map_params[0]
        assert map_entry['to_plot'] == ['xy']

    @patch('eviz.lib.utils.load_yaml_simple')
    @patch('eviz.lib.utils.read_meta_coords')
    @patch('eviz.lib.utils.read_meta_attrs')
    @patch('eviz.lib.utils.read_species_db')
    def test_parse_multiple_fields(self, mock_species, mock_attrs, mock_coords, mock_load):
        """Test parsing multiple fields with different plot types."""
        mock_load.return_value = {
            'inputs': [{
                'name': 'test.csv',
                'location': '/data',
                'to_plot': {
                    'metric1': 'bar,pie',
                    'metric2': 'hist',
                    'metric3': ['scatter', 'line']
                }
            }],
            'outputs': {'output_dir': '/output'}
        }
        mock_coords.return_value = {}
        mock_attrs.return_value = {}
        mock_species.return_value = {}

        parser = YAMLParser(
            config_files=['test.yaml'],
            source_names=['test']
        )
        parser.parse()

        # Should create separate map entries for each field
        assert len(parser.map_params) == 3

        # Find entries by field name
        entries_by_field = {entry['field']: entry for entry in parser.map_params.values()}

        assert entries_by_field['metric1']['to_plot'] == ['bar', 'pie']
        assert entries_by_field['metric2']['to_plot'] == ['hist']
        assert entries_by_field['metric3']['to_plot'] == ['scatter', 'line']

    @patch('eviz.lib.utils.load_yaml_simple')
    @patch('eviz.lib.utils.read_meta_coords')
    @patch('eviz.lib.utils.read_meta_attrs')
    @patch('eviz.lib.utils.read_species_db')
    def test_parse_with_whitespace(self, mock_species, mock_attrs, mock_coords, mock_load):
        """Test that whitespace in plot type strings is handled correctly."""
        mock_load.return_value = {
            'inputs': [{
                'name': 'test.csv',
                'location': '/data',
                'to_plot': {
                    'metric_name': ' bar , pie , hist '
                }
            }],
            'outputs': {'output_dir': '/output'}
        }
        mock_coords.return_value = {}
        mock_attrs.return_value = {}
        mock_species.return_value = {}

        parser = YAMLParser(
            config_files=['test.yaml'],
            source_names=['test']
        )
        parser.parse()

        # Check that whitespace was stripped
        map_entry = parser.map_params[0]
        assert map_entry['to_plot'] == ['bar', 'pie', 'hist']

    @patch('eviz.lib.utils.load_yaml_simple')
    @patch('eviz.lib.utils.read_meta_coords')
    @patch('eviz.lib.utils.read_meta_attrs')
    @patch('eviz.lib.utils.read_species_db')
    def test_parse_default_plot_type(self, mock_species, mock_attrs, mock_coords, mock_load):
        """Test that unknown format defaults to 'xy'."""
        mock_load.return_value = {
            'inputs': [{
                'name': 'test.nc',
                'location': '/data',
                'to_plot': {
                    'field1': 12345  # Invalid format
                }
            }],
            'outputs': {'output_dir': '/output'}
        }
        mock_coords.return_value = {}
        mock_attrs.return_value = {}
        mock_species.return_value = {}

        parser = YAMLParser(
            config_files=['test.yaml'],
            source_names=['test']
        )
        parser.parse()

        # Should default to 'xy'
        map_entry = parser.map_params[0]
        assert map_entry['to_plot'] == ['xy']

    def test_to_dict(self):
        """Test to_dict method."""
        parser = YAMLParser(
            config_files=['test.yaml'],
            source_names=['test']
        )
        result = parser.to_dict()

        assert 'config_files' in result
        assert 'source_names' in result
        assert 'app_data' in result
        assert 'spec_data' in result
        assert 'map_params' in result
        assert result['config_files'] == ['test.yaml']
        assert result['source_names'] == ['test']
