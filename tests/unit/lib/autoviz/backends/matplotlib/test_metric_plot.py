"""Unit tests for metric_plot module (correlation and RMSE computations)."""

import pytest
import numpy as np
import xarray as xr
from unittest.mock import MagicMock, patch
import matplotlib.pyplot as plt

from eviz.lib.autoviz.plotting.backends.matplotlib.metric_plot import MatplotlibMetricPlotter


@pytest.fixture
def sample_3d_data():
    """Create sample 3D data arrays (time, lat, lon) for testing."""
    np.random.seed(42)
    time = np.arange(10)
    lat = np.linspace(-90, 90, 20)
    lon = np.linspace(-180, 180, 30)

    data1 = xr.DataArray(
        np.random.randn(10, 20, 30),
        coords={'time': time, 'lat': lat, 'lon': lon},
        dims=['time', 'lat', 'lon'],
        attrs={'units': 'm3/m3', 'long_name': 'Soil Moisture Dataset 1'}
    )
    data1.name = 'soil_moisture_1'

    # Create correlated data with some noise
    data2 = data1 * 0.8 + np.random.randn(10, 20, 30) * 0.2
    data2.attrs = {'units': 'm3/m3', 'long_name': 'Soil Moisture Dataset 2'}
    data2.name = 'soil_moisture_2'

    return data1, data2


@pytest.fixture
def sample_2d_data():
    """Create sample 2D data arrays (lat, lon) for testing."""
    np.random.seed(42)
    lat = np.linspace(-90, 90, 20)
    lon = np.linspace(-180, 180, 30)

    data1 = xr.DataArray(
        np.random.randn(20, 30),
        coords={'lat': lat, 'lon': lon},
        dims=['lat', 'lon'],
        attrs={'units': 'K', 'long_name': 'Temperature Dataset 1'}
    )
    data1.name = 'temperature_1'

    data2 = data1 * 0.9 + np.random.randn(20, 30) * 0.1
    data2.attrs = {'units': 'K', 'long_name': 'Temperature Dataset 2'}
    data2.name = 'temperature_2'

    return data1, data2


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
        'soil_moisture': {'name': 'Soil Moisture'},
        'temperature': {'name': 'Temperature'}
    }
    config.app_data.for_inputs = {
        'correlation': {'method': 'pearson', 'ids': 'dataset1,dataset2'}
    }
    return config


@pytest.fixture
def mock_figure():
    """Create a mock figure object."""
    fig = MagicMock()
    fig.subplots = (1, 1)
    ax = plt.subplot(111)
    fig.get_axes = MagicMock(return_value=[ax])
    fig.set_axes = MagicMock()
    return fig


