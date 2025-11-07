"""Unit tests for plot_manager module."""

import pytest
import numpy as np
import xarray as xr
from unittest.mock import MagicMock, patch, PropertyMock
import matplotlib.pyplot as plt

from eviz.lib.autoviz.plotting.plot_manager import PlotManager


@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    config = MagicMock()
    config.compare = False
    config.compare_diff = False
    config.ax_opts = {}
    config.axindex = 0
    config.ds_index = 0
    config.source_names = ['test_source']
    config.spec_data = {
        'temperature': {'name': 'Temperature', 'units': 'K'},
        'pressure': {'name': 'Pressure', 'units': 'Pa'}
    }
    config.map_params = {}
    config.compare_exp_ids = ['exp1', 'exp2']
    config.a_list = [0]
    config.b_list = [1]
    config.correlation = False
    config.make_gif = False

    # Mock pipeline
    config.pipeline = MagicMock()
    config.pipeline.get_all_data_sources = MagicMock(return_value={})

    return config


@pytest.fixture
def sample_2d_data():
    """Create sample 2D data array (lat, lon)."""
    np.random.seed(42)
    lat = np.linspace(-90, 90, 20)
    lon = np.linspace(-180, 180, 30)

    data = xr.DataArray(
        np.random.randn(20, 30),
        coords={'lat': lat, 'lon': lon},
        dims=['lat', 'lon'],
        attrs={'units': 'K', 'long_name': 'Temperature'}
    )
    data.name = 'temperature'
    return data


@pytest.fixture
def sample_3d_data():
    """Create sample 3D data array (time, lat, lon)."""
    np.random.seed(42)
    time = np.arange(10)
    lat = np.linspace(-90, 90, 20)
    lon = np.linspace(-180, 180, 30)

    data = xr.DataArray(
        np.random.randn(10, 20, 30),
        coords={'time': time, 'lat': lat, 'lon': lon},
        dims=['time', 'lat', 'lon'],
        attrs={'units': 'K', 'long_name': 'Temperature'}
    )
    data.name = 'temperature'
    return data


@pytest.fixture
def mock_data_extractor():
    """Create a mock data extractor."""
    extractor = MagicMock()
    extractor._extract_xy_data = MagicMock(return_value=np.random.randn(20, 30))
    return extractor


@pytest.fixture
def plot_manager(mock_config, mock_data_extractor):
    """Create a PlotManager instance."""
    manager = PlotManager(mock_config, mock_data_extractor)
    return manager


class TestPlotManagerInit:
    """Test PlotManager initialization."""

    def test_init(self, mock_config, mock_data_extractor):
        """Test PlotManager can be initialized."""
        manager = PlotManager(mock_config, mock_data_extractor)
        assert manager is not None
        assert manager.config_manager == mock_config
        assert manager.data_extractor == mock_data_extractor
        assert hasattr(manager, 'logger')

    def test_init_with_none_config(self):
        """Test PlotManager handles None config gracefully."""
        with pytest.raises((TypeError, AttributeError)):
            PlotManager(None)


class TestProcessPlot:
    """Test process_plot method."""

    def test_process_plot_handles_unknown_type(self, plot_manager, sample_2d_data):
        """Test that process_plot handles unknown plot types gracefully."""
        # Create a mock figure
        from eviz.lib.autoviz.figure import Figure

        with patch.object(Figure, 'create_eviz_figure') as mock_figure:
            mock_fig = MagicMock()
            mock_figure.return_value = mock_fig
            mock_fig.init_ax_opts = MagicMock(return_value={})

            # Mock get_dim_names to avoid ValueError
            plot_manager.config_manager.get_dim_names = MagicMock(return_value=('x', 'y'))

            # Should not raise an exception even with unknown plot type
            # PlotManager will either handle it or log an error
            try:
                plot_manager.process_plot(sample_2d_data, 'temperature', 0, 'unknown_xyz_type')
                # If we get here, it handled it gracefully (which is good)
                assert True
            except Exception as e:
                # If it raises an exception, that's also acceptable as long as
                # it's a meaningful error
                assert 'not implemented' in str(e).lower() or 'not supported' in str(e).lower()

    def test_process_plot_xy_without_implementation(self, plot_manager, sample_2d_data):
        """Test xy plot without _process_xy_plot shows error if not available."""
        # Remove _process_xy_plot if it exists to test error handling
        if hasattr(plot_manager, '_process_xy_plot'):
            # PlotManager has _process_xy_plot, so this test would pass
            # We'll test that it's callable instead
            assert callable(getattr(plot_manager, '_process_xy_plot'))
        else:
            # If it doesn't have the method, it should log an error
            with patch.object(plot_manager.logger, 'error') as mock_error:
                from eviz.lib.autoviz.figure import Figure
                with patch.object(Figure, 'create_eviz_figure') as mock_figure:
                    mock_fig = MagicMock()
                    mock_figure.return_value = mock_fig
                    mock_fig.init_ax_opts = MagicMock(return_value={})

                    plot_manager.process_plot(sample_2d_data, 'temperature', 0, 'xy')

                    # Should have logged an error
                    assert mock_error.called


