"""Bar chart plotter for CSV data using Matplotlib."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import logging
from .base import MatplotlibBasePlotter


class MatplotlibCSVBarPlotter(MatplotlibBasePlotter):
    """Matplotlib implementation of bar chart plotting for CSV data."""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

    def plot(self, config, data_to_plot):
        """Create a bar chart using Matplotlib.

        Args:
            config: Configuration manager
            data_to_plot: Tuple containing (data, field_name, plot_type, findex, fig, plot_options)
                - data: pandas DataFrame or Series with the data to plot
                - field_name: Name of the field/column being plotted
                - plot_type: 'bar'
                - findex: File index
                - fig: Figure object
                - plot_options: Dict of plot-specific options (color, width, etc.)

        Returns:
            The created/updated figure
        """
        # Unpack data_to_plot
        if len(data_to_plot) == 6:
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

        # Create the bar chart
        self._plot_bar_data(config, data, field_name, plot_options)

        return fig

    def _plot_bar_data(self, config, data, field_name, plot_options):
        """Create the actual bar chart.

        Args:
            config: Configuration manager
            data: pandas DataFrame or Series
            field_name: Name of the field being plotted
            plot_options: Dictionary of plotting options
        """
        ax = self.ax

        # Extract plot options with defaults
        color = plot_options.get('color', 'steelblue')
        width = plot_options.get('width', 0.8)
        alpha = plot_options.get('alpha', 1.0)
        edgecolor = plot_options.get('edgecolor', 'black')
        linewidth = plot_options.get('linewidth', 0.5)
        orientation = plot_options.get('orientation', 'vertical')  # 'vertical' or 'horizontal'

        with mpl.rc_context(rc=self.ax_opts.get('rc_params', {})):
            if isinstance(data, pd.Series):
                # Simple series - use index as x-axis labels
                x_labels = data.index
                y_values = data.values
            elif isinstance(data, pd.DataFrame):
                # DataFrame - check if field_name is a column
                if field_name in data.columns:
                    y_values = data[field_name].values
                    # Try to find an appropriate x-axis (first column or index)
                    if len(data.columns) > 1:
                        # Use first column that's not the field being plotted
                        x_col = [col for col in data.columns if col != field_name][0]
                        x_labels = data[x_col].values
                    else:
                        x_labels = data.index
                else:
                    self.logger.error(f"Field {field_name} not found in DataFrame columns")
                    return
            else:
                self.logger.error(f"Unsupported data type: {type(data)}")
                return

            # Create x positions
            x_pos = np.arange(len(x_labels))

            # Create bar chart
            if orientation == 'horizontal':
                bars = ax.barh(
                    x_pos,
                    y_values,
                    height=width,
                    color=color,
                    alpha=alpha,
                    edgecolor=edgecolor,
                    linewidth=linewidth
                )
                ax.set_yticks(x_pos)
                ax.set_yticklabels(x_labels, rotation=0)
                ax.set_xlabel(field_name)
            else:  # vertical (default)
                bars = ax.bar(
                    x_pos,
                    y_values,
                    width=width,
                    color=color,
                    alpha=alpha,
                    edgecolor=edgecolor,
                    linewidth=linewidth
                )
                ax.set_xticks(x_pos)
                ax.set_xticklabels(x_labels, rotation=plot_options.get('rotation', 45), ha='right')
                ax.set_ylabel(field_name)

            # Add value labels on bars if requested
            if plot_options.get('show_values', False):
                label_format = plot_options.get('value_format', '%.1f')
                for i, (bar, value) in enumerate(zip(bars, y_values)):
                    if orientation == 'horizontal':
                        label_x = value
                        label_y = bar.get_y() + bar.get_height() / 2
                        ha, va = 'left', 'center'
                    else:
                        label_x = bar.get_x() + bar.get_width() / 2
                        label_y = value
                        ha, va = 'center', 'bottom'

                    ax.text(label_x, label_y, label_format % value,
                           ha=ha, va=va, fontsize=8)

            # Set title
            title = plot_options.get('title', f'{field_name} - Bar Chart')
            ax.set_title(title, fontsize=plot_options.get('title_fontsize', 12))

            # Add grid if requested
            if plot_options.get('grid', True):
                ax.grid(axis='y' if orientation == 'vertical' else 'x',
                       alpha=0.3, linestyle='--')

            # Set y-limits if specified
            if 'ylim' in plot_options:
                if orientation == 'vertical':
                    ax.set_ylim(plot_options['ylim'])
                else:
                    ax.set_xlim(plot_options['ylim'])

            self.logger.info(f"Created bar chart for {field_name} with {len(x_labels)} bars")
