import matplotlib as mpl
import numpy as np
import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import eviz.lib.autoviz.utils as pu

from .base import MatplotlibBasePlotter


class MatplotlibXYPlotter(MatplotlibBasePlotter):
    """Matplotlib implementation of XY plotting."""
    def __init__(self):
        super().__init__()
        self.fig = None
        self.ax = None
            
    def plot(self, config, data_to_plot):
        """Create an XY plot using Matplotlib.
        
        Args:
            config: Configuration manager
            data_to_plot: Tuple containing (data2d, x, y, field_name, plot_type, findex, fig)
        
        Returns:
            The created figure
        """
        # TODO: remove field_name from data_to_plot tuple (get from data2d.name)
        data2d, x, y, field_name, plot_type, findex, fig = data_to_plot
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

        self.ax_opts = fig.update_ax_opts(field_name, self.ax, 'xy', level=config.level)
        self.plot_text(config, field_name=field_name, pid='xy', level=config.level, data=data2d)
        self._plot_xy_data(config, data2d, x, y, field_name, fig, plot_type, findex)
        
        # Add shared colorbar if enabled
        if config.compare and config.shared_cbar:
            self.add_shared_colorbar(fig, config._filled_contours, field_name, config)
        
        return fig

    def _plot_xy_data(self, config, data2d, x, y, field_name, fig, plot_type, findex):
        """Helper function to plot XY data on a single axes."""
        ax = self.ax
        ax_opts = self.ax_opts
        with mpl.rc_context(rc=ax_opts.get('rc_params', {})):
            if 'fill_value' in config.spec_data[field_name]['xyplot']:
                fill_value = config.spec_data[field_name]['xyplot']['fill_value']
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

            # Ensure contour levels are created based on vmin and vmax
            self._create_clevs(field_name, data2d, vmin, vmax)

            if fig.use_cartopy and is_cartopy_axis:
                cfilled = self.filled_contours(config, field_name, ax, x, y, data2d, 
                                            vmin=vmin, vmax=vmax, transform=data_transform)
                if 'extent' in ax_opts:
                    self.set_cartopy_ticks(ax, ax_opts['extent'])
                else:
                    self.set_cartopy_ticks(ax, [-180, 180, -90, 90])
            else:
                cfilled = self.filled_contours(config, field_name, ax, x, y, data2d,
                                            vmin=vmin, vmax=vmax)

            if cfilled is None:
                self.set_const_colorbar(cfilled, fig, ax)
            else:
                # Store colorbar limits for the first plot in a comparison
                if (config.compare or not config.compare_diff) and config.axindex == 0:
                    vmin, vmax = cfilled.get_clim()
                    config._comparison_cbar_limits[field_name] = (vmin, vmax)
                    self.logger.debug(f"Setting comparison colorbar limits for {field_name}: {vmin} to {vmax}")
                
                # Suppress individual colorbars if shared_bar is enabled
                if config.shared_cbar:
                    ax_opts['suppress_colorbar'] = True
                    self.logger.debug(f"Suppressing individual colorbar for {field_name} (axindex={config.axindex})")
                else:
                    self.cbar = self.set_colorbar(config, cfilled, fig, ax, findex, field_name, data2d)

                if ax_opts.get('line_contours', False):
                    if fig.use_cartopy and is_cartopy_axis:
                        self.line_contours(fig, ax, x, y, data2d, transform=data_transform)
                    else:
                        self.line_contours(fig, ax, x, y, data2d)

            long_name = self.get_long_name(config, data2d, findex)
            if config.compare_diff:
                level_text = None
                if ax_opts.get('zave', False):
                    level_text = ' (Column Mean)'
                elif ax_opts.get('zsum', False):
                    level_text = ' (Total Column)'
                else:
                    if str(config.level) == '0':
                        level_text = ''
                    else:
                        if config.level is not None:
                            if config.level > 10000:
                                level_text = '@ ' + str(config.level) + ' Pa'
                            else:
                                level_text = '@ ' + str(config.level) + ' mb'

                if level_text and long_name:
                    title_str = long_name + level_text
                else:
                    title_str = data2d.name + level_text

                fig.suptitle_eviz(title_str, 
                                fontweight='bold',
                                fontstyle='italic',
                                fontsize=self._image_font_size(fig.subplots))
            
            elif config.compare:
                title_str = data2d.name
                if long_name:
                    title_str = long_name

                fig.suptitle_eviz(text=title_str, 
                                fontweight='bold',
                                fontstyle='italic',
                                fontsize=self._image_font_size(fig.subplots))

            if config.add_logo:
                pu.add_logo_ax(fig, desired_width_ratio=0.04)

            # Collect filled contour objects for shared colorbar
            if not hasattr(config, '_filled_contours'):
                config._filled_contours = []
            config._filled_contours.append(cfilled)