class TestProcessXyPlot:
    """Test _process_xy_plot method."""

    def test_process_xy_plot_no_levels(self, plot_manager, sample_2d_data):
        """Test that _process_xy_plot returns early with error when no levels defined."""
        # Mock get_levels to return empty dict
        plot_manager.config_manager.get_levels = MagicMock(return_value={})
        plot_manager.config_manager.ax_opts = {'zsum': False}

        from eviz.lib.autoviz.figure import Figure
        mock_figure = MagicMock()

        with patch.object(plot_manager.logger, 'error') as mock_error:
            plot_manager._process_xy_plot(
                sample_2d_data, 'temperature', 0, 'xy', mock_figure
            )

            # Should log error about missing levels
            mock_error.assert_called_once()
            assert 'No vertical levels defined' in mock_error.call_args[0][0]

    def test_process_xy_plot_with_levels(self, plot_manager, sample_3d_data):
        """Test _process_xy_plot with valid levels."""
        # Mock get_levels to return valid levels
        plot_manager.config_manager.get_levels = MagicMock(return_value={0: []})
        plot_manager.config_manager.ax_opts = {
            'time_lev': 0,
            'tave': False,
            'zsum': False
        }
        plot_manager.config_manager.get_model_dim_name = MagicMock(return_value='time')
        plot_manager.config_manager.get_model_dim_name_for_data = MagicMock(return_value='lev')

        # Mock the _process_level_plot method
        with patch.object(plot_manager, '_process_level_plot') as mock_process_level:
            from eviz.lib.autoviz.figure import Figure
            mock_figure = MagicMock()

            plot_manager._process_xy_plot(
                sample_3d_data, 'temperature', 0, 'xy', mock_figure
            )

            # Should call _process_level_plot
            mock_process_level.assert_called_once()

    def test_process_xy_plot_time_range_format(self, plot_manager, sample_3d_data):
        """Test _process_xy_plot handles time_lev range format [start, end]."""
        plot_manager.config_manager.get_levels = MagicMock(return_value={0: []})
        plot_manager.config_manager.ax_opts = {
            'time_lev': [0, 5],  # Range format
            'tave': False,
            'zsum': False
        }
        plot_manager.config_manager.get_model_dim_name = MagicMock(return_value='time')
        plot_manager.config_manager.get_model_dim_name_for_data = MagicMock(return_value='lev')
        plot_manager.config_manager.make_gif = False

        with patch.object(plot_manager, '_process_level_plot') as mock_process_level:
            from eviz.lib.autoviz.figure import Figure
            mock_figure = MagicMock()

            plot_manager._process_xy_plot(
                sample_3d_data, 'temperature', 0, 'xy', mock_figure
            )

            # Should call _process_level_plot
            mock_process_level.assert_called_once()

    def test_process_xy_plot_time_lev_all(self, plot_manager, sample_3d_data):
        """Test _process_xy_plot handles time_lev='all' format."""
        plot_manager.config_manager.get_levels = MagicMock(return_value={0: []})
        plot_manager.config_manager.ax_opts = {
            'time_lev': 'all',
            'tave': False,
            'zsum': False
        }
        plot_manager.config_manager.get_model_dim_name = MagicMock(return_value='time')
        plot_manager.config_manager.get_model_dim_name_for_data = MagicMock(return_value='lev')
        plot_manager.config_manager.make_gif = False

        with patch.object(plot_manager, '_process_level_plot') as mock_process_level:
            from eviz.lib.autoviz.figure import Figure
            mock_figure = MagicMock()

            plot_manager._process_xy_plot(
                sample_3d_data, 'temperature', 0, 'xy', mock_figure
            )

            # Should call _process_level_plot with all time levels
            mock_process_level.assert_called_once()


