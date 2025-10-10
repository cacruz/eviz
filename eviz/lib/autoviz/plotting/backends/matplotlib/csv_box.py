"""Box plot plotter for categorical/CSV data using Matplotlib."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import logging
from .base import MatplotlibBasePlotter


class MatplotlibCSVBoxPlotter(MatplotlibBasePlotter):
    """Matplotlib implementation of box plot for categorical/CSV data."""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

    def plot(self, config, data_to_plot):
        """Create a box plot using Matplotlib.

        Args:
            config: Configuration manager
            data_to_plot: Tuple containing (data, field_name, plot_type, findex, fig, plot_options, plot_params)
                - data: pandas DataFrame with the data to plot
                - field_name: Name of the field/column being plotted
                - plot_type: 'box'
                - findex: File index
                - fig: Figure object
                - plot_options: Dict of plot-specific options (color, showmeans, etc.)
                - plot_params: Dict of plot parameters (y, by for categorical data)

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

        self._plot_box_data(config, data, field_name, plot_options, plot_params)

        return fig

    def _plot_box_data(self, config, data, field_name, plot_options, plot_params):
        """Create the actual box plot.

        Args:
            config: Configuration manager
            data: pandas DataFrame
            field_name: Name of the field being plotted
            plot_options: Dictionary of plotting options
            plot_params: Dictionary of plot parameters (y, by for categorical data)
        """
        ax = self.ax

        with mpl.rc_context(rc=self.ax_opts.get('rc_params', {})):
            # Handle categorical data with plot_params (y, by)
            if plot_params and 'y' in plot_params:
                y_col = plot_params['y']
                by_col = plot_params.get('by', None)

                if not isinstance(data, pd.DataFrame):
                    self.logger.error("Box plot requires DataFrame")
                    return

                if y_col not in data.columns:
                    self.logger.error(f"Column {y_col} not found in DataFrame")
                    return

                if by_col:
                    # Grouped box plot
                    if by_col not in data.columns:
                        self.logger.error(f"Column {by_col} not found in DataFrame")
                        return

                    # Prepare data
                    categories = data[by_col].unique()
                    box_data = [data[data[by_col] == cat][y_col].dropna().values for cat in categories]

                    bp = ax.boxplot(
                        box_data,
                        labels=[str(cat) for cat in categories],
                        patch_artist=True,
                        showmeans=plot_options.get('showmeans', False),
                        meanline=plot_options.get('meanline', False),
                        notch=plot_options.get('notch', False),
                        vert=plot_options.get('vert', True)
                    )

                    # Color the boxes (make optional?)
                    box_color = plot_options.get('color', 'lightblue')
                    for patch in bp['boxes']:
                        patch.set_facecolor(box_color)
                        patch.set_alpha(plot_options.get('alpha', 0.7))

                    xlabel = by_col
                    ylabel = y_col
                else:
                    # Single box plot
                    values = data[y_col].dropna().values
                    bp = ax.boxplot(
                        [values],
                        labels=[y_col],
                        patch_artist=True,
                        showmeans=plot_options.get('showmeans', False),
                        meanline=plot_options.get('meanline', False),
                        notch=plot_options.get('notch', False),
                        vert=plot_options.get('vert', True)
                    )

                    # Color the box
                    box_color = plot_options.get('color', 'lightblue')
                    for patch in bp['boxes']:
                        patch.set_facecolor(box_color)
                        patch.set_alpha(plot_options.get('alpha', 0.7))

                    xlabel = 'Variable'
                    ylabel = y_col
            else:
                self.logger.error("Box plot requires 'y' parameter in plot_params")
                return

            ax.set_xlabel(xlabel, fontsize=plot_options.get('xlabel_fontsize', 10))
            ax.set_ylabel(ylabel, fontsize=plot_options.get('ylabel_fontsize', 10))

            if by_col:
                title = plot_options.get('title', f'{ylabel} by {xlabel}')
                ax.set_title(title, fontsize=plot_options.get('title_fontsize', 12))

            if plot_options.get('grid', True):
                ax.grid(axis='y', alpha=0.3, linestyle='--')

            # Rotate x-axis labels if requested
            if plot_options.get('rotate_labels', False):
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

            num_boxes = len(box_data) if by_col else 1
            self.logger.info(f"Created box plot for {field_name} with {num_boxes} box(es)")
