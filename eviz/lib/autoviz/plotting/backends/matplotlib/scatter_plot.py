"""Unified scatter plot plotter for both gridded and categorical data using Matplotlib."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import logging
from matplotlib.ticker import FormatStrFormatter
import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import eviz.lib.autoviz.utils as pu
from .base import MatplotlibBasePlotter


class MatplotlibScatterPlotter(MatplotlibBasePlotter):
    """Matplotlib implementation of scatter plotting for both gridded and categorical data."""

    def __init__(self):
        super().__init__()
        self.fig = None
        self.ax = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def plot(self, config, data_to_plot):
        """Create a scatter plot using Matplotlib.

        Handles two types of data:
        1. Gridded data: (data2d, x, y, field_name, plot_type, findex, fig, [global_vmin, global_vmax])
        2. Categorical data: (data, field_name, plot_type, findex, fig, plot_options, plot_params)

        Args:
            config: Configuration manager
            data_to_plot: Tuple with data and plotting parameters

        Returns:
            The created/updated figure
        """
        # Detect data type based on tuple structure
        if self._is_categorical_data(data_to_plot):
            return self._plot_categorical(config, data_to_plot)
        else:
            return self._plot_gridded(config, data_to_plot)

    def _is_categorical_data(self, data_to_plot):
        """Detect if this is categorical data based on tuple structure.

        Categorical data has:
        - DataFrame as first element
        - field_name as second element (string)
        - 6 or 7 elements total

        Gridded data has:
        - Array/xarray as first element
        - x coordinates as second element (array)
        - 7 or 9 elements total
        """
        if len(data_to_plot) < 6:
            return False

        # Check if first element is a DataFrame
        first_elem = data_to_plot[0]
        if isinstance(first_elem, pd.DataFrame):
            return True

        # Check if second element is coordinates (array) vs field_name (string)
        second_elem = data_to_plot[1]
        if isinstance(second_elem, str):
            # Categorical: (data, field_name, ...)
            return True
        elif isinstance(second_elem, (np.ndarray, list)):
            # Gridded: (data2d, x, y, ...)
            return False

        return False

    def _plot_gridded(self, config, data_to_plot):
        """Create scatter plot for gridded data.

        Args:
            config: Configuration manager
            data_to_plot: Tuple containing (data2d, x, y, field_name, plot_type, findex, fig, [global_vmin, global_vmax])

        Returns:
            The created figure
        """
        # Handle both old 7-element and new 9-element tuples (with global min/max for GIF consistency)
        if len(data_to_plot) == 9:
            data2d, x, y, field_name, plot_type, findex, fig, global_vmin, global_vmax = data_to_plot
        else:
            data2d, x, y, field_name, plot_type, findex, fig = data_to_plot
            global_vmin, global_vmax = None, None

        if data2d is None:
            return fig

        self.source_name = config.source_names[config.ds_index]
        self.units = self.get_units(config,
                                    field_name,
                                    data2d,
                                    findex)
        self.fig = fig
        self.ax_opts = config.ax_opts

        if not config.compare and not config.compare_diff:
            fig.set_axes()

        ax_temp = fig.get_axes()
        axes_shape = fig.subplots

        if axes_shape == (3, 1):
            if self.ax_opts['is_diff_field']:
                self.ax = ax_temp[2]
            else:
                self.ax = ax_temp[config.axindex]
        elif axes_shape == (2, 2):
            if self.ax_opts['is_diff_field']:
                self.ax = ax_temp[2]
                if self.ax_opts['add_extra_field_type']:
                    self.ax = ax_temp[3]
            else:
                self.ax = ax_temp[config.axindex]
        elif axes_shape == (1, 2) or axes_shape == (1, 3):
            if isinstance(ax_temp, list):
                self.ax = ax_temp[config.axindex]
            else:
                self.ax = ax_temp
        else:
            self.ax = ax_temp[0]

        if x is None or y is None:
            return fig

        self.ax_opts = fig.update_ax_opts(field_name, self.ax, 'sc', level=0)
        self.plot_text(config, field_name, 'sc', level=0)

        self._plot_gridded_scatter_data(config, fig, x, y, data2d, field_name, findex)

        # Add shared colorbar if enabled
        if config.compare and config.shared_cbar:
            self.add_shared_colorbar(fig, config._filled_contours, field_name, config)

        return fig

    def _plot_gridded_scatter_data(self, config, fig, x, y, data2d, field_name, findex):
        """Create a scatter plot for gridded data using SPECS data.

        Args:
            config: Configuration with data source and plotting options
            fig: Matplotlib figure object
            x (array-like): X coordinates for scatter points
            y (array-like): Y coordinates for scatter points
            data2d (xarray.DataArray or array-like): Data values for coloring
            field_name (str): The field being plotted
            findex (int): Index of this field in the comparison sequence
        """
        ax = self.ax
        ax_opts = self.ax_opts
        with mpl.rc_context(rc=ax_opts.get('rc_params', {})):
            if 'fill_value' in config.spec_data[field_name]['scplot']:
                fill_value = config.spec_data[field_name]['scplot']['fill_value']
                data2d = data2d.where(data2d != fill_value, np.nan)

            # Check if we're using Cartopy and if the axis is a GeoAxes
            is_cartopy_axis = False
            try:
                is_cartopy_axis = isinstance(ax, GeoAxes)
            except ImportError:
                pass

            data_transform = ccrs.PlateCarree()

            vmin, vmax = None, None
            if config.compare or not config.compare_diff:
                # Check if we've stored limits for this field in the config
                if not hasattr(config, '_comparison_cbar_limits'):
                    config._comparison_cbar_limits = {}

                if field_name in config._comparison_cbar_limits:
                    vmin, vmax = config._comparison_cbar_limits[field_name]

            if self.fig.use_cartopy and is_cartopy_axis:
                # TODO: Make the following an option:
                ax.stock_img()
                scat = ax.scatter(x, y, c=data2d, cmap=ax_opts['use_cmap'], s=5,
                                transform=data_transform)
                if 'extent' in ax_opts:
                    self._set_cartopy_ticks_alt(ax, ax_opts['extent'])
                else:
                    self.set_cartopy_ticks(ax, [-180, 180, -90, 90])
            else:
                scat = ax.scatter(x, y, c=data2d, cmap=ax_opts['use_cmap'], s=2)

            if scat is None:
                self.set_const_colorbar(scat, fig, ax)
            else:
                # Store colorbar limits for the first plot in a comparison
                if (config.compare or not config.compare_diff) and config.axindex == 0:
                    # Get the limits used in the plot
                    vmin, vmax = scat.get_clim()
                    config._comparison_cbar_limits[field_name] = (vmin, vmax)

                # Suppress individual colorbars if shared_bar is enabled
                if config.shared_cbar:
                    ax_opts['suppress_colorbar'] = True

                self.set_colorbar(config, scat, fig, ax, findex, field_name, data2d)
                if ax_opts.get('line_contours', False):
                    if fig.use_cartopy and is_cartopy_axis:
                        self.line_contours(fig, ax, x, y, data2d, transform=data_transform)
                    else:
                        self.line_contours(fig, ax, x, y, data2d)

            if config.compare_diff:
                name = field_name
                if 'name' in config.spec_data[field_name]:
                    name = config.spec_data[field_name]['name']

                fig.suptitle_eviz(name,
                                fontweight='bold',
                                fontstyle='italic',
                                fontsize=self._image_font_size(fig.subplots))

            elif config.compare:
                fig.suptitle_eviz(text=field_name,
                                fontweight='bold',
                                fontstyle='italic',
                                fontsize=self._image_font_size(fig.subplots))

                if config.add_logo:
                    pu.add_logo_ax(fig, desired_width_ratio=0.05)

            # Collect filled contour objects for shared colorbar
            if not hasattr(config, '_filled_contours'):
                config._filled_contours = []
            config._filled_contours.append(scat)

    def _plot_categorical(self, config, data_to_plot):
        """Create scatter plot for categorical/CSV data.

        Args:
            config: Configuration manager
            data_to_plot: Tuple containing (data, field_name, plot_type, findex, fig, plot_options, plot_params)

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

                # Create axes on the EViz figure without projection
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

        self._plot_categorical_scatter_data(config, data, field_name, plot_options, plot_params)

        return fig

    def _plot_categorical_scatter_data(self, config, data, field_name, plot_options, plot_params):
        """Create the actual scatter plot for categorical data.

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
                            marker=plot_options.get('marker', 'o'),
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
                        marker=plot_options.get('marker', 'o'),
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