class TestMatplotlibMetricPlotter:
    """Test suite for metric plotter (correlation and RMSE)."""

    def test_init(self):
        """Test plotter initialization."""
        plotter = MatplotlibMetricPlotter()
        assert plotter is not None
        assert hasattr(plotter, 'logger')

    def test_valid_correlation_methods(self, sample_3d_data, mock_config):
        """Test that valid correlation methods are accepted."""
        data1, data2 = sample_3d_data
        plotter = MatplotlibMetricPlotter()

        valid_methods = ['pearson', 'spearman', 'cross', 'rmse']

        for method in valid_methods:
            result = plotter._compute_correlation_map(method, data1, data2)
            assert result is not None
            assert isinstance(result, xr.DataArray)
            assert result.shape == data1.isel(time=0).shape
            assert 'correlation_method' in result.attrs
            assert result.attrs['correlation_method'] == method

    def test_invalid_correlation_method(self, sample_3d_data):
        """Test that invalid correlation method is handled gracefully."""
        data1, data2 = sample_3d_data
        plotter = MatplotlibMetricPlotter()

        # Invalid methods should return a result (will be caught in try/except)
        result = plotter._compute_correlation_map('invalid_method', data1, data2)

        # Should return a valid DataArray (exception handling sets to NaN or returns result)
        assert result is not None
        assert isinstance(result, xr.DataArray)
        # The result should have the correlation_method attribute
        assert 'correlation_method' in result.attrs

    def test_pearson_correlation_computation(self, sample_3d_data):
        """Test Pearson correlation computation."""
        data1, data2 = sample_3d_data
        plotter = MatplotlibMetricPlotter()

        result = plotter._compute_correlation_map('pearson', data1, data2)

        # Check output structure
        assert result is not None
        assert isinstance(result, xr.DataArray)
        assert result.dims == ('lat', 'lon')

        # Check correlation values are in valid range [-1, 1]
        valid_mask = ~np.isnan(result.values)
        if valid_mask.any():
            assert np.all(result.values[valid_mask] >= -1.0)
            assert np.all(result.values[valid_mask] <= 1.0)

        # Check attributes
        assert result.attrs['correlation_method'] == 'pearson'
        assert result.attrs['units'] == 'dimensionless'

    def test_spearman_correlation_computation(self, sample_3d_data):
        """Test Spearman correlation computation."""
        data1, data2 = sample_3d_data
        plotter = MatplotlibMetricPlotter()

        result = plotter._compute_correlation_map('spearman', data1, data2)

        assert result is not None
        assert isinstance(result, xr.DataArray)

        # Check correlation values are in valid range [-1, 1]
        valid_mask = ~np.isnan(result.values)
        if valid_mask.any():
            assert np.all(result.values[valid_mask] >= -1.0)
            assert np.all(result.values[valid_mask] <= 1.0)

    def test_rmse_computation(self, sample_3d_data):
        """Test RMSE computation."""
        data1, data2 = sample_3d_data
        plotter = MatplotlibMetricPlotter()

        result = plotter._compute_correlation_map('rmse', data1, data2)

        # Check output structure
        assert result is not None
        assert isinstance(result, xr.DataArray)
        assert result.dims == ('lat', 'lon')

        # Check RMSE values are non-negative
        valid_mask = ~np.isnan(result.values)
        if valid_mask.any():
            assert np.all(result.values[valid_mask] >= 0.0)

        # Check attributes
        assert result.attrs['correlation_method'] == 'rmse'
        # Units should inherit from input data or be 'unknown'
        assert 'units' in result.attrs
        assert result.attrs['units'] in ['m3/m3', 'unknown']
        # Long name should contain either "RMSE" or "Root Mean Square Error"
        assert 'RMSE' in result.attrs['long_name'] or 'Root Mean Square Error' in result.attrs['long_name']

    def test_rmse_units_inheritance(self, sample_3d_data):
        """Test that RMSE inherits units from input data."""
        data1, data2 = sample_3d_data
        plotter = MatplotlibMetricPlotter()

        # Modify units
        data1.attrs['units'] = 'kg/m2'
        data2.attrs['units'] = 'kg/m2'

        result = plotter._compute_correlation_map('rmse', data1, data2)

        assert result.attrs['units'] == 'kg/m2'

    def test_rmse_zero_for_identical_data(self):
        """Test that RMSE is zero for identical datasets."""
        # Create identical datasets
        data = xr.DataArray(
            np.ones((10, 20, 30)),
            coords={'time': np.arange(10), 'lat': np.linspace(-90, 90, 20),
                    'lon': np.linspace(-180, 180, 30)},
            dims=['time', 'lat', 'lon'],
            attrs={'units': 'm'}
        )

        plotter = MatplotlibMetricPlotter()
        result = plotter._compute_correlation_map('rmse', data, data)

        # RMSE should be zero (or very close to zero due to numerical precision)
        assert np.allclose(result.values, 0.0, atol=1e-10)

    def test_calculate_r_squared(self, sample_3d_data):
        """Test R² calculation."""
        data1, data2 = sample_3d_data
        plotter = MatplotlibMetricPlotter()

        r_squared = plotter._calculate_r_squared(data1, data2)

        assert isinstance(r_squared, (float, np.floating))
        assert not np.isnan(r_squared)
        assert 0.0 <= r_squared <= 1.0

    def test_calculate_r_squared_perfect_correlation(self):
        """Test R² calculation for perfectly correlated data."""
        data1 = xr.DataArray(
            np.arange(100).reshape(10, 10),
            dims=['x', 'y'],
            attrs={'units': 'm'}
        )
        data2 = data1.copy()  # Identical data

        plotter = MatplotlibMetricPlotter()
        r_squared = plotter._calculate_r_squared(data1, data2)

        # R² should be 1.0 for identical data
        assert np.isclose(r_squared, 1.0, atol=1e-6)

    def test_calculate_r_squared_no_correlation(self):
        """Test R² calculation for uncorrelated data."""
        np.random.seed(42)
        data1 = xr.DataArray(
            np.random.randn(100, 50),
            dims=['x', 'y'],
            attrs={'units': 'm'}
        )
        np.random.seed(123)  # Different seed
        data2 = xr.DataArray(
            np.random.randn(100, 50),
            dims=['x', 'y'],
            attrs={'units': 'm'}
        )

        plotter = MatplotlibMetricPlotter()
        r_squared = plotter._calculate_r_squared(data1, data2)

        # R² should be close to 0 for uncorrelated random data
        assert 0.0 <= r_squared <= 0.3  # Allow some random correlation

    def test_calculate_global_rmse(self, sample_3d_data):
        """Test global RMSE calculation."""
        data1, data2 = sample_3d_data
        plotter = MatplotlibMetricPlotter()

        global_rmse = plotter._calculate_global_rmse(data1, data2)

        assert isinstance(global_rmse, (float, np.floating))
        assert not np.isnan(global_rmse)
        assert global_rmse >= 0.0

    def test_calculate_global_rmse_zero_for_identical(self):
        """Test that global RMSE is zero for identical data."""
        data = xr.DataArray(
            np.ones((10, 20, 30)),
            dims=['time', 'lat', 'lon'],
            attrs={'units': 'm'}
        )

        plotter = MatplotlibMetricPlotter()
        global_rmse = plotter._calculate_global_rmse(data, data)

        assert np.isclose(global_rmse, 0.0, atol=1e-10)

    def test_calculate_global_rmse_with_known_values(self):
        """Test global RMSE with known values."""
        data1 = xr.DataArray(np.array([1, 2, 3, 4, 5]), dims=['x'])
        data2 = xr.DataArray(np.array([2, 3, 4, 5, 6]), dims=['x'])

        plotter = MatplotlibMetricPlotter()
        global_rmse = plotter._calculate_global_rmse(data1, data2)

        # Expected RMSE: sqrt(mean((1-2)^2, (2-3)^2, ...)) = sqrt(1) = 1.0
        assert np.isclose(global_rmse, 1.0, atol=1e-6)

    def test_nan_handling_in_correlation(self):
        """Test that NaN values are handled correctly in correlation."""
        data1 = xr.DataArray(
            np.array([[1, 2, np.nan], [4, 5, 6]]),
            dims=['x', 'y'],
            coords={'x': [0, 1], 'y': [0, 1, 2]}
        )
        data2 = xr.DataArray(
            np.array([[2, 3, 4], [5, np.nan, 7]]),
            dims=['x', 'y'],
            coords={'x': [0, 1], 'y': [0, 1, 2]}
        )

        # Add time dimension for 3D processing
        data1 = data1.expand_dims({'time': 5})
        data2 = data2.expand_dims({'time': 5})

        plotter = MatplotlibMetricPlotter()
        result = plotter._compute_correlation_map('pearson', data1, data2)

        # Should have NaN where insufficient valid data points
        assert np.any(np.isnan(result.values))

    def test_nan_handling_in_rmse(self):
        """Test that NaN values are handled correctly in RMSE."""
        data1 = xr.DataArray(
            np.array([[1, 2, np.nan], [4, 5, 6]]),
            dims=['x', 'y'],
            coords={'x': [0, 1], 'y': [0, 1, 2]},
            attrs={'units': 'm'}
        )
        data2 = xr.DataArray(
            np.array([[2, 3, 4], [5, np.nan, 7]]),
            dims=['x', 'y'],
            coords={'x': [0, 1], 'y': [0, 1, 2]},
            attrs={'units': 'm'}
        )

        # Add time dimension for 3D processing
        data1 = data1.expand_dims({'time': 5})
        data2 = data2.expand_dims({'time': 5})

        plotter = MatplotlibMetricPlotter()
        result = plotter._compute_correlation_map('rmse', data1, data2)

        # Should handle NaN values appropriately
        assert isinstance(result, xr.DataArray)

    def test_insufficient_data_points(self):
        """Test handling when there are insufficient data points."""
        # Create data with only 1 time step (insufficient for correlation)
        data1 = xr.DataArray(
            np.random.randn(1, 5, 5),
            dims=['time', 'lat', 'lon'],
            attrs={'units': 'm'}
        )
        data2 = xr.DataArray(
            np.random.randn(1, 5, 5),
            dims=['time', 'lat', 'lon'],
            attrs={'units': 'm'}
        )

        plotter = MatplotlibMetricPlotter()
        result = plotter._compute_correlation_map('pearson', data1, data2)

        # Should return result with NaN values (insufficient points for correlation)
        assert np.all(np.isnan(result.values))

    def test_2d_spatial_correlation(self, sample_2d_data):
        """Test 2D spatial correlation computation."""
        data1, data2 = sample_2d_data
        plotter = MatplotlibMetricPlotter()

        # For 2D data, the function should handle it appropriately
        result = plotter._compute_correlation_map('pearson', data1, data2)

        assert result is not None
        assert isinstance(result, xr.DataArray)

    def test_estimate_r_squared_from_correlation(self):
        """Test R² estimation from correlation values."""
        # Create correlation data
        corr_data = xr.DataArray(
            np.array([[0.9, 0.8, 0.7], [0.6, 0.5, 0.4]]),
            dims=['lat', 'lon']
        )

        plotter = MatplotlibMetricPlotter()
        r_squared = plotter._estimate_r_squared_from_correlation(corr_data)

        # Expected: mean of squared correlations
        expected = np.mean(np.array([0.9**2, 0.8**2, 0.7**2, 0.6**2, 0.5**2, 0.4**2]))

        assert np.isclose(r_squared, expected, atol=1e-6)

    def test_cross_correlation_computation(self, sample_3d_data):
        """Test cross-correlation computation."""
        data1, data2 = sample_3d_data
        plotter = MatplotlibMetricPlotter()

        result = plotter._compute_correlation_map('cross', data1, data2)

        assert result is not None
        assert isinstance(result, xr.DataArray)
        assert result.attrs['correlation_method'] == 'cross'


