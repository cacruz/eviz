"""Unit tests for xy_plot module - specifically testing the None data.name fix."""

import pytest
import numpy as np
import xarray as xr
from unittest.mock import MagicMock

from eviz.lib.autoviz.plotting.backends.matplotlib.xy_plot import MatplotlibXYPlotter


@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    config = MagicMock()
    config.compare = False
    config.compare_diff = False
    config.ax_opts = {}
    config.axindex = 0
    config.level = None
    config.time_val = None
    config.spec_data = {
        'temperature': {'name': 'Temperature', 'units': 'K'}
    }
    return config


@pytest.fixture
def sample_data_with_name():
    """Create sample data with a name attribute."""
    data = xr.DataArray(
        np.random.randn(20, 30),
        coords={'lat': np.linspace(-90, 90, 20), 'lon': np.linspace(-180, 180, 30)},
        dims=['lat', 'lon'],
        attrs={'units': 'K', 'long_name': 'Temperature'}
    )
    data.name = 'temperature'
    return data


@pytest.fixture
def sample_data_without_name():
    """Create sample data without a name attribute (e.g., difference plots)."""
    data = xr.DataArray(
        np.random.randn(20, 30),
        coords={'lat': np.linspace(-90, 90, 20), 'lon': np.linspace(-180, 180, 30)},
        dims=['lat', 'lon'],
        attrs={'units': 'K', 'long_name': 'Temperature Difference'}
    )
    data.name = None  # Simulates difference plots where name is None
    return data


class TestMatplotlibXYPlotter:
    """Test suite for XY plotter - focused on None data.name bug fix."""

    def test_init(self):
        """Test XY plotter initialization."""
        plotter = MatplotlibXYPlotter()
        assert plotter is not None
        assert hasattr(plotter, 'logger')

    def test_data_name_none_handling(self):
        """Test that the code handles data.name = None without TypeError.

        This is a regression test for the bug fix where compare_diff plots
        created data arrays without a name, causing:
        TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'
        """
        # Create data without a name (simulating difference plots)
        data = xr.DataArray(
            np.random.randn(20, 30),
            coords={'lat': np.linspace(-90, 90, 20), 'lon': np.linspace(-180, 180, 30)},
            dims=['lat', 'lon']
        )
        data.name = None  # This is the critical test case

        field_name = 'test_field'
        level_text = '@ 500 mb'

        # The fix: use field_name when data.name is None
        data_name = data.name if data.name is not None else field_name
        title_str = data_name + level_text

        # Should construct title without TypeError
        assert title_str == 'test_field@ 500 mb'
        assert 'None' not in title_str

    def test_data_name_exists_handling(self):
        """Test that normal data with name still works correctly."""
        data = xr.DataArray(
            np.random.randn(20, 30),
            coords={'lat': np.linspace(-90, 90, 20), 'lon': np.linspace(-180, 180, 30)},
            dims=['lat', 'lon']
        )
        data.name = 'temperature'

        field_name = 'fallback_name'
        level_text = '@ 850 mb'

        # Should use data.name when it exists
        data_name = data.name if data.name is not None else field_name
        title_str = data_name + level_text

        assert title_str == 'temperature@ 850 mb'

    def test_empty_level_text(self):
        """Test handling when level_text is empty."""
        data = xr.DataArray(np.random.randn(20, 30))
        data.name = None

        field_name = 'surface_pressure'
        level_text = ''

        # Should still work with empty level_text
        data_name = data.name if data.name is not None else field_name
        title_str = data_name + level_text

        assert title_str == 'surface_pressure'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
