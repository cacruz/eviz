import logging
from typing import Any, Dict, Optional
import matplotlib as mpl
import matplotlib.figure as mfigure
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.gridspec as gridspec
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.ticker import MultipleLocator

import numpy as np

from eviz.lib.autoviz.utils import get_subplot_geometry
import eviz.lib.autoviz.utils as pu


class Figure(mfigure.Figure):
    """Enhanced Figure class inheriting from Matplotlib's Figure with eViz framework customizations.

    Args:
        config_manager (ConfigManager): Representation of the model configuration
        plot_type (str): Type of plot to be created
        nrows (int, optional): Number of subplot rows. Defaults to None
        ncols (int, optional): Number of subplot columns. Defaults to None
        **kwargs: Additional keyword arguments passed to matplotlib.figure.Figure

    See Also:
        matplotlib.figure.Figure
    """
    def __init__(self, config_manager, plot_type, 
        *,
        nrows=None,
        ncols=None,
        **kwargs,
    ):

        self._gridspec = None
        self._panel_dict = {"left": [], "right": [], "bottom": [], "top": []}
        self._subplot_dict = {}  # subplots indexed by number
        self._subplot_counter = 0  # avoid add_subplot() returning an existing subplot
        self._projection = None
        self._subplots = (1, 1)

        # Initialize eViz-specific attributes
        self.config_manager = config_manager
        self.plot_type = plot_type
        self._logger = logging.getLogger(__name__)
        
        self._rindex = 0
        self._ax_opts = {}
        self._frame_params = {}
        
        # If nrows and ncols are provided, use them to set _subplots
        if nrows is not None and ncols is not None:
            self._subplots = (nrows, ncols)
            
        self._use_cartopy = False
        self.gs = None
        self.axes_array = []
        self._refnum = 1

        # Remove nrows and ncols from kwargs to avoid passing them to matplotlib.figure.Figure
        if 'nrows' in kwargs:
            del kwargs['nrows']
        if 'ncols' in kwargs:
            del kwargs['ncols']
            
        super().__init__(**kwargs)

        # Ensure the figure has a canvas
        if not hasattr(self, 'canvas') or self.canvas is None:
            from matplotlib.backends.backend_agg import FigureCanvasAgg
            self.canvas = FigureCanvasAgg(self)
                            
        self._init_frame()

    def _init_frame(self):
        """Set shape and size for figure frames using improved sizing strategy."""
        self._set_compare_diff_subplots()
        
        # Calculate optimal figure size based on content and layout
        figsize = self._calculate_optimal_figsize()
        
        # Store frame parameters with calculated size
        _frame_params = {}
        rindex = 0
        nrows, ncols = self._subplots
        _frame_params[rindex] = [nrows, ncols, figsize[0], figsize[1]]
        
        self._frame_params = _frame_params

    def _set_compare_diff_subplots(self):
        """Set subplots for comparison plots."""
        try:
            # Handle simple side-by-side comparison
            if self.config_manager.compare and not self.config_manager.compare_diff:
                # Get the number of variables to compare from the config
                if hasattr(self.config_manager, 'compare_exp_ids'):
                    num_vars = len(self.config_manager.compare_exp_ids)
                    # TODO: unless panels shape is specified in config
                    self._subplots = (num_vars, 1)
                else:
                    self._subplots = (2, 1)  # Default to side by side layout
                return
                
            # Handle comparison with difference plots
            extra_diff_plot = self.config_manager.extra_diff_plot
            if not self.config_manager.compare_diff:
                extra_diff_plot = False
                
            if self.config_manager.spec_data and extra_diff_plot:
                self._subplots = (2, 2)
            elif self.config_manager.compare_diff:
                self._subplots = (3, 1)
            else:
                self._subplots = (1, 1)  # fallback for single plots
                
        except Exception as e:
            self.logger.warning(f"Error setting subplot layout: {str(e)}, using default")
            self._subplots = (1, 1)

    def set_axes(self) -> "Figure":
        """
        Set figure axes objects based on required subplots.

        Returns:
            self: The Figure object itself.
        """
        if 'tx' in self.plot_type or 'sc' in self.plot_type or 'xy' in self.plot_type:
            self._use_cartopy = True

        self.create_subplot_grid()
        self.create_subplots()

        return self

    def reset_axes(self, ax):
        """Remove all plotted data, colorbars, and titles from either a Matplotlib Axes
        or Cartopy GeoAxes.
        """
        if self is None:
            raise ValueError("Figure is None! It may have been closed or deleted.")

        for self.artist in ax.lines + ax.collections + ax.patches + ax.images:
            self.artist.remove()

        # Cartopy GeoAxes
        if hasattr(ax, "coastlines"):  
            ax.cla()  

        colorbars = [cbar_ax for cbar_ax in self.axes if cbar_ax is not ax]
        for cbar_ax in colorbars:
            if "colorbar" in str(cbar_ax):
                self.delaxes(cbar_ax)  

        ax.set_title("")
        self.canvas.draw_idle()

    def _get_fig_ax(self) -> "Figure":
        """
        Initialize figure and axes objects for all plots based on plot type.

        Returns:
            self: The Figure object itself.
        """
        if "po" in self.plot_type:
            return self

        if 'tx' in self.plot_type or 'sc' in self.plot_type or 'xy' in self.plot_type:
            self._use_cartopy = True

        self.create_subplot_grid()
        self.create_subplots()

        return self
    
    def get_fig_ax(self):
        return self._get_fig_ax()

    def get_axes(self) -> list:
        # Always return a list of axes, even for a single axes
        return self.axes_array

    def create_subplot_grid(self) -> "Figure":
        """Create a grid of subplots with optimized spacing and sizing."""
        # Apply calculated figure size
        if self._frame_params[self._rindex][2] and self._frame_params[self._rindex][3]:
            figsize = (self._frame_params[self._rindex][2], self._frame_params[self._rindex][3])
            self.set_size_inches(figsize)

        # Calculate optimal spacing based on subplot configuration
        spacing_params = self._calculate_subplot_spacing()
        
        # Create GridSpec with calculated spacing
        self.gs = gridspec.GridSpec(
            *self._subplots,
            **spacing_params
        )
            
        return self

    @classmethod
    def create_eviz_figure(cls, config_manager, 
                        plot_type, 
                        field_name=None, nrows=None, ncols=None,
                        figsize=None, **kwargs) -> "Figure":
        """
        Enhanced factory method to create an eViz Figure instance with improved sizing.
        
        Args:
            config_manager (ConfigManager): Configuration manager
            plot_type (str): Type of plot
            field_name (str, optional): Name of the field being plotted
            nrows (int, optional): Number of rows in the subplot grid
            ncols (int, optional): Number of columns in the subplot grid
            figsize (tuple, optional): Explicit figure size (width, height)
            **kwargs: Additional arguments passed to Figure constructor
        
        Returns:
            Figure: An instance of the eViz Figure class with optimized sizing
        """
        if field_name is None:
            field_name = config_manager.current_field_name
        
        # Get plot-specific configuration
        plot_config = cls._get_plot_config(config_manager, field_name, plot_type)
        
        # Determine subplot layout
        layout = cls._determine_subplot_layout(config_manager, field_name, plot_type, nrows, ncols)
        nrows, ncols = layout
        
        # Create figure instance
        fig = cls(config_manager, plot_type, nrows=nrows, ncols=ncols, **kwargs)
        
        # Store field name for sizing calculations
        fig.field_name = field_name
        
        # Initialize axis options with plot configuration
        fig._initialize_ax_opts(plot_config)
        
        # Override figsize if explicitly provided
        if figsize is not None:
            fig._frame_params[0][2] = figsize[0]
            fig._frame_params[0][3] = figsize[1]
        
        return fig

    def set_us_map_layout(self):
        """Adjust figure layout for US maps."""
        # Set a wider figure size
        self.set_size_inches(18, 6)
        
        # Adjust subplot spacing
        self.subplots_adjust(wspace=0.1, right=0.85)
        
        # Set aspect ratio for all axes
        for ax in self.axes_array:
            ax.set_aspect('auto')

    def create_subplots(self):
        """
        Create subplots based on the gridspec (subplot grid) and projection requirements.
        """
        if self.use_cartopy:
            return self._create_subplots_crs()
        else:
            for i in range(self._subplots[0]):
                for j in range(self._subplots[1]):
                    ax = self.add_subplot(self.gs[i, j])
                    self.axes_array.append(ax)
            return self

    def _create_subplots_crs(self) -> "Figure":
        """Create subplots with cartopy projections."""
        # Determine the projection to use
        map_projection = None
        # Check if we have a field_name and can get projection from spec_data
        if hasattr(self, 'field_name') and self.field_name:
            if (self.config_manager.spec_data and
                    self.field_name in self.config_manager.spec_data
            ):
                # Check for projection at the top level of the field spec
                if 'projection' in self.config_manager.spec_data[self.field_name]:
                    projection_name = self.config_manager.spec_data[self.field_name]['projection']
                    map_projection = self._get_projection(projection_name)
                    self._logger.debug(f"Using projection '{projection_name}' for field {self.field_name}")
                # Also check in the plot-type specific section
                elif 'projection' in self.config_manager.spec_data[self.field_name].get(f"{self.plot_type[:2]}plot", {}):
                    projection_name = self.config_manager.spec_data[self.field_name][f"{self.plot_type[:2]}plot"]['projection']
                    map_projection = self._get_projection(projection_name)
                    self._logger.debug(f"Using projection '{projection_name}' for field {self.field_name}")

        # If no projection found from field_name, check ax_opts
        if map_projection is None and 'projection' in self._ax_opts:
            map_projection = self._get_projection(self._ax_opts['projection'])

        # Default to PlateCarree if no projection specified
        if map_projection is None:
            map_projection = self._get_projection()

        for i in range(self._subplots[0]):
            for j in range(self._subplots[1]):
                ax = self.add_subplot(self.gs[i, j], projection=map_projection)
                self.axes_array.append(ax)

        for ax in self.axes_array:
            ax.coastlines()
            ax.add_feature(cfeature.BORDERS, linestyle=':')
            ax.add_feature(cfeature.LAND, edgecolor='black')
            ax.add_feature(cfeature.LAKES, edgecolor='black', color='white', zorder=0)
            ax.add_feature(cfeature.OCEAN, color='white', zorder=0)
            
        return self

    def get_gs_geometry(self):
        if self.gs:
            return self.gs.get_geometry()
        else:
            return None

    def have_multiple_axes(self):
        return self.axes is not None and (self.axes.numRows > 1 or self.axes.numCols > 1)

    def have_nontrivial_grid(self):
        return self.gs.nrows > 1 or self.gs.ncols > 1

    def _set_fig_axes_regional(self, use_cartopy_opt):
        pass

    def savefig_eviz(self, *args, **kwargs):
        # Custom savefig behavior
        super().savefig(*args, **kwargs)
        # Do more custom stuff

    def show_eviz(self, *args, **kwargs):
        """Display the figure with any custom processing."""
        # Register with pyplot if needed
        if not hasattr(self, 'number') or self.number not in plt.get_fignums():
            num = max(plt.get_fignums() + [0]) + 1
            self.number = num
            plt.figure(num).canvas = self.canvas
        
        # Call the parent method or use plt.show() if needed
        plt.figure(self.number)  # Make sure this figure is active
        plt.show(*args, **kwargs)

    def _get_projection(self, projection=None) -> Optional[ccrs.Projection]:
        """Get projection parameter."""
        # Default extent and central coordinates
        extent = [-180, 180, -90, 90]
        central_lon = 0.0
        central_lat = 0.0

        # Get extent from _ax_opts if available
        extent_key = next((k for k in self._ax_opts if k.lower() == 'extent'), None)

        if extent_key:
            val = self._ax_opts[extent_key]
            if isinstance(val, str) and val.lower() == 'conus':
                extent = [-120, -70, 24, 50.5]
            elif isinstance(val, (list, tuple)) and len(val) == 4:
                extent = list(val)

            # Compute central coordinates
            central_lon = np.mean(extent[:2])
            central_lat = np.mean(extent[2:])

        if projection is None:
            self._ax_opts['extent'] = extent
            self._projection = ccrs.PlateCarree()
            return self._projection

        # Safe default for standard_parallels
        def valid_std_parallels(ext):
            lat_min, lat_max = ext[2], ext[3]
            if abs(lat_min + lat_max) > 1e-6:  # avoid lat_1 + lat_2 == 0
                return (lat_min, lat_max)
            return (33, 45)  # reasonable fallback (e.g., CONUS)

        std_parallels = valid_std_parallels(extent)

        options = {
            'mercator': ccrs.Mercator(central_longitude=central_lon),
            'robinson': ccrs.Robinson(central_longitude=central_lon),
            'orthographic': ccrs.Orthographic(
                central_longitude=central_lon, central_latitude=central_lat),
            'mollweide': ccrs.Mollweide(central_longitude=central_lon),
            'lambert': ccrs.LambertConformal(
                central_longitude=central_lon,
                central_latitude=central_lat,
                standard_parallels=std_parallels),
            'albers': ccrs.AlbersEqualArea(
                central_longitude=central_lon,
                central_latitude=central_lat,
                standard_parallels=std_parallels),
            'stereo': ccrs.Stereographic(
                central_latitude=central_lat,
                central_longitude=central_lon),
            'ortho': ccrs.Orthographic(
                central_latitude=central_lat,
                central_longitude=central_lon),
            'polar': ccrs.NorthPolarStereo(central_longitude=central_lon),
        }

        self._ax_opts['extent'] = extent
        self._projection = options.get(projection.lower())

        return self._projection

    def set_ax_opts_diff_field(self, ax):
        """ Modify axes internal state based on user-defined options

        Note:
            Only relevant for comparison plots.
        """
        geom = pu.get_subplot_geometry(ax)
        if geom[0] == (3, 1) and geom[1:] == (0, 1, 1, 1):
            self._ax_opts['is_diff_field'] = True
        if geom[0] == (2, 2):
            if geom[1:] == (0, 1, 1, 0):
                self._ax_opts['is_diff_field'] = True
            if geom[1:] == (0, 0, 1, 1):
                self._ax_opts['is_diff_field'] = True
                self._ax_opts['add_extra_field_type'] = True

    def init_ax_opts(self, field_name) -> Dict[str, Any]:
        """Initialize map options for a given field."""
        plot_type = "polar" if self.plot_type.startswith("po") else self.plot_type[:2]
        spec = self.config_manager.spec_data.get(field_name, {}).get(f"{plot_type}plot", {})
        

        existing_rc_params = {}
        if hasattr(self, '_ax_opts') and 'rc_params' in self._ax_opts:
            existing_rc_params = self._ax_opts.get('rc_params', {}).copy()  # Make a copy

        # Preserve existing domain extent and projection from config_manager if available
        existing_extent = None
        existing_projection = None
        if hasattr(self, '_ax_opts'):
            existing_extent = self._ax_opts.get('extent')
            existing_projection = self._ax_opts.get('projection')

        defaults = {
            'rc_params': existing_rc_params,
            'boundary': None,
            'use_pole': 'north',
            'profile_dim': None,
            'zsum': None,
            'zave': None,
            'tave': None,
            'taverange': 'all',
            'cmap_set_over': None,
            'cmap_set_under': None,
            'use_cmap': self.config_manager.input_config.cmap,
            'use_diff_cmap': self.config_manager.input_config.cmap,
            'cscale': None,
            'zscale': 'linear',
            'variation_threshold': 1e-12,
            'cbar_sci_notation': False,
            'custom_title': False,
            'add_grid': False,
            'line_contours': True,
            'add_tropp_height': False,
            'torder': None,
            'add_trend': False,
            'extent': existing_extent,
            'projection': existing_projection,
            'num_clevs': 10,
            'time_lev': 0,
            'is_diff_field': False,
            'add_extra_field_type': False,
            'clabel': None,
            'create_clevs': False,
            'clevs_prec': 0,
            'clevs': None,
            'plot_title': None,
            'extend_value': 'both',
            'norm': 'both',
            'overlay': False,
            'contour_linestyle': {
                'lines.linewidth': 0.5,
                'lines.linestyle': 'solid'
            },
            'time_series_plot_linestyle': {
                'lines.linewidth': 1,
                'lines.linestyle': 'solid'
            },
            'colorbar_fontsize': {
                'colorbar.fontsize': 8
            },
            'axes_fontsize': {
                'axes.fontsize': 10
            },
            'title_fontsize': {
                'title.fontsize': 10
            },
            'subplot_title_fontsize': {
                'subplot_title.fontsize': 12
            }
        }
        # self._ax_opts = {key: spec.get(key, defaults[key]) for key in defaults}

        # Create new ax_opts dictionary
        new_ax_opts = {}
        for key in defaults:
            if key == 'rc_params':
                # Special handling for rc_params to preserve existing values
                new_ax_opts[key] = defaults[key].copy()
            else:
                new_ax_opts[key] = spec.get(key, defaults[key])
        
        # Update with any new rc_params from YAML
        rc_params_from_yaml = spec.get('rc_params', {})

        rc_keys = set(mpl.rcParams.keys())
        # Filter for valid rcParams
        filtered_rc_params = {k: v for k, v in rc_params_from_yaml.items() if k in rc_keys}

        if filtered_rc_params:
            new_ax_opts['rc_params'].update(filtered_rc_params)
        
        # Set the new ax_opts
        self._ax_opts = new_ax_opts   

        return self._ax_opts

    @staticmethod
    def add_grid(ax, lines=True, locations=None):
        """Add a grid to the plot."""
        if lines:
            ax.grid(lines, alpha=0.5, which="minor", ls=":")
            ax.grid(lines, alpha=0.7, which="major")
        if locations:
            assert len(locations) == 4, "Invalid grid locations"
            ax.xaxis.set_minor_locator(MultipleLocator(locations[0]))
            ax.xaxis.set_major_locator(MultipleLocator(locations[1]))
            ax.yaxis.set_minor_locator(MultipleLocator(locations[2]))
            ax.yaxis.set_major_locator(MultipleLocator(locations[3]))

    def colorbar_eviz(self, mappable):
        """
        Create a colorbar
        https://joseph-long.com/writing/colorbars/
        """
        last_axes = plt.gca()
        ax = mappable.axes
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cbar = self.colorbar(mappable, cax=cax)
        plt.sca(last_axes)
        return cbar

    def update_ax_opts(self, field_name, ax, pid, level=None) -> Dict[str, Any]:
        """Set (or reset) some map options.

        Args:
            field_name (str): Name of field that needs axes options updated
            ax (Axes): Axes object
            pid (str): Plot type identifier
            level (int, optional): Vertical level. Defaults to None

        Returns:
            Dict[str, Any]: Updated axes internal state
        """
        if not self.config_manager.compare or not self.config_manager.compare_diff:
            return self._update_single_plot(field_name, pid, level)

        geom = get_subplot_geometry(ax)
        if self._subplots == (3, 1) and geom[1:] == (0, 1, 1, 1):
            self._ax_opts['line_contours'] = False
            self._set_clevs(field_name, f"{pid}plot",
                            f"diff_{level}" if level is not None else "diffcontours")
        elif self._subplots == (2, 2) and geom[1:] == (0, 1, 1, 0):
            self._set_clevs(field_name, f"{pid}plot",
                            f"diff_{level}" if level is not None else "diffcontours")
        elif self._subplots == (2, 2) and geom[1:] == (0, 0, 1, 1):
            self._ax_opts['line_contours'] = False
            diff_opt = f"diff_{self.config_manager.extra_diff_plot}"
            self._ax_opts['clevs'] = self.config_manager.yaml_parser.spec_data[field_name].get(diff_opt, None)
        else:
            self._set_clevs(field_name, f"{pid}plot",
                            level if isinstance(level, int) else "contours")

        # Optionally, update rc_params if new ones are found in the spec
        plot_type = "polar" if self.plot_type.startswith("po") else self.plot_type[:2]
        self.config_manager.spec_data.get(field_name, {}).get(f"{plot_type}plot", {})
        return self._ax_opts
    
    def _update_single_plot(self, field_name, pid, level):
        """Update axes options for single subplot case."""
        plot_type_map = {
            'yz': 'yzplot', 'yzave': 'yzaveplot', 'xy': 'xyplot', 'xt': 'xtplot',
            'tx': 'txplot', 'polar': 'polarplot', 'box': 'boxplot', 'corr': 'corrplot',
        }
        plot_key = plot_type_map.get(pid, None)
        if plot_key in ['xyplot', 'yzplot', 'txplot', 'polarplot']:
            self._set_clevs(field_name, plot_key,
                            level if isinstance(level, int) else "contours")

        # Update options at the field (not plot) level
        opts = {k: v for k, v in self.config_manager.spec_data[field_name].items() if not isinstance(v, dict)}
        self._ax_opts.update(opts)

        return self._ax_opts

    def _set_clevs(self, field_name, ptype, ctype):
        """ Helper function for update_ax_opts(): sets contour levels """
        if 'contours' in self.config_manager.spec_data[field_name][ptype]:
            self._ax_opts['clevs'] = self.config_manager.spec_data[field_name][ptype]['contours']
            return

        if isinstance(ctype, int):
            if ctype in self.config_manager.spec_data[field_name][ptype]['levels']:
                self._ax_opts['clevs'] = self.config_manager.spec_data[field_name][ptype]['levels'][ctype]
                if not self._ax_opts['clevs']:
                    self._ax_opts['create_clevs'] = True
            else:
                self._ax_opts['create_clevs'] = True

        else:
            if ctype in self.config_manager.spec_data[field_name][ptype]:
                self._ax_opts['clevs'] = self.config_manager.spec_data[field_name][ptype][ctype]
                if not self._ax_opts['clevs']:
                    self._ax_opts['create_clevs'] = True
            else:
                self._ax_opts['create_clevs'] = True

    def apply_rc_params(self, default_params=None):
        """Apply matplotlib rcParams from a config dictionary.

        Args:
            default_params (dict, optional): Base set of rcParams to start with. Defaults to None
        """
        if default_params is None:
            default_params = {
                'image.origin': 'lower',
                'image.interpolation': 'nearest',
                'image.cmap': 'gray',
                'axes.grid': False,
                'savefig.dpi': 150,
                'axes.labelsize': 10,
                'axes.titlesize': 14,
                'font.size': 10,
                'legend.fontsize': 6,
                'xtick.labelsize': 8,
                'ytick.labelsize': 8,
                'figure.figsize': [3.39, 2.10],
                'font.family': 'serif',
            }

        # Update with user-specific overrides
        if self.ax_opts['rc_params']:
            rc_params = self.ax_opts['rc_params']
        else:
            rc_params = default_params
        updated_params = default_params.copy()
        updated_params.update(rc_params)

        # Apply to matplotlib
        mpl.rcParams.update(updated_params)


    @staticmethod
    def get_default_plot_params() -> Dict[str, Any]:
        """
        Return default matplotlib plot parameters.

        Returns:
            dict: Default plot parameters.
        """
        return {
            'image.origin': 'lower',
            'image.interpolation': 'nearest',
            'image.cmap': 'gray',
            'axes.grid': False,
            'savefig.dpi': 150,
            'axes.labelsize': 10,
            'axes.titlesize': 14,
            'font.size': 10,
            'legend.fontsize': 6,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
            'font.family': 'sans-serif',
        }
    
    def suptitle_eviz(self, text, **kwargs):
        """Custom suptitle method that ensures proper placement."""
        # Make sure top margin is adjusted
        self.subplots_adjust(top=0.9)
        return self.suptitle(text, **kwargs)

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

    @property
    def projection(self) -> ccrs.Projection:
        return self._projection

    @property
    def frame_params(self):
        return self._frame_params

    @property
    def subplots(self):
        return self._subplots

    @property
    def use_cartopy(self):
        return self._use_cartopy

    @property
    def map_extent(self):
        return self._ax_opts['extent']

    @property
    def ax_opts(self):
        """Access to the axis options."""
        if not hasattr(self, '_ax_opts'):
            self._ax_opts = {}
        return self._ax_opts

    @ax_opts.setter
    def ax_opts(self, value):
        """Set the axis options."""
        self._ax_opts = value

    def _calculate_optimal_figsize(self):
        """Calculate optimal figure size based on subplot configuration and content type."""
        nrows, ncols = self._subplots
        
        # Base subplot size (minimum usable size)
        base_subplot_width = self._get_base_subplot_width()
        base_subplot_height = self._get_base_subplot_height()
        
        # Calculate total figure dimensions
        spacing_params = self._calculate_subplot_spacing()
        
        # Account for spacing between subplots
        total_width = (ncols * base_subplot_width + 
                    (ncols - 1) * spacing_params.get('wspace', 0.2) * base_subplot_width)
        total_height = (nrows * base_subplot_height + 
                    (nrows - 1) * spacing_params.get('hspace', 0.2) * base_subplot_height)
        
        # Add margins for labels, titles, colorbars
        margin_width = self._calculate_margin_width()
        margin_height = self._calculate_margin_height()
        
        final_width = total_width + margin_width
        final_height = total_height + margin_height
        
        # Apply constraints
        final_width = max(4, min(final_width, 20))  # Reasonable bounds
        final_height = max(3, min(final_height, 16))
        
        return (final_width, final_height)

    def _get_base_subplot_width(self):
        """Get base width for a single subplot based on plot type."""
        if self._is_map_plot():
            # Maps need more width, especially for regional plots
            if self._is_regional_plot():
                return 6  # Square-ish for regional maps
            else:
                return 8  # Wider for global maps
        elif self._is_time_series_plot():
            return 6  # Time series can be narrower
        else:
            return 5  # Default width

    def _get_base_subplot_height(self):
        """Get base height for a single subplot based on plot type."""
        if self._is_map_plot():
            if self._is_regional_plot():
                return 6  # Square for regional maps
            else:
                return 5  # Slightly shorter for global maps
        elif self._is_time_series_plot():
            return 4  # Time series can be shorter
        else:
            return 4  # Default height

    def _calculate_subplot_spacing(self):
        """Calculate optimal spacing between subplots."""
        nrows, ncols = self._subplots
        
        # Base spacing
        base_wspace = 0.3
        base_hspace = 0.3
        
        # Adjust based on number of subplots
        if ncols > 3:
            base_wspace = 0.2  # Tighter spacing for many columns
        elif ncols == 1:
            base_wspace = 0.1  # Minimal spacing for single column
            
        if nrows > 3:
            base_hspace = 0.2  # Tighter spacing for many rows
        elif nrows == 1:
            base_hspace = 0.1  # Minimal spacing for single row
        
        # Adjust for comparison plots
        if self.config_manager.compare and not self.config_manager.compare_diff:
            base_wspace = max(0.4, base_wspace)  # More space for comparison labels
        
        return {
            'wspace': base_wspace,
            'hspace': base_hspace
        }

    def _calculate_margin_width(self):
        """Calculate additional width needed for labels, colorbars, etc."""
        margin = 1.5  # Base margin for y-axis labels
        
        # Add space for colorbar
        if self._needs_colorbar():
            margin += 1.5
        
        # Add space for comparison labels
        if self.config_manager.compare:
            margin += 0.5
            
        return margin

    def _calculate_margin_height(self):
        """Calculate additional height needed for titles, labels, etc."""
        margin = 1.0  # Base margin for x-axis labels
        
        # Add space for titles
        if self._has_subplot_titles():
            margin += 0.8
        
        # Add space for main title
        if self._has_main_title():
            margin += 0.6
            
        return margin

    def _is_map_plot(self):
        """Check if this is a map-based plot."""
        return any(plot_type in self.plot_type for plot_type in ['tx', 'sc', 'xy'])

    def _is_regional_plot(self):
        """Check if this is a regional (non-global) map plot."""
        if not self._is_map_plot():
            return False
        
        # Check if extent is not global
        if hasattr(self, '_ax_opts') and 'extent' in self._ax_opts:
            extent = self._ax_opts['extent']
            if isinstance(extent, list) and len(extent) == 4:
                return extent != [-180, 180, -90, 90]
        
        return False

    def _is_time_series_plot(self):
        """Check if this is a time series plot."""
        return 'xt' in self.plot_type or 'time' in self.plot_type.lower()

    def _needs_colorbar(self):
        """Check if plot needs a colorbar."""
        # Most contour and image plots need colorbars
        return self._is_map_plot() or 'contour' in self.plot_type.lower()

    def _has_subplot_titles(self):
        """Check if subplots will have individual titles."""
        return self._subplots[0] * self._subplots[1] > 1

    def _has_main_title(self):
        """Check if figure will have a main title."""
        return True  # Most plots have main titles

    @classmethod
    def _get_plot_config(cls, config_manager, field_name, plot_type):
        """Extract plot-specific configuration from config manager."""
        plot_config = {
            'rc_params': {},
            'projection': None,
            'extent': None,
            'aspect_ratio': None
        }

        if (config_manager.spec_data and
            field_name in config_manager.spec_data):
            
            field_spec = config_manager.spec_data[field_name]
            plot_spec_key = plot_type + 'plot' if not plot_type.startswith('po') else 'polarplot'
            
            if plot_spec_key in field_spec:
                plot_spec = field_spec[plot_spec_key]
                plot_config['rc_params'] = plot_spec.get('rc_params', {})
                plot_config['projection'] = plot_spec.get('projection')
                plot_config['extent'] = plot_spec.get('extent')
                plot_config['aspect_ratio'] = plot_spec.get('aspect_ratio')
            
            # Also check field-level settings
            plot_config['projection'] = plot_config['projection'] or field_spec.get('projection')
            plot_config['extent'] = plot_config['extent'] or field_spec.get('extent')
        
        return plot_config

    @classmethod
    def _determine_subplot_layout(cls, config_manager, field_name, plot_type, nrows, ncols):
        """Determine optimal subplot layout based on configuration."""
        # If explicitly provided, use those values
        if nrows is not None and ncols is not None:
            return (nrows, ncols)
        
        # Check for overlay mode
        use_overlay = False
        if config_manager.compare and field_name:
            try:
                use_overlay = config_manager.should_overlay_plots(field_name, plot_type[:2])
            except AttributeError:
                use_overlay = False
        
        if use_overlay:
            return (1, 1)
        
        # Determine layout based on comparison mode
        if config_manager.compare and not config_manager.compare_diff:
            # Side-by-side comparison
            if hasattr(config_manager, 'compare_exp_ids'):
                num_comparisons = len(config_manager.compare_exp_ids)
                return (1, num_comparisons)
            else:
                return (1, 2)  # Default to 2-way comparison
        
        elif config_manager.compare_diff:
            # Comparison with difference plots
            if hasattr(config_manager, 'input_config') and hasattr(config_manager.input_config, '_comp_panels'):
                return config_manager.input_config._comp_panels
            else:
                # Default difference layout
                if config_manager.extra_diff_plot:
                    return (2, 2)
                else:
                    return (3, 1)
        
        else:
            # Single plot
            return (1, 1)

    def _initialize_ax_opts(self, plot_config):
        """Initialize axis options with plot configuration."""
        if not hasattr(self, '_ax_opts'):
            self._ax_opts = {}
        
        # Set rc_params
        self._ax_opts['rc_params'] = plot_config.get('rc_params', {})
        
        # Set projection and extent for map plots
        if plot_config.get('projection'):
            self._ax_opts['projection'] = plot_config['projection']
        
        if plot_config.get('extent'):
            self._ax_opts['extent'] = plot_config['extent']
        
        # Set aspect ratio if specified
        if plot_config.get('aspect_ratio'):
            self._ax_opts['aspect_ratio'] = plot_config['aspect_ratio']
