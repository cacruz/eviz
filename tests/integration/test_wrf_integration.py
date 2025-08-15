"""Integration tests for WRF data processing and plotting."""

import pytest
import numpy as np
import xarray as xr
import tempfile
import os
from unittest.mock import MagicMock, patch

from eviz.lib.config.config_manager import ConfigManager


class TestWRFIntegration:
    """Integration tests for WRF data processing pipeline."""

    @pytest.fixture
    def mock_wrf_dataset(self):
        """Create a comprehensive mock WRF dataset with multiple variables."""
        # Create realistic WRF dimensions
        time_size = 25
        soil_layers = 4
        atmos_levels = 60
        south_north = 150
        west_east = 150

        # Create coordinate data
        lat_data = np.linspace(35.0, 41.0, south_north)
        lon_data = np.linspace(-103.0, -96.0, west_east)
        lat_2d, lon_2d = np.meshgrid(lat_data, lon_data, indexing='ij')
        
        time_data = np.arange(time_size)
        
        # Create various WRF variables with different dimensionalities
        variables = {}
        coords = {
            'XLAT': (('south_north', 'west_east'), lat_2d),
            'XLONG': (('south_north', 'west_east'), lon_2d),
            'XTIME': ('Time', time_data)
        }
        
        # 2D+time variables (surface variables)
        for var in ['TSK', 'ALBEDO', 'HFX', 'LH', 'EMISS', 'QFX', 'GRDFLX', 'SWDOWN', 'T2', 'Q2']:
            variables[var] = (
                ('Time', 'south_north', 'west_east'),
                np.random.rand(time_size, south_north, west_east) * 100 + 250  # Realistic temperature range
            )
        
        # 3D+time variables (soil variables)
        for var in ['TSLB', 'SMOIS']:
            variables[var] = (
                ('Time', 'soil_layers_stag', 'south_north', 'west_east'),
                np.random.rand(time_size, soil_layers, south_north, west_east) * 50 + 270
            )
        
        # 3D+time atmospheric variables (if needed for future tests)
        # variables['T'] = (
        #     ('Time', 'bottom_top', 'south_north', 'west_east'),
        #     np.random.rand(time_size, atmos_levels, south_north, west_east) * 50 + 250
        # )
        
        # Create dimensions
        dims = {
            'Time': time_size,
            'south_north': south_north,
            'west_east': west_east,
            'soil_layers_stag': soil_layers,
            'bottom_top': atmos_levels,
            'bottom_top_stag': atmos_levels + 1,
            'west_east_stag': west_east + 1,
            'south_north_stag': south_north + 1
        }
        
        # Create the dataset
        ds = xr.Dataset(
            data_vars=variables,
            coords=coords,
            attrs={
                'TITLE': 'OUTPUT FROM WRF V4.6.0 MODEL',
                'START_DATE': '2015-07-11_12:00:00',
                'SIMULATION_START_DATE': '2015-07-11_12:00:00'
            }
        )
        
        # Set dimension sizes
        for dim_name, size in dims.items():
            if dim_name not in ds.dims:
                # Add dimension coordinates if they don't exist
                if dim_name not in coords:
                    ds = ds.assign_coords({dim_name: np.arange(size)})
        
        return ds

    @pytest.fixture
    def temporary_wrf_file(self, mock_wrf_dataset):
        """Create a temporary WRF NetCDF file."""
        with tempfile.NamedTemporaryFile(suffix='.nc', delete=False) as tmp:
            mock_wrf_dataset.to_netcdf(tmp.name)
            yield tmp.name
            os.unlink(tmp.name)

    @pytest.fixture
    def wrf_config_manager(self):
        """Create a ConfigManager configured for WRF processing."""
        # Mock the required configuration objects
        mock_input_config = MagicMock()
        mock_output_config = MagicMock()
        mock_system_config = MagicMock()
        mock_history_config = MagicMock()
        mock_app_data = MagicMock()
        
        # Create mock config
        mock_config = MagicMock()
        mock_config.app_data = mock_app_data
        mock_config.source_names = ['wrf']
        
        # Set up realistic meta_coordinates
        meta_coords = {
            'tc': {
                'wrf': {'dim': 'Time'},
                'gridded': 'time,Time,rec_dim,ntimemax,t,rec_dim'
            },
            'zc': {
                'wrf': {'dim': 'bottom_top,bottom_top_stag,soil_layers,soil_layers_stag'},
                'gridded': 'lev,level,levels,plev,lm,eta_dim,z,eta_dim'
            },
            'xc': {
                'wrf': {'dim': 'west_east', 'coords': 'XLONG,XLONG_U,XLONG_V'},
                'gridded': 'lon,longitude,im,Longitude,x,longitude_dim'
            },
            'yc': {
                'wrf': {'dim': 'south_north', 'coords': 'XLAT,XLAT_U,XLAT_V'},
                'gridded': 'lat,latitude,jm,Latitude,y,latitude_dim'
            }
        }
        
        mock_config.meta_coords = meta_coords
        
        config_manager = ConfigManager(
            input_config=mock_input_config,
            output_config=mock_output_config,
            system_config=mock_system_config,
            history_config=mock_history_config,
            config=mock_config
        )
        
        config_manager.ds_index = 0
        
        return config_manager

    def test_wrf_dimension_detection_integration(self, mock_wrf_dataset, wrf_config_manager):
        """Test end-to-end dimension detection for various WRF variables."""
        
        # Test 2D surface variables (TSK)
        tsk = mock_wrf_dataset['TSK']
        tc_dim = wrf_config_manager.get_model_dim_name_for_data('tc', tsk)
        zc_dim = wrf_config_manager.get_model_dim_name_for_data('zc', tsk)
        
        assert tc_dim == 'Time'
        assert zc_dim is None  # No vertical dimension for surface variables
        
        # Test 3D soil variables (TSLB)
        tslb = mock_wrf_dataset['TSLB']
        tc_dim = wrf_config_manager.get_model_dim_name_for_data('tc', tslb)
        zc_dim = wrf_config_manager.get_model_dim_name_for_data('zc', tslb)
        
        assert tc_dim == 'Time'
        assert zc_dim == 'soil_layers_stag'  # Should find soil layers
        
    def test_wrf_time_slicing_simulation(self, mock_wrf_dataset, wrf_config_manager):
        """Test dimension detection after time slicing (simulates plot_manager behavior)."""
        
        # Simulate plot_manager time slicing
        tslb_original = mock_wrf_dataset['TSLB']
        tslb_time_sliced = tslb_original.isel(Time=8)  # Remove Time dimension
        
        # Should still detect vertical dimension after time slicing
        zc_dim = wrf_config_manager.get_model_dim_name_for_data('zc', tslb_time_sliced)
        tc_dim = wrf_config_manager.get_model_dim_name_for_data('tc', tslb_time_sliced)
        
        assert zc_dim == 'soil_layers_stag'
        assert tc_dim is None  # Time dimension removed by slicing
        
        # Check dimensions
        assert 'Time' not in tslb_time_sliced.dims
        assert 'soil_layers_stag' in tslb_time_sliced.dims
        assert tslb_time_sliced.shape == (4, 150, 150)  # soil_layers_stag, south_north, west_east

    def test_wrf_level_selection_simulation(self, mock_wrf_dataset, wrf_config_manager):
        """Test level selection on time-sliced WRF data."""
        
        # Start with 4D TSLB data
        tslb = mock_wrf_dataset['TSLB']
        assert tslb.shape == (25, 4, 150, 150)  # Time, soil_layers_stag, south_north, west_east
        
        # Simulate plot_manager: time slice first
        tslb_time_sliced = tslb.isel(Time=8)
        assert tslb_time_sliced.shape == (4, 150, 150)  # soil_layers_stag, south_north, west_east
        
        # Simulate data_extractor: level selection
        zc_dim = wrf_config_manager.get_model_dim_name_for_data('zc', tslb_time_sliced)
        assert zc_dim == 'soil_layers_stag'
        
        # Select level 0 (first soil layer)
        tslb_level_selected = tslb_time_sliced.isel(soil_layers_stag=0)
        assert tslb_level_selected.shape == (150, 150)  # south_north, west_east
        
        # Verify it's now 2D and ready for plotting
        assert len(tslb_level_selected.dims) == 2
        assert 'south_north' in tslb_level_selected.dims
        assert 'west_east' in tslb_level_selected.dims

    def test_wrf_multiple_variables_processing(self, mock_wrf_dataset, wrf_config_manager):
        """Test processing multiple WRF variables with different dimensionalities."""
        
        variable_tests = [
            # (variable_name, expected_has_vertical_dim, expected_zc_dim)
            ('TSK', False, None),
            ('ALBEDO', False, None),
            ('HFX', False, None),
            ('TSLB', True, 'soil_layers_stag'),
            ('SMOIS', True, 'soil_layers_stag'),
        ]
        
        for var_name, expected_has_vertical, expected_zc_dim in variable_tests:
            var_data = mock_wrf_dataset[var_name]
            
            # Test original data
            zc_dim = wrf_config_manager.get_model_dim_name_for_data('zc', var_data)
            has_vertical = zc_dim is not None and zc_dim in var_data.dims
            
            assert has_vertical == expected_has_vertical, f"Failed for {var_name}"
            assert zc_dim == expected_zc_dim, f"Failed for {var_name}"
            
            # Test after time slicing
            time_sliced = var_data.isel(Time=4)
            zc_dim_sliced = wrf_config_manager.get_model_dim_name_for_data('zc', time_sliced)
            
            assert zc_dim_sliced == expected_zc_dim, f"Failed after time slicing for {var_name}"

    def test_wrf_coordinate_detection(self, mock_wrf_dataset, wrf_config_manager):
        """Test WRF coordinate detection (XLAT, XLONG)."""
        
        tsk = mock_wrf_dataset['TSK']
        
        # Test horizontal coordinates  
        xc_dim = wrf_config_manager.get_model_dim_name_for_data('xc', tsk)
        yc_dim = wrf_config_manager.get_model_dim_name_for_data('yc', tsk)
        
        assert xc_dim == 'west_east'
        assert yc_dim == 'south_north'
        
        # Verify coordinates exist
        assert 'XLAT' in tsk.coords
        assert 'XLONG' in tsk.coords
        assert 'XTIME' in tsk.coords

    def test_realistic_wrf_data_structure(self, mock_wrf_dataset):
        """Test that mock data structure matches real WRF output."""
        
        # Verify expected variables exist
        expected_vars = ['TSK', 'ALBEDO', 'TSLB', 'SMOIS', 'HFX', 'LH', 'EMISS', 'QFX', 'GRDFLX', 'SWDOWN', 'T2', 'Q2']
        for var in expected_vars:
            assert var in mock_wrf_dataset.data_vars
        
        # Verify expected coordinates
        expected_coords = ['XLAT', 'XLONG', 'XTIME']
        for coord in expected_coords:
            assert coord in mock_wrf_dataset.coords
        
        # Verify expected dimensions
        expected_dims = ['Time', 'south_north', 'west_east', 'soil_layers_stag']
        for dim in expected_dims:
            assert dim in mock_wrf_dataset.dims
        
        # Verify specific variable structures
        assert mock_wrf_dataset['TSK'].dims == ('Time', 'south_north', 'west_east')
        assert mock_wrf_dataset['TSLB'].dims == ('Time', 'soil_layers_stag', 'south_north', 'west_east')
        assert mock_wrf_dataset['SMOIS'].dims == ('Time', 'soil_layers_stag', 'south_north', 'west_east')

    def test_error_conditions(self, wrf_config_manager):
        """Test error handling in WRF dimension detection."""
        
        # Test with invalid data
        result = wrf_config_manager.get_model_dim_name_for_data('zc', None)
        assert result is None
        
        # Test with data missing expected dimensions
        minimal_data = xr.DataArray([1, 2, 3], dims=['x'], name='minimal')
        result = wrf_config_manager.get_model_dim_name_for_data('zc', minimal_data)
        assert result is None
        
        # Test with unknown dimension type
        tsk_data = xr.DataArray(np.random.rand(25, 150, 150), 
                               dims=('Time', 'south_north', 'west_east'), 
                               name='TSK')
        result = wrf_config_manager.get_model_dim_name_for_data('unknown_dim', tsk_data)
        assert result is None


