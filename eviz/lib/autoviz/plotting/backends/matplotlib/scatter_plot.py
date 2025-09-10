import matplotlib as mpl
import numpy as np
from matplotlib.ticker import FormatStrFormatter
import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import eviz.lib.autoviz.utils as pu
from .base import MatplotlibBasePlotter


class MatplotlibScatterPlotter(MatplotlibBasePlotter):
    """Matplotlib implementation of scatter plotting."""
    def __init__(self):
        super().__init__()
        self.fig = None
        self.ax = None
    
    def plot(self, config, data_to_plot):
        """Create a scatter plot using Matplotlib.
        
        Args:
            config: Configuration manager
            data_to_plot: Tuple containing (x, y, z_data, field_name, plot_type, findex, fig)
                where z_data is optional and can be used for coloring points
        
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
        
        self._plot_scatter_data(config, fig, x, y, data2d, field_name, findex)
        
        # Add shared colorbar if enabled
        if config.compare and config.shared_cbar:
            self.add_shared_colorbar(fig, config._filled_contours, field_name, config)
        
        return fig

    def _plot_scatter_data(self, config, fig, x, y, data2d, field_name, findex):
        """Create a single scatter plot using SPECS data.

        Parameters:
            config (Config): Configuration with data source and plotting options.
            fig (matplotlib figure): The figure object.
            x, y (array-like): Coordinates for scatter points.
            data2d (xarray or array-like): Data values for coloring.
            field_name (str): The field being plotted.
            findex (int): Index of this field in the comparison sequence.
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