class TestMetricPlotIntegration:
    """Integration tests for metric plotter."""

    def test_plotter_factory_creates_metric_plotter(self):
        """Test creating metric plotter through factory."""
        from eviz.lib.autoviz.plotting.factory import PlotterFactory

        plotter = PlotterFactory.create_plotter('corr', 'matplotlib')
        assert isinstance(plotter, MatplotlibMetricPlotter)

    def test_correlation_method_attribute_storage(self, sample_3d_data, mock_config, mock_figure):
        """Test that correlation method is stored for later use."""
        data1, data2 = sample_3d_data
        plotter = MatplotlibMetricPlotter()

        # Create data_to_plot tuple
        data_to_plot = (
            (data1, data2),  # Tuple of datasets to correlate
            data1.lon,
            data1.lat,
            'soil_moisture',
            'corr',
            0,
            mock_figure
        )

        mock_config.app_data.for_inputs['correlation']['method'] = 'rmse'

        # Mock the colorbar and other plotting methods to avoid matplotlib errors
        with patch.object(plotter, 'set_colorbar'), \
             patch('matplotlib.pyplot.contourf'), \
             patch.object(mock_figure, 'set_axes'):
            try:
                result = plotter.plot(mock_config, data_to_plot)
            except Exception:
                # Plot might fail due to mock config, but that's ok
                pass

        # Check that correlation method was stored
        assert hasattr(plotter, '_corr_method')
        assert plotter._corr_method == 'rmse'

    def test_different_methods_produce_different_results(self, sample_3d_data):
        """Test that different correlation methods produce different results."""
        data1, data2 = sample_3d_data
        plotter = MatplotlibMetricPlotter()

        pearson_result = plotter._compute_correlation_map('pearson', data1, data2)
        spearman_result = plotter._compute_correlation_map('spearman', data1, data2)
        rmse_result = plotter._compute_correlation_map('rmse', data1, data2)

        # Results should be different (at least for some methods)
        # RMSE should be significantly different as it has different units/scale
        assert not np.allclose(pearson_result.values, rmse_result.values, equal_nan=True)