class TestWRFRegressionPrevention:
    """Tests to prevent regression of the specific issues that were fixed."""

    def test_tslb_dimension_detection_regression(self):
        """
        Regression test for TSLB dimension detection issue.
        
        Previously, TSLB with dimensions ('Time', 'soil_layers_stag', 'south_north', 'west_east')
        was incorrectly getting zc_dim='bottom_top' instead of 'soil_layers_stag'.
        """
        from eviz.lib.config.config_manager import ConfigManager
        from unittest.mock import MagicMock
        
        # Set up config manager like in the real system
        mock_config = MagicMock()
        mock_config.app_data = MagicMock()
        mock_config.source_names = ['wrf']
        
        # Set up meta_coords as in real system
        mock_config.meta_coords = {
            'zc': {
                'wrf': {'dim': 'bottom_top,bottom_top_stag,soil_layers,soil_layers_stag'},
                'gridded': 'lev,level,levels,plev,lm,eta_dim,z,eta_dim'
            }
        }
        
        config_manager = ConfigManager(
            input_config=MagicMock(),
            output_config=MagicMock(),
            system_config=MagicMock(),
            history_config=MagicMock(),
            config=mock_config
        )
        config_manager.ds_index = 0
        
        # Create TSLB-like data
        tslb_data = xr.DataArray(
            np.random.rand(25, 4, 150, 150),
            dims=('Time', 'soil_layers_stag', 'south_north', 'west_east'),
            name='TSLB'
        )
        
        # The new method should correctly find soil_layers_stag
        zc_dim = config_manager.get_model_dim_name_for_data('zc', tslb_data)
        assert zc_dim == 'soil_layers_stag', "Regression: TSLB dimension detection failed"

    def test_time_dimension_handling_regression(self):
        """
        Regression test for time dimension handling in data extractor.
        
        Previously, data_extractor would fail with "Time dimension 'Time' not found"
        when data was already time-sliced by plot_manager.
        """
        from eviz.lib.data.data_extractor import DataExtractor
        from unittest.mock import MagicMock
        
        # Set up mock config manager
        config_manager = MagicMock()
        config_manager.get_model_dim_name_for_data.side_effect = lambda dim, data: {
            'tc': 'Time' if 'Time' in data.dims else None,
            'zc': 'soil_layers_stag' if 'soil_layers_stag' in data.dims else None
        }.get(dim)
        config_manager.ax_opts = {'zsum': False, 'zave': False, 'tave': False}
        config_manager.logger = MagicMock()
        
        data_extractor = DataExtractor(config_manager)
        
        # Create time-sliced data (simulates what plot_manager does)
        time_sliced_tslb = xr.DataArray(
            np.random.rand(4, 150, 150),  # No Time dimension
            dims=('soil_layers_stag', 'south_north', 'west_east'),
            name='TSLB'
        )
        
        # Should not fail when time dimension is missing
        result = data_extractor._extract_xy_data(time_sliced_tslb, time_level=8, level=0)
        
        # Should successfully extract 2D data
        assert result is not None, "Regression: Failed to handle time-sliced data"
        assert len(result.dims) == 2, "Regression: Should return 2D data"
        assert result.shape == (150, 150), "Regression: Wrong output shape"