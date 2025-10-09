"""Scatter plot plotter for categorical/CSV data using Matplotlib."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import logging
from .base import MatplotlibBasePlotter


class MatplotlibCSVScatterPlotter(MatplotlibBasePlotter):
    """Matplotlib implementation of scatter plot for categorical/CSV data."""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

    def plot(self, config, data_to_plot):
        """Create a scatter plot using Matplotlib.

        Args:
            config: Configuration manager
            data_to_plot: Tuple containing (data, field_name, plot_type, findex, fig, plot_options, plot_params)
                - data: pandas DataFrame with the data to plot
                - field_name: Name of the field/column being plotted
                - plot_type: 'scatter'
                - findex: File index
                - fig: Figure object
                - plot_options: Dict of plot-specific options (color, size, etc.)
                - plot_params: Dict of plot parameters (x, y, color for categorical data)

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

        # Set up axes - for categorical scatter plots, use regular axes (no map projection)
        if not config.compare and not config.compare_diff:
            if fig.get_axes() is None or len(fig.get_axes()) == 0:
                # Temporarily disable projection for categorical plots
                original_ax_opts = config.ax_opts.copy() if hasattr(config, 'ax_opts') else {}
                if hasattr(config, 'ax_opts'):
                    config.ax_opts['projection'] = None

                # Create axes on the EViz figure without projection (default for scatter)
                self.ax = fig.figure.add_subplot(111)

                # Restore original ax_opts
                if hasattr(config, 'ax_opts'):
                    config.ax_opts = original_ax_opts
            else:
                ax_temp = fig.get_axes()
                if isinstance(ax_temp, list) and len(ax_temp) > 0:
                    self.ax = ax_temp[0]
                else:
                    self.ax = ax_temp
        else:
            ax_temp = fig.get_axes()
            if isinstance(ax_temp, list) and len(ax_temp) > 0:
                self.ax = ax_temp[0]
            else:
                self.ax = ax_temp

        self._plot_scatter_data(config, data, field_name, plot_options, plot_params)

        return fig

    def _plot_scatter_data(self, config, data, field_name, plot_options, plot_params):
        """Create the actual scatter plot.

        Args:
            config: Configuration manager
            data: pandas DataFrame
            field_name: Name of the field being plotted
            plot_options: Dictionary of plotting options
            plot_params: Dictionary of plot parameters (x, y, color for categorical data)
        """
        ax = self.ax

        with mpl.rc_context(rc=self.ax_opts.get('rc_params', {})):
            # Handle categorical data with plot_params (x, y, color)
            if plot_params and 'x' in plot_params and 'y' in plot_params:
                x_col = plot_params['x']
                y_col = plot_params['y']
                color_col = plot_params.get('color', None)

                if not isinstance(data, pd.DataFrame):
                    self.logger.error("Scatter plot requires DataFrame")
                    return

                if x_col not in data.columns or y_col not in data.columns:
                    self.logger.error(f"Columns {x_col} or {y_col} not found in DataFrame")
                    return

                # Drop rows with NaN in the columns we need
                columns_to_check = [x_col, y_col]
                if color_col and color_col in data.columns:
                    columns_to_check.append(color_col)

                data_clean = data.dropna(subset=columns_to_check)
                if len(data_clean) == 0:
                    self.logger.error(f"No valid data after removing NaN values")
                    return

                if len(data_clean) < len(data):
                    self.logger.info(f"Dropped {len(data) - len(data_clean)} rows with NaN values")

                x_values = data_clean[x_col].values
                y_values = data_clean[y_col].values
                xlabel = x_col
                ylabel = y_col

                # Handle color column
                if color_col and color_col in data.columns:
                    # Categorical color mapping
                    categories = data_clean[color_col].unique()
                    colors = plt.cm.get_cmap(plot_options.get('cmap', 'viridis'))
                    color_map = {cat: colors(i / len(categories)) for i, cat in enumerate(categories)}
                    c_values = [color_map[val] for val in data_clean[color_col]]

                    # Create scatter plot with categorical colors
                    for category in categories:
                        mask = data_clean[color_col] == category
                        ax.scatter(
                            x_values[mask],
                            y_values[mask],
                            c=[color_map[category]],
                            s=plot_options.get('s', 50),
                            alpha=plot_options.get('alpha', 0.7),
                            edgecolors=plot_options.get('edgecolors', 'black'),
                            linewidths=plot_options.get('linewidths', 0.5),
                            label=str(category)
                        )
                    ax.legend(title=color_col, loc=plot_options.get('legend_loc', 'best'))
                else:
                    # Single color scatter plot
                    color = plot_options.get('color', 'steelblue')
                    ax.scatter(
                        x_values,
                        y_values,
                        c=color,
                        s=plot_options.get('s', 50),
                        alpha=plot_options.get('alpha', 0.7),
                        edgecolors=plot_options.get('edgecolors', 'black'),
                        linewidths=plot_options.get('linewidths', 0.5)
                    )
            else:
                self.logger.error("Scatter plot requires 'x' and 'y' parameters in plot_params")
                return

            ax.set_xlabel(xlabel, fontsize=plot_options.get('xlabel_fontsize', 10))
            ax.set_ylabel(ylabel, fontsize=plot_options.get('ylabel_fontsize', 10))

            title = plot_options.get('title', f'{ylabel} vs {xlabel}')
            ax.set_title(title, fontsize=plot_options.get('title_fontsize', 12))

            if plot_options.get('grid', True):
                ax.grid(alpha=0.3, linestyle='--')

            if 'xlim' in plot_options:
                ax.set_xlim(plot_options['xlim'])
            if 'ylim' in plot_options:
                ax.set_ylim(plot_options['ylim'])

            if plot_options.get('hide_top_spine', False):
                ax.spines['top'].set_visible(False)
            if plot_options.get('hide_right_spine', False):
                ax.spines['right'].set_visible(False)
            if plot_options.get('hide_bottom_spine', False):
                ax.spines['bottom'].set_visible(False)
            if plot_options.get('hide_left_spine', False):
                ax.spines['left'].set_visible(False)

            self.logger.info(f"Created scatter plot for {field_name} with {len(x_values)} points")