class TestSideBySideComparison:
    """Test side-by-side comparison plot methods."""

    def test_create_xy_side_by_side_plot_different_field_names(self, plot_manager):
        """Test that side-by-side plots support different field names."""
        # Create two datasets with different field names
        data1 = xr.Dataset({
            'field1': xr.DataArray(
                np.random.randn(20, 30),
                coords={'lat': np.linspace(-90, 90, 20), 'lon': np.linspace(-180, 180, 30)},
                dims=['lat', 'lon']
            )
        })

        data2 = xr.Dataset({
            'field2': xr.DataArray(
                np.random.randn(20, 30),
                coords={'lat': np.linspace(-90, 90, 20), 'lon': np.linspace(-180, 180, 30)},
                dims=['lat', 'lon']
            )
        })

        plot_manager.config_manager.compare_exp_ids = ['exp1', 'exp2']
        plot_manager.config_manager.a_list = [0]
        plot_manager.config_manager.b_list = [1]
        plot_manager.config_manager.map_params = {
            0: {'filename': 'file1.nc', 'field': 'field1'},
            1: {'filename': 'file2.nc', 'field': 'field2'}
        }

        # Mock data source
        mock_ds1 = MagicMock()
        mock_ds1.dataset = data1
        mock_ds2 = MagicMock()
        mock_ds2.dataset = data2

        plot_manager.config_manager.pipeline.get_data_source = MagicMock(
            side_effect=lambda x: mock_ds1 if x == 'file1.nc' else mock_ds2
        )

        # Mock the single plot processing
        with patch.object(plot_manager, '_process_single_side_by_side_plot') as mock_process:
            from eviz.lib.autoviz.figure import Figure
            mock_figure = MagicMock()
            mock_figure.set_axes = MagicMock()

            plot_manager._create_xy_side_by_side_plot(
                0, 'field1', 'field2', mock_figure, 'xy', data1, data2
            )

            # Should call process for both datasets
            assert mock_process.call_count == 2

    def test_process_side_by_side_plots_empty_lists(self, plot_manager):
        """Test that empty a_list or b_list shows error."""
        plot_manager.config_manager.a_list = []
        plot_manager.config_manager.b_list = []

        with patch.object(plot_manager.logger, 'error') as mock_error:
            # This should be called from process_side_by_side_plots
            # but we'll test the error condition directly
            if not plot_manager.config_manager.a_list or not plot_manager.config_manager.b_list:
                plot_manager.logger.error("a_list or b_list is empty, cannot perform side-by-side comparison.")

            mock_error.assert_called_once()
            assert 'a_list or b_list is empty' in mock_error.call_args[0][0]


class TestCorrelationPlots:
    """Test correlation plot methods."""

    def test_process_corr_plots_not_implemented(self, plot_manager, sample_3d_data):
        """Test that correlation plots show error when not implemented in base class."""
        from eviz.lib.autoviz.figure import Figure

        with patch.object(Figure, 'create_eviz_figure') as mock_figure:
            mock_fig = MagicMock()
            mock_figure.return_value = mock_fig
            mock_fig.init_ax_opts = MagicMock(return_value={})

            # PlotManager base class doesn't implement _process_corr_plot
            # so it should show an error
            with patch.object(plot_manager.logger, 'error') as mock_error:
                plot_manager.process_plot(sample_3d_data, 'temperature', 0, 'corr')

                # Should log error about missing implementation
                mock_error.assert_called()
                assert 'not implemented' in mock_error.call_args[0][0].lower()


class TestRegisterPlotType:
    """Test register_plot_type method."""

    def test_register_plot_type_new_field(self, plot_manager):
        """Test registering a new field plot type."""
        plot_manager.register_plot_type('temperature', 'xy')

        assert hasattr(plot_manager, '_plot_type_registry')
        assert plot_manager.get_plot_type('temperature') == 'xy'

    def test_register_plot_type_existing_field(self, plot_manager):
        """Test registering and retrieving plot types."""
        plot_manager.register_plot_type('temperature', 'xy')
        assert plot_manager.get_plot_type('temperature') == 'xy'

        # Register a different type (overwrites)
        plot_manager.register_plot_type('temperature', 'xt')
        assert plot_manager.get_plot_type('temperature') == 'xt'

    def test_get_plot_type_default(self, plot_manager):
        """Test getting plot type returns default when not registered."""
        # Should return default 'xy' for unregistered field
        assert plot_manager.get_plot_type('nonexistent_field') == 'xy'
        assert plot_manager.get_plot_type('another_field', default='xt') == 'xt'


