"""Histogram plotter for CSV data using Matplotlib."""

import matplotlib as mpl
import numpy as np
import pandas as pd
import logging
from .base import MatplotlibBasePlotter


class MatplotlibCSVHistPlotter(MatplotlibBasePlotter):
    """Matplotlib implementation of histogram plotting for CSV data."""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

    def plot(self, config, data_to_plot):
        """Create a histogram using Matplotlib.

        Args:
            config: Configuration manager
            data_to_plot: Tuple containing (data, field_name, plot_type, findex, fig, plot_options, plot_params)
                - data: pandas DataFrame or Series with the data to plot
                - field_name: Name of the field/column being plotted
                - plot_type: 'hist'
                - findex: File index
                - fig: Figure object
                - plot_options: Dict of plot-specific options (bins, color, etc.)
                - plot_params: Dict of plot parameters (x, bins for categorical data)

        Returns:
            The created/updated figure
        """
        # Unpack data_to_plot with backward compatibility
        plot_params = {}
        if len(data_to_plot) >= 7:
            data, field_name, plot_type, findex, fig, plot_options, plot_params = data_to_plot[:7]
        elif len(data_to_plot) == 6:
            data, field_name, plot_type, findex, fig, plot_options = data_to_plot
        else:
            # Fallback for older format
            data, field_name, plot_type, findex, fig = data_to_plot[:5]
            plot_options = data_to_plot[5] if len(data_to_plot) > 5 else {}

        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            self.logger.warning(f"No data available for {field_name}")
            return fig

        self.fig = fig
        self.ax_opts = config.ax_opts if hasattr(config, 'ax_opts') else {}

        # Set up axes
        if not config.compare and not config.compare_diff:
            if fig.get_axes() is None or len(fig.get_axes()) == 0:
                fig.set_axes()

        ax_temp = fig.get_axes()
        if isinstance(ax_temp, list) and len(ax_temp) > 0:
            self.ax = ax_temp[0]
        else:
            self.ax = ax_temp

        self._plot_hist_data(config, data, field_name, plot_options, plot_params)

        return fig

    def _plot_hist_data(self, config, data, field_name, plot_options, plot_params):
        """Create the actual histogram.

        Args:
            config: Configuration manager
            data: pandas DataFrame or Series
            field_name: Name of the field being plotted
            plot_options: Dictionary of plotting options
            plot_params: Dictionary of plot parameters (x for categorical data)
        """
        ax = self.ax

        with mpl.rc_context(rc=self.ax_opts.get('rc_params', {})):
            # Handle categorical data with plot_params
            if plot_params and 'x' in plot_params:
                # For categorical data, use the 'x' parameter as the column name
                x_col = plot_params['x']
                if isinstance(data, pd.DataFrame) and x_col in data.columns:
                    values = data[x_col].values
                    xlabel = x_col
                else:
                    self.logger.error(f"Column {x_col} not found in DataFrame")
                    return
            elif isinstance(data, pd.Series):
                # Simple series - use values directly
                values = data.values
                xlabel = field_name
            elif isinstance(data, pd.DataFrame):
                # DataFrame - check if field_name is a column
                if field_name in data.columns:
                    values = data[field_name].values
                    xlabel = field_name
                else:
                    self.logger.error(f"Field {field_name} not found in DataFrame columns")
                    return
            else:
                self.logger.error(f"Unsupported data type: {type(data)}")
                return

            # Remove NaN values
            values = values[~np.isnan(values)]

            if len(values) == 0:
                self.logger.warning(f"No valid values found for {field_name}")
                ax.text(0.5, 0.5, 'No valid values',
                       ha='center', va='center', transform=ax.transAxes)
                return

            # Extract plot options with defaults
            bins = plot_options.get('bins', 'auto')
            color = plot_options.get('color', 'steelblue')
            alpha = plot_options.get('alpha', 0.7)
            edgecolor = plot_options.get('edgecolor', 'black')
            linewidth = plot_options.get('linewidth', 0.5)
            density = plot_options.get('density', False)
            cumulative = plot_options.get('cumulative', False)
            orientation = plot_options.get('orientation', 'vertical')
            histtype = plot_options.get('histtype', 'bar')  # 'bar', 'barstacked', 'step', 'stepfilled'

            n, bin_edges, patches = ax.hist(
                values,
                bins=bins,
                color=color,
                alpha=alpha,
                edgecolor=edgecolor,
                linewidth=linewidth,
                density=density,
                cumulative=cumulative,
                orientation=orientation,
                histtype=histtype
            )

            # Add statistical lines if requested
            if plot_options.get('show_mean', False):
                mean_val = np.mean(values)
                if orientation == 'vertical':
                    ax.axvline(mean_val, color='red', linestyle='--', linewidth=2,
                              label=f'Mean: {mean_val:.2f}')
                else:
                    ax.axhline(mean_val, color='red', linestyle='--', linewidth=2,
                              label=f'Mean: {mean_val:.2f}')

            if plot_options.get('show_median', False):
                median_val = np.median(values)
                if orientation == 'vertical':
                    ax.axvline(median_val, color='green', linestyle='--', linewidth=2,
                              label=f'Median: {median_val:.2f}')
                else:
                    ax.axhline(median_val, color='green', linestyle='--', linewidth=2,
                              label=f'Median: {median_val:.2f}')

            if plot_options.get('show_std', False):
                mean_val = np.mean(values)
                std_val = np.std(values)
                if orientation == 'vertical':
                    ax.axvline(mean_val - std_val, color='orange', linestyle=':', linewidth=1.5,
                              label=f'±1 Std: {std_val:.2f}')
                    ax.axvline(mean_val + std_val, color='orange', linestyle=':', linewidth=1.5)
                else:
                    ax.axhline(mean_val - std_val, color='orange', linestyle=':', linewidth=1.5,
                              label=f'±1 Std: {std_val:.2f}')
                    ax.axhline(mean_val + std_val, color='orange', linestyle=':', linewidth=1.5)

            if orientation == 'vertical':
                ax.set_xlabel(xlabel, fontsize=10)
                ylabel = 'Density' if density else 'Frequency'
                if cumulative:
                    ylabel = f'Cumulative {ylabel}'
                ax.set_ylabel(ylabel, fontsize=10)
            else:
                ax.set_ylabel(xlabel, fontsize=10)
                xlabel_freq = 'Density' if density else 'Frequency'
                if cumulative:
                    xlabel_freq = f'Cumulative {xlabel_freq}'
                ax.set_xlabel(xlabel_freq, fontsize=10)

            title = plot_options.get('title', f'{xlabel}')
            ax.set_title(title, fontsize=plot_options.get('title_fontsize', 12))

            if plot_options.get('grid', True):
                ax.grid(axis='y' if orientation == 'vertical' else 'x',
                       alpha=0.3, linestyle='--')

            # Add legend if statistical lines were added
            if plot_options.get('show_mean', False) or plot_options.get('show_median', False) or plot_options.get('show_std', False):
                ax.legend(loc=plot_options.get('legend_loc', 'best'), fontsize=8)

            # Add statistics text box if requested
            if plot_options.get('show_stats', False):
                stats_text = f'Count: {len(values)}\n'
                stats_text += f'Mean: {np.mean(values):.2f}\n'
                stats_text += f'Std: {np.std(values):.2f}\n'
                stats_text += f'Min: {np.min(values):.2f}\n'
                stats_text += f'Max: {np.max(values):.2f}'

                # Place text box in upper right corner
                props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
                ax.text(0.95, 0.95, stats_text,
                       transform=ax.transAxes,
                       fontsize=8,
                       verticalalignment='top',
                       horizontalalignment='right',
                       bbox=props)

            # Set x/y limits if specified
            if 'xlim' in plot_options:
                if orientation == 'vertical':
                    ax.set_xlim(plot_options['xlim'])
                else:
                    ax.set_ylim(plot_options['xlim'])

            if 'ylim' in plot_options:
                if orientation == 'vertical':
                    ax.set_ylim(plot_options['ylim'])
                else:
                    ax.set_xlim(plot_options['ylim'])

            self.logger.info(f"Created histogram for {field_name} with {len(bin_edges)-1} bins")
