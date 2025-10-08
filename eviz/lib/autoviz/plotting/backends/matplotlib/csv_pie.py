"""Pie chart plotter for CSV data using Matplotlib."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import logging
from .base import MatplotlibBasePlotter


class MatplotlibCSVPiePlotter(MatplotlibBasePlotter):
    """Matplotlib implementation of pie chart plotting for CSV data."""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

    def plot(self, config, data_to_plot):
        """Create a pie chart using Matplotlib.

        Args:
            config: Configuration manager
            data_to_plot: Tuple containing (data, field_name, plot_type, findex, fig, plot_options, plot_params)
                - data: pandas DataFrame or Series with the data to plot
                - field_name: Name of the field/column being plotted
                - plot_type: 'pie'
                - findex: File index
                - fig: Figure object
                - plot_options: Dict of plot-specific options (colors, explode, etc.)
                - plot_params: Dict of plot parameters (labels, values for categorical data)

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

        # Create the pie chart
        self._plot_pie_data(config, data, field_name, plot_options, plot_params)

        return fig

    def _plot_pie_data(self, config, data, field_name, plot_options, plot_params):
        """Create the actual pie chart.

        Args:
            config: Configuration manager
            data: pandas DataFrame or Series
            field_name: Name of the field being plotted
            plot_options: Dictionary of plotting options
            plot_params: Dictionary of plot parameters (labels, values for categorical data)
        """
        ax = self.ax

        with mpl.rc_context(rc=self.ax_opts.get('rc_params', {})):
            # Handle categorical data with plot_params (labels, values)
            if plot_params and 'labels' in plot_params and 'values' in plot_params:
                labels_col = plot_params['labels']
                values_col = plot_params['values']

                if isinstance(data, pd.DataFrame):
                    if labels_col not in data.columns or values_col not in data.columns:
                        self.logger.error(f"Columns {labels_col} or {values_col} not found in DataFrame")
                        return

                    # Group by labels column and sum values
                    grouped = data.groupby(labels_col)[values_col].sum()
                    labels = grouped.index.astype(str).values
                    values = grouped.values
                else:
                    self.logger.error("plot_params with 'labels' and 'values' requires DataFrame")
                    return

            elif isinstance(data, pd.Series):
                # Simple series - use index as labels
                labels = data.index.astype(str)
                values = data.values
            elif isinstance(data, pd.DataFrame):
                # DataFrame - check if field_name is a column
                if field_name in data.columns:
                    values = data[field_name].values
                    # Try to find an appropriate label column (first column or index)
                    if len(data.columns) > 1:
                        # Use first column that's not the field being plotted
                        label_col = [col for col in data.columns if col != field_name][0]
                        labels = data[label_col].astype(str).values
                    else:
                        labels = data.index.astype(str)
                else:
                    self.logger.error(f"Field {field_name} not found in DataFrame columns")
                    return
            else:
                self.logger.error(f"Unsupported data type: {type(data)}")
                return

            # Filter out zero or negative values (can't be in pie chart)
            valid_mask = values > 0
            if not np.any(valid_mask):
                self.logger.warning(f"No positive values found for {field_name}")
                ax.text(0.5, 0.5, 'No positive values',
                       ha='center', va='center', transform=ax.transAxes)
                return

            values = values[valid_mask]
            labels = labels[valid_mask]

            # Extract plot options with defaults
            colors = plot_options.get('colors', None)
            explode = plot_options.get('explode', None)
            autopct = plot_options.get('autopct', '%1.1f%%')
            startangle = plot_options.get('startangle', 0)
            shadow = plot_options.get('shadow', False)
            labeldistance = plot_options.get('labeldistance', 1.1)
            pctdistance = plot_options.get('pctdistance', 0.6)
            counterclock = plot_options.get('counterclock', False)

            # Validate explode parameter
            if explode is not None:
                if len(explode) != len(values):
                    self.logger.warning(
                        f"Explode length ({len(explode)}) doesn't match data length ({len(values)}). Ignoring explode."
                    )
                    explode = None

            # Create pie chart
            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                colors=colors,
                explode=explode,
                autopct=autopct,
                startangle=startangle,
                shadow=shadow,
                labeldistance=labeldistance,
                pctdistance=pctdistance,
                counterclock=counterclock
            )

            # Customize text properties
            label_fontsize = plot_options.get('label_fontsize', 10)
            pct_fontsize = plot_options.get('pct_fontsize', 9)

            for text in texts:
                text.set_fontsize(label_fontsize)

            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(pct_fontsize)
                autotext.set_weight('bold')

            # Equal aspect ratio ensures that pie is drawn as a circle
            ax.axis('equal')

            # Set title
            title = plot_options.get('title', f'{field_name} - Pie Chart')
            ax.set_title(title, fontsize=plot_options.get('title_fontsize', 12))

            # Add legend if requested
            if plot_options.get('legend', False):
                legend_loc = plot_options.get('legend_loc', 'best')
                ax.legend(wedges, labels, loc=legend_loc, fontsize=8)

            self.logger.info(f"Created pie chart for {field_name} with {len(values)} slices")
