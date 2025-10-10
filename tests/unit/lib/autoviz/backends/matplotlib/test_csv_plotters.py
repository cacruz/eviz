"""Unit tests for CSV plotters (bar, pie, histogram)."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
import matplotlib.pyplot as plt

from eviz.lib.autoviz.plotting.backends.matplotlib.bar_plot import MatplotlibCSVBarPlotter
from eviz.lib.autoviz.plotting.backends.matplotlib.pie_plot import MatplotlibCSVPiePlotter
from eviz.lib.autoviz.plotting.backends.matplotlib.hist_plot import MatplotlibCSVHistPlotter


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'category': ['A', 'B', 'C', 'D', 'E'],
        'values': [10.5, 20.3, 15.7, 25.1, 18.9],
        'counts': [5, 10, 7, 12, 8]
    })


@pytest.fixture
def sample_series():
    """Create a sample Series for testing."""
    return pd.Series([10, 20, 15, 25, 18], index=['A', 'B', 'C', 'D', 'E'], name='values')


@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    config = MagicMock()
    config.compare = False
    config.compare_diff = False
    config.ax_opts = {}
    return config


@pytest.fixture
def mock_figure():
    """Create a mock figure object."""
    fig = MagicMock()
    fig.get_axes = MagicMock(return_value=[plt.subplot(111)])
    return fig


class TestMatplotlibCSVBarPlotter:
    """Test suite for bar chart plotter."""

    def test_init(self):
        """Test plotter initialization."""
        plotter = MatplotlibCSVBarPlotter()
        assert plotter is not None
        assert hasattr(plotter, 'logger')

    def test_plot_with_dataframe(self, sample_dataframe, mock_config, mock_figure):
        """Test plotting with DataFrame input."""
        plotter = MatplotlibCSVBarPlotter()
        plot_options = {'color': 'blue', 'width': 0.8}

        data_to_plot = (sample_dataframe, 'values', 'bar', 0, mock_figure, plot_options)

        with patch.object(plotter, '_plot_bar_data') as mock_plot:
            result = plotter.plot(mock_config, data_to_plot)
            assert result == mock_figure
            mock_plot.assert_called_once()

    def test_plot_with_series(self, sample_series, mock_config, mock_figure):
        """Test plotting with Series input."""
        plotter = MatplotlibCSVBarPlotter()
        plot_options = {}

        data_to_plot = (sample_series, 'values', 'bar', 0, mock_figure, plot_options)

        with patch.object(plotter, '_plot_bar_data') as mock_plot:
            result = plotter.plot(mock_config, data_to_plot)
            assert result == mock_figure
            mock_plot.assert_called_once()

    def test_plot_with_empty_data(self, mock_config, mock_figure):
        """Test handling of empty DataFrame."""
        plotter = MatplotlibCSVBarPlotter()
        empty_df = pd.DataFrame()

        data_to_plot = (empty_df, 'values', 'bar', 0, mock_figure, {})

        result = plotter.plot(mock_config, data_to_plot)
        assert result == mock_figure

    def test_plot_bar_data_vertical(self, sample_dataframe, mock_config):
        """Test vertical bar chart creation."""
        plotter = MatplotlibCSVBarPlotter()
        plotter.ax = plt.subplot(111)
        plotter.ax_opts = {}

        plot_options = {'orientation': 'vertical', 'color': 'steelblue'}
        plot_params = {}  # No categorical params for this test

        plotter._plot_bar_data(mock_config, sample_dataframe, 'values', plot_options, plot_params)

        # Check that bars were created
        assert len(plotter.ax.patches) > 0
        plt.close('all')

    def test_plot_bar_data_horizontal(self, sample_dataframe, mock_config):
        """Test horizontal bar chart creation."""
        plotter = MatplotlibCSVBarPlotter()
        plotter.ax = plt.subplot(111)
        plotter.ax_opts = {}

        plot_options = {'orientation': 'horizontal', 'color': 'coral'}
        plot_params = {}  # No categorical params for this test

        plotter._plot_bar_data(mock_config, sample_dataframe, 'values', plot_options, plot_params)

        # Check that bars were created
        assert len(plotter.ax.patches) > 0
        plt.close('all')

    def test_plot_bar_data_with_value_labels(self, sample_dataframe, mock_config):
        """Test bar chart with value labels."""
        plotter = MatplotlibCSVBarPlotter()
        plotter.ax = plt.subplot(111)
        plotter.ax_opts = {}

        plot_options = {'show_values': True, 'value_format': '%.1f'}
        plot_params = {}  # No categorical params for this test

        plotter._plot_bar_data(mock_config, sample_dataframe, 'values', plot_options, plot_params)

        # Check that text labels were added
        assert len(plotter.ax.texts) > 0
        plt.close('all')


class TestMatplotlibCSVPiePlotter:
    """Test suite for pie chart plotter."""

    def test_init(self):
        """Test plotter initialization."""
        plotter = MatplotlibCSVPiePlotter()
        assert plotter is not None
        assert hasattr(plotter, 'logger')

    def test_plot_with_dataframe(self, sample_dataframe, mock_config, mock_figure):
        """Test plotting with DataFrame input."""
        plotter = MatplotlibCSVPiePlotter()
        plot_options = {'autopct': '%1.1f%%'}

        data_to_plot = (sample_dataframe, 'values', 'pie', 0, mock_figure, plot_options)

        with patch.object(plotter, '_plot_pie_data') as mock_plot:
            result = plotter.plot(mock_config, data_to_plot)
            assert result == mock_figure
            mock_plot.assert_called_once()

    def test_plot_with_series(self, sample_series, mock_config, mock_figure):
        """Test plotting with Series input."""
        plotter = MatplotlibCSVPiePlotter()
        plot_options = {}

        data_to_plot = (sample_series, 'values', 'pie', 0, mock_figure, plot_options)

        with patch.object(plotter, '_plot_pie_data') as mock_plot:
            result = plotter.plot(mock_config, data_to_plot)
            assert result == mock_figure
            mock_plot.assert_called_once()

    def test_plot_pie_data_basic(self, sample_dataframe, mock_config):
        """Test basic pie chart creation."""
        plotter = MatplotlibCSVPiePlotter()
        plotter.ax = plt.subplot(111)
        plotter.ax_opts = {}

        plot_options = {'autopct': '%1.1f%%', 'startangle': 90}
        plot_params = {}  # No categorical params for this test

        plotter._plot_pie_data(mock_config, sample_dataframe, 'values', plot_options, plot_params)

        # Check that pie chart was created (patches will be wedges)
        assert len(plotter.ax.patches) > 0
        plt.close('all')

    def test_plot_pie_data_with_explode(self, sample_dataframe, mock_config):
        """Test pie chart with exploded slices."""
        plotter = MatplotlibCSVPiePlotter()
        plotter.ax = plt.subplot(111)
        plotter.ax_opts = {}

        plot_options = {
            'explode': [0.1, 0, 0, 0, 0],
            'autopct': '%1.1f%%',
            'shadow': True
        }
        plot_params = {}  # No categorical params for this test

        plotter._plot_pie_data(mock_config, sample_dataframe, 'values', plot_options, plot_params)

        assert len(plotter.ax.patches) > 0
        plt.close('all')

    def test_plot_pie_data_with_legend(self, sample_dataframe, mock_config):
        """Test pie chart with legend."""
        plotter = MatplotlibCSVPiePlotter()
        plotter.ax = plt.subplot(111)
        plotter.ax_opts = {}

        plot_options = {'legend': True, 'legend_loc': 'upper right'}
        plot_params = {}  # No categorical params for this test

        plotter._plot_pie_data(mock_config, sample_dataframe, 'values', plot_options, plot_params)

        # Check that legend was added
        assert plotter.ax.get_legend() is not None
        plt.close('all')

    def test_plot_pie_data_filters_negative(self, mock_config):
        """Test that negative values are filtered out."""
        plotter = MatplotlibCSVPiePlotter()
        plotter.ax = plt.subplot(111)
        plotter.ax_opts = {}

        df_with_negative = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'values': [10, -5, 15]  # One negative value
        })

        plot_options = {}
        plot_params = {}  # No categorical params for this test

        plotter._plot_pie_data(mock_config, df_with_negative, 'values', plot_options, plot_params)

        # Should only have 2 wedges (positive values)
        assert len(plotter.ax.patches) == 2
        plt.close('all')


class TestMatplotlibCSVHistPlotter:
    """Test suite for histogram plotter."""

    def test_init(self):
        """Test plotter initialization."""
        plotter = MatplotlibCSVHistPlotter()
        assert plotter is not None
        assert hasattr(plotter, 'logger')

    def test_plot_with_dataframe(self, sample_dataframe, mock_config, mock_figure):
        """Test plotting with DataFrame input."""
        plotter = MatplotlibCSVHistPlotter()
        plot_options = {'bins': 10, 'color': 'green'}

        data_to_plot = (sample_dataframe, 'values', 'hist', 0, mock_figure, plot_options)

        with patch.object(plotter, '_plot_hist_data') as mock_plot:
            result = plotter.plot(mock_config, data_to_plot)
            assert result == mock_figure
            mock_plot.assert_called_once()

    def test_plot_with_series(self, sample_series, mock_config, mock_figure):
        """Test plotting with Series input."""
        plotter = MatplotlibCSVHistPlotter()
        plot_options = {}

        data_to_plot = (sample_series, 'values', 'hist', 0, mock_figure, plot_options)

        with patch.object(plotter, '_plot_hist_data') as mock_plot:
            result = plotter.plot(mock_config, data_to_plot)
            assert result == mock_figure
            mock_plot.assert_called_once()

    def test_plot_hist_data_basic(self, sample_dataframe, mock_config):
        """Test basic histogram creation."""
        plotter = MatplotlibCSVHistPlotter()
        plotter.ax = plt.subplot(111)
        plotter.ax_opts = {}

        plot_options = {'bins': 5, 'color': 'steelblue'}
        plot_params = {}  # No categorical params for this test

        plotter._plot_hist_data(mock_config, sample_dataframe, 'values', plot_options, plot_params)

        # Check that histogram bars were created
        assert len(plotter.ax.patches) > 0
        plt.close('all')

    def test_plot_hist_data_with_density(self, sample_dataframe, mock_config):
        """Test histogram with density normalization."""
        plotter = MatplotlibCSVHistPlotter()
        plotter.ax = plt.subplot(111)
        plotter.ax_opts = {}

        plot_options = {'bins': 5, 'density': True}
        plot_params = {}  # No categorical params for this test

        plotter._plot_hist_data(mock_config, sample_dataframe, 'values', plot_options, plot_params)

        assert len(plotter.ax.patches) > 0
        plt.close('all')

    def test_plot_hist_data_with_stats_lines(self, sample_dataframe, mock_config):
        """Test histogram with mean, median, and std lines."""
        plotter = MatplotlibCSVHistPlotter()
        plotter.ax = plt.subplot(111)
        plotter.ax_opts = {}

        plot_options = {
            'bins': 5,
            'show_mean': True,
            'show_median': True,
            'show_std': True
        }
        plot_params = {}  # No categorical params for this test

        plotter._plot_hist_data(mock_config, sample_dataframe, 'values', plot_options, plot_params)

        # Check that statistical lines were added (as vertical lines)
        assert len(plotter.ax.lines) > 0
        # Check that legend was added
        assert plotter.ax.get_legend() is not None
        plt.close('all')

    def test_plot_hist_data_with_stats_box(self, sample_dataframe, mock_config):
        """Test histogram with statistics text box."""
        plotter = MatplotlibCSVHistPlotter()
        plotter.ax = plt.subplot(111)
        plotter.ax_opts = {}

        plot_options = {'bins': 5, 'show_stats': True}
        plot_params = {}  # No categorical params for this test

        plotter._plot_hist_data(mock_config, sample_dataframe, 'values', plot_options, plot_params)

        # Check that text annotation was added
        assert len(plotter.ax.texts) > 0
        plt.close('all')

    def test_plot_hist_data_cumulative(self, sample_dataframe, mock_config):
        """Test cumulative histogram."""
        plotter = MatplotlibCSVHistPlotter()
        plotter.ax = plt.subplot(111)
        plotter.ax_opts = {}

        plot_options = {'bins': 5, 'cumulative': True}
        plot_params = {}  # No categorical params for this test

        plotter._plot_hist_data(mock_config, sample_dataframe, 'values', plot_options, plot_params)

        assert len(plotter.ax.patches) > 0
        plt.close('all')

    def test_plot_hist_data_horizontal(self, sample_dataframe, mock_config):
        """Test horizontal histogram."""
        plotter = MatplotlibCSVHistPlotter()
        plotter.ax = plt.subplot(111)
        plotter.ax_opts = {}

        plot_options = {'bins': 5, 'orientation': 'horizontal'}
        plot_params = {}  # No categorical params for this test

        plotter._plot_hist_data(mock_config, sample_dataframe, 'values', plot_options, plot_params)

        assert len(plotter.ax.patches) > 0
        plt.close('all')

    def test_plot_hist_data_different_histtypes(self, sample_dataframe, mock_config):
        """Test different histogram types."""
        for histtype in ['bar', 'step', 'stepfilled']:
            plotter = MatplotlibCSVHistPlotter()
            plotter.ax = plt.subplot(111)
            plotter.ax_opts = {}

            plot_options = {'bins': 5, 'histtype': histtype}
            plot_params = {}  # No categorical params for this test

            plotter._plot_hist_data(mock_config, sample_dataframe, 'values', plot_options, plot_params)

            if histtype == 'bar':
                assert len(plotter.ax.patches) > 0
            plt.close('all')


class TestPlotterIntegration:
    """Integration tests for plotters with PlotterFactory."""

    def test_create_bar_plotter_from_factory(self):
        """Test creating bar plotter through factory."""
        from eviz.lib.autoviz.plotting.factory import PlotterFactory

        plotter = PlotterFactory.create_plotter('bar', 'matplotlib')
        assert isinstance(plotter, MatplotlibCSVBarPlotter)

    def test_create_pie_plotter_from_factory(self):
        """Test creating pie plotter through factory."""
        from eviz.lib.autoviz.plotting.factory import PlotterFactory

        plotter = PlotterFactory.create_plotter('pie', 'matplotlib')
        assert isinstance(plotter, MatplotlibCSVPiePlotter)

    def test_create_hist_plotter_from_factory(self):
        """Test creating histogram plotter through factory."""
        from eviz.lib.autoviz.plotting.factory import PlotterFactory

        plotter = PlotterFactory.create_plotter('hist', 'matplotlib')
        assert isinstance(plotter, MatplotlibCSVHistPlotter)

    def test_factory_raises_for_unknown_plot_type(self):
        """Test that factory raises error for unknown plot types."""
        from eviz.lib.autoviz.plotting.factory import PlotterFactory

        with pytest.raises(ValueError, match="No plotter available"):
            PlotterFactory.create_plotter('unknown_type', 'matplotlib')