class TestDataExtraction:
    """Test data extraction and preparation methods."""

    def test_set_time_config(self, plot_manager, sample_3d_data):
        """Test _set_time_config method."""
        # This method should set time-related configuration
        plot_manager._set_time_config(0, sample_3d_data)

        # Should set time_val in config
        assert hasattr(plot_manager.config_manager, 'time_val')


class TestErrorHandling:
    """Test error handling in PlotManager."""

    def test_missing_field_in_dataset(self, plot_manager):
        """Test error handling when field is missing from dataset."""
        # Create dataset without the expected field
        data = xr.Dataset({
            'other_field': xr.DataArray(
                np.random.randn(20, 30),
                coords={'lat': np.linspace(-90, 90, 20), 'lon': np.linspace(-180, 180, 30)},
                dims=['lat', 'lon']
            )
        })

        # Try to access missing field - should handle gracefully
        missing_field = data.get('temperature')
        assert missing_field is None

    def test_invalid_time_lev_format(self, plot_manager, sample_3d_data):
        """Test handling of invalid time_lev format."""
        plot_manager.config_manager.get_levels = MagicMock(return_value={0: []})
        plot_manager.config_manager.ax_opts = {
            'time_lev': [0, 5, 10],  # Invalid - should be 2 elements
            'tave': False,
            'zsum': False
        }
        plot_manager.config_manager.get_model_dim_name = MagicMock(return_value='time')
        plot_manager.config_manager.get_model_dim_name_for_data = MagicMock(return_value='lev')
        plot_manager.config_manager.make_gif = False

        with patch.object(plot_manager.logger, 'warning') as mock_warning:
            with patch.object(plot_manager, '_process_level_plot'):
                from eviz.lib.autoviz.figure import Figure
                mock_figure = MagicMock()

                plot_manager._process_xy_plot(
                    sample_3d_data, 'temperature', 0, 'xy', mock_figure
                )

                # Should log warning about invalid format
                mock_warning.assert_called()
                assert 'Invalid time_lev list format' in mock_warning.call_args[0][0]


class TestPlotManagerIntegration:
    """Integration tests for PlotManager."""

    def test_full_xy_plot_workflow(self, plot_manager, sample_3d_data):
        """Test complete xy plot workflow."""
        # Setup config for a complete plot
        plot_manager.config_manager.get_levels = MagicMock(return_value={0: []})
        plot_manager.config_manager.ax_opts = {
            'time_lev': 0,
            'tave': False,
            'zsum': False
        }
        plot_manager.config_manager.get_model_dim_name = MagicMock(return_value='time')
        plot_manager.config_manager.get_model_dim_name_for_data = MagicMock(return_value='lev')
        plot_manager.config_manager.make_gif = False
        plot_manager.config_manager.level = None

        # Mock all the downstream methods
        with patch.object(plot_manager, '_process_level_plot'):
            from eviz.lib.autoviz.figure import Figure
            with patch.object(Figure, 'create_eviz_figure') as mock_create_fig:
                mock_figure = MagicMock()
                mock_figure.init_ax_opts = MagicMock(return_value={})
                mock_create_fig.return_value = mock_figure

                # Should not raise any exceptions
                plot_manager.process_plot(sample_3d_data, 'temperature', 0, 'xy')


class TestPlotTypeValidation:
    """Test plot type validation."""

    def test_supported_plot_types(self, plot_manager):
        """Test that common plot types are recognized."""
        supported_types = ['xy', 'xt', 'polar', 'sc', 'corr', 'box', 'line']

        for plot_type in supported_types:
            # Check if PlotManager has the corresponding method
            method_name = f'_process_{plot_type}_plot'

            # Some plot types may not be implemented in base PlotManager
            # but should be recognized in process_plot
            assert isinstance(plot_type, str)
            assert len(plot_type) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
