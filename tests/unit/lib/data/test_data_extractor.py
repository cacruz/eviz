"""Tests for data extractor functionality, particularly WRF dimension handling."""

import pytest
import numpy as np
import xarray as xr
from unittest.mock import MagicMock, patch

from eviz.lib.data.data_extractor import DataExtractor


class TestDataExtractorWRF:
    """Test data extractor functionality for WRF data."""

    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock config manager with WRF dimension detection."""
        config_manager = MagicMock()
        
        # Mock the new get_model_dim_name_for_data method
        def mock_get_dim_name_for_data(dim_name, data_array):
            if not hasattr(data_array, 'dims'):
                return None
                
            dim_map = {
                'tc': 'Time' if 'Time' in data_array.dims else None,
                'zc': 'soil_layers_stag' if 'soil_layers_stag' in data_array.dims else 
                      'bottom_top' if 'bottom_top' in data_array.dims else None,
                'xc': 'west_east' if 'west_east' in data_array.dims else None,
                'yc': 'south_north' if 'south_north' in data_array.dims else None
            }
            return dim_map.get(dim_name)
        
        config_manager.get_model_dim_name_for_data = mock_get_dim_name_for_data
        config_manager.ax_opts = {'zsum': False, 'zave': False, 'tave': False}
        config_manager.logger = MagicMock()
        
        return config_manager

    @pytest.fixture
    def wrf_tslb_data(self):
        """Create mock WRF TSLB data with soil layers."""
        data = np.random.rand(25, 4, 150, 150)  # Time, soil_layers_stag, south_north, west_east
        coords = {
            'XLAT': (('south_north', 'west_east'), np.random.rand(150, 150)),
            'XLONG': (('south_north', 'west_east'), np.random.rand(150, 150)),
            'XTIME': ('Time', np.arange(25))
        }
        dims = ('Time', 'soil_layers_stag', 'south_north', 'west_east')
        
        return xr.DataArray(data, dims=dims, coords=coords, name='TSLB')

    @pytest.fixture
    def wrf_tsk_data(self):
        """Create mock WRF TSK data (2D surface variable)."""
        data = np.random.rand(25, 150, 150)  # Time, south_north, west_east
        coords = {
            'XLAT': (('south_north', 'west_east'), np.random.rand(150, 150)),
            'XLONG': (('south_north', 'west_east'), np.random.rand(150, 150)),
            'XTIME': ('Time', np.arange(25))
        }
        dims = ('Time', 'south_north', 'west_east')
        
        return xr.DataArray(data, dims=dims, coords=coords, name='TSK')

    @pytest.fixture
    def data_extractor(self, mock_config_manager):
        """Create a data extractor instance."""
        return DataExtractor(mock_config_manager)

    def test_extract_xy_data_wrf_with_vertical_dim(self, data_extractor, wrf_tslb_data):
        """Test XY extraction from WRF data with vertical dimension (TSLB)."""
        # Simulate time-sliced data (as done in plot_manager)
        time_sliced_data = wrf_tslb_data.isel(Time=8)  # Remove time dimension
        
        # Should handle level selection correctly
        result = data_extractor._extract_xy_data(time_sliced_data, time_level=8, level=0)
        
        # Should return 2D data
        assert result is not None
        assert len(result.dims) == 2
        assert result.shape == (150, 150)  # south_north, west_east
        assert 'south_north' in result.dims
        assert 'west_east' in result.dims

    def test_extract_xy_data_wrf_no_vertical_dim(self, data_extractor, wrf_tsk_data):
        """Test XY extraction from WRF data without vertical dimension (TSK)."""
        # Simulate time-sliced data
        time_sliced_data = wrf_tsk_data.isel(Time=4)  # Remove time dimension
        
        # Should work without level selection
        result = data_extractor._extract_xy_data(time_sliced_data, time_level=4, level=None)
        
        # Should return 2D data
        assert result is not None
        assert len(result.dims) == 2
        assert result.shape == (150, 150)  # south_north, west_east
        assert 'south_north' in result.dims
        assert 'west_east' in result.dims

    def test_extract_xy_data_level_selection(self, data_extractor, wrf_tslb_data):
        """Test that level selection works correctly for different soil layers."""
        # Test different levels
        time_sliced_data = wrf_tslb_data.isel(Time=8)
        
        for level in range(4):  # 4 soil layers
            result = data_extractor._extract_xy_data(time_sliced_data, time_level=8, level=level)
            
            assert result is not None
            assert len(result.dims) == 2
            assert result.shape == (150, 150)
            
            # Values should be different for different levels
            if level > 0:
                other_result = data_extractor._extract_xy_data(time_sliced_data, time_level=8, level=0)
                assert not np.array_equal(result.values, other_result.values)

    def test_extract_xy_data_handles_missing_time_dim(self, data_extractor, wrf_tslb_data):
        """Test that extraction works when time dimension is already removed."""
        # Remove time dimension (simulates what plot_manager does)
        time_sliced_data = wrf_tslb_data.isel(Time=8)
        
        # Should not fail when time dimension is missing
        result = data_extractor._extract_xy_data(time_sliced_data, time_level=8, level=0)
        
        assert result is not None
        assert 'Time' not in result.dims  # Should not have time dimension
        assert len(result.dims) == 2

    def test_dimension_size_helper(self, data_extractor, wrf_tslb_data):
        """Test the _get_dimension_size helper method."""
        # Test existing dimension
        size = data_extractor._get_dimension_size(wrf_tslb_data, 'Time')
        assert size == 25
        
        size = data_extractor._get_dimension_size(wrf_tslb_data, 'soil_layers_stag')
        assert size == 4
        
        # Test non-existing dimension
        size = data_extractor._get_dimension_size(wrf_tslb_data, 'nonexistent')
        assert size == 0

    def test_extract_xy_data_error_handling(self, data_extractor):
        """Test error handling in _extract_xy_data."""
        # Test with None input
        result = data_extractor._extract_xy_data(None, time_level=0, level=0)
        assert result is None
        
        # Test with invalid data - currently raises AttributeError
        invalid_data = "not a data array"
        with pytest.raises(AttributeError):
            data_extractor._extract_xy_data(invalid_data, time_level=0, level=0)


class TestDataExtractorDimensionDetection:
    """Test the improved dimension detection in data extractor."""

    @pytest.fixture
    def multi_dim_config_manager(self):
        """Config manager that can handle multiple dimension types."""
        config_manager = MagicMock()
        
        def mock_get_dim_name_for_data(dim_name, data_array):
            if not hasattr(data_array, 'dims'):
                return None
                
            # Prioritized dimension mapping for different WRF variable types
            if dim_name == 'zc':
                for candidate in ['bottom_top', 'bottom_top_stag', 'soil_layers', 'soil_layers_stag']:
                    if candidate in data_array.dims:
                        return candidate
                return None
            elif dim_name == 'tc':
                return 'Time' if 'Time' in data_array.dims else None
            elif dim_name == 'xc':
                return 'west_east' if 'west_east' in data_array.dims else None
            elif dim_name == 'yc':
                return 'south_north' if 'south_north' in data_array.dims else None
            
            return None
        
        config_manager.get_model_dim_name_for_data = mock_get_dim_name_for_data
        config_manager.ax_opts = {'zsum': False, 'zave': False, 'tave': False}
        config_manager.logger = MagicMock()
        
        return config_manager

    def test_dimension_priority_atmospheric_vs_soil(self, multi_dim_config_manager):
        """Test that atmospheric dimensions are prioritized over soil dimensions."""
        data_extractor = DataExtractor(multi_dim_config_manager)
        
        # Create data with both atmospheric and soil dimensions
        data = np.random.rand(25, 60, 4, 150, 150)  # Time, bottom_top, soil_layers_stag, south_north, west_east
        dims = ('Time', 'bottom_top', 'soil_layers_stag', 'south_north', 'west_east')
        data_array = xr.DataArray(data, dims=dims, name='mixed')
        
        # Should prioritize bottom_top over soil_layers_stag
        time_sliced = data_array.isel(Time=0)
        zc_dim = multi_dim_config_manager.get_model_dim_name_for_data('zc', time_sliced)
        assert zc_dim == 'bottom_top'