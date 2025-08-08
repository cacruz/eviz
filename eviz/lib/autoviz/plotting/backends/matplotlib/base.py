import numpy as np
import cartopy.crs as ccrs
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import colors
import logging
from matplotlib.ticker import FixedLocator
from matplotlib.ticker import FuncFormatter, FormatStrFormatter
from eviz.lib.autoviz.utils import FlexibleOOMFormatter, OOMFormatter
from eviz.lib.autoviz.plotting.base import BasePlotter
import eviz.lib.autoviz.utils as pu
from eviz.lib.autoviz.utils import bar_font_size, contour_tick_font_size


DEFAULT_CONTOUR_LABELSIZE = 12
DEFAULT_COLORBAR_LABELSIZE = 10
DEFAULT_COLORBAR_TICKFORMAT = "%.1f"


class MatplotlibBasePlotter(BasePlotter):
    """Base class for all Matplotlib plotters with common functionality."""

    def __init__(self):
        super().__init__()
        self.fig = None
        self.ax = None
        self.ax_opts = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def plot(self, config, data_to_plot):
        pass

    def filled_contours(
        self, config, field_name, ax, x, y, data2d, transform=None, vmin=None, vmax=None
    ):
        """Plot filled contours."""
        # Check if data is all NaN
        if np.isnan(data2d).all():
            self.logger.warning(
                f"All values are NaN for {field_name}. Cannot create contour plot."
            )
            ax.set_facecolor("whitesmoke")
            ax.text(
                0.5,
                0.5,
                "No valid data",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=16,
                color="gray",
                fontweight="bold",
            )
            return None

        # Create contour levels if they don't exist
        if (
            "clevs" not in self.ax_opts
            or self.ax_opts["clevs"] is None
            or len(self.ax_opts["clevs"]) == 0
        ):
            self._create_clevs(field_name, data2d)

        # Check if field was marked as constant during level creation
        if self.ax_opts.get("is_constant_field", False):
            self.logger.debug("Rendering constant field with neutral color and text")
            ax.set_facecolor("whitesmoke")
            ax.text(
                0.5,
                0.5,
                "Constant field",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=16,
                color="gray",
                fontweight="bold",
            )
            return None

        if config.compare:
            cmap_str = self.ax_opts["use_diff_cmap"]
        else:
            cmap_str = self.ax_opts["use_cmap"]

        try:
            if np.all(np.diff(self.ax_opts["clevs"]) > 0):
                cfilled = ax.contourf(
                    x,
                    y,
                    data2d,
                    levels=self.ax_opts["clevs"],
                    cmap=cmap_str,
                    extend=self.ax_opts["extend_value"],
                    norm=colors.Normalize(vmin=vmin, vmax=vmax),
                    transform=transform,
                )

                # Set under/over colors if specified
                if self.ax_opts["cmap_set_under"]:
                    cfilled.cmap.set_under(self.ax_opts["cmap_set_under"])
                if self.ax_opts["cmap_set_over"]:
                    cfilled.cmap.set_over(self.ax_opts["cmap_set_over"])

                ax.set_aspect("auto")
                return cfilled
            else:
                raise ValueError("Contour levels must be increasing")
        except ValueError as e:
            self.logger.error(f"Error: {e}")
            try:
                cfilled = ax.contourf(x, y, data2d, extend="both", transform=transform)
            except Exception:
                cfilled = ax.contourf(x, y, data2d, extend="both")

            return cfilled

    def _create_clevs(self, field_name, data2d, vmin=None, vmax=None):
        """Create contour levels for the plot."""
        self.logger.debug(f"Create contour levels for {field_name}")

        # If clevs already set, exit early
        if self.ax_opts.get("clevs"):
            return

        if np.isnan(data2d).all():
            self.logger.warning("All values are NaN! Cannot create contour levels.")
            self.ax_opts.update(clevs=np.array([0, 1]), clevs_prec=0)
            return

        # Determine min/max
        dmin = vmin if vmin is not None else np.nanmin(data2d)
        dmax = vmax if vmax is not None else np.nanmax(data2d)
        self.logger.debug(f"dmin: {dmin}, dmax: {dmax}")

        variation_threshold = float(self.ax_opts.get("variation_threshold", 1e-12))
        data_range = abs(dmax - dmin)
        max_abs_value = max(abs(dmin), abs(dmax))

        # Constant field detection
        if max_abs_value < 1e-10:
            is_constant = data_range < variation_threshold
        else:
            relative_threshold = max(variation_threshold, 1e-6 * max_abs_value)
            is_constant = data_range < relative_threshold

        if is_constant:
            center = (dmin + dmax) / 2
            clevs = np.array(
                [center - variation_threshold, center, center + variation_threshold])
            self.ax_opts.update(
                is_constant_field=True,
                clevs=clevs,
                clevs_prec=max(0, int(-np.floor(np.log10(variation_threshold))))
            )
            return

        self.ax_opts["is_constant_field"] = False

        # Decide number of levels
        num_levels = int(self.ax_opts.get("num_clevs", 10))

        # Logarithmic-aware spacing
        # TODO: make this an option
        if dmin > 0 and (dmax / dmin) > 50:
            self.logger.debug("Using logarithmic spacing for contour levels.")
            clevs = np.geomspace(dmin, dmax, num_levels)
        else:
            clevs = np.linspace(dmin, dmax, num_levels)

        # Precision rules
        if data_range >= 10:
            precision = 0  # integers only
        elif data_range >= 1:
            precision = 1
        elif data_range >= 0.1:
            precision = 2
        elif data_range >= 0.01:
            precision = 3
        elif data_range >= 0.001:
            precision = 4
            self.ax_opts["cbar_sci_notation"] = True
        else:
            precision = max(5, int(np.ceil(-np.log10(data_range))) + 1)
            self.ax_opts["cbar_sci_notation"] = True

        self.ax_opts["clevs_prec"] = precision

        # Keep exact levels for plotting
        clevs_display = np.round(clevs, precision)

        # Avoid collapse after rounding
        if len(np.unique(clevs_display)) < num_levels // 2:
            precision += 2
            clevs_display = np.round(clevs, precision)

        self.ax_opts["clevs"] = clevs
        self.ax_opts["clevs_display"] = clevs_display  # for labels

        self.logger.debug(f"Created contour levels: {self.ax_opts['clevs']}")

    def line_contours(self, fig, ax, x, y, data2d, transform=None):
        """Add line contours to the plot."""
        with mpl.rc_context(rc=self.ax_opts.get("rc_params", {})):
            try:
                # Check if clevs exists and has enough levels
                if (
                    "clevs" not in self.ax_opts
                    or self.ax_opts["clevs"] is None
                    or len(self.ax_opts["clevs"]) < 2
                ):
                    return

                try:
                    formatted_clevs = pu.formatted_contours(self.ax_opts["clevs"])
                    contour_format = pu.contour_format_from_levels(
                        formatted_clevs, scale=self.ax_opts.get("cscale", None)
                    )
                except IndexError:
                    # Handle the case where contour_format_from_levels fails
                    contour_format = "%.1f"

                clines = ax.contour(
                    x,
                    y,
                    data2d,
                    levels=self.ax_opts["clevs"],
                    colors="black",
                    alpha=0.5,
                    transform=transform,
                )
                if len(clines.allsegs) == 0 or all(
                    len(seg) == 0 for seg in clines.allsegs
                ):
                    return
                self.clabel_with_default_fontsize(
                    ax, clines, fmt=contour_format, fontsize=8
                )
            except Exception as e:
                self.logger.error(f"Error adding contour lines: {e}")

    def set_colorbar(
        self, config, cfilled, fig, ax, findex, field_name, data2d
    ):
        """Add a colorbar to the plot."""
        self.logger.debug(f"Create colorbar for {field_name}")
        try:
            # Skip colorbar creation if suppressed (for shared colorbar)
            if self.ax_opts.get("suppress_colorbar", False):
                return None

            # Create formatter for colorbar ticks
            if self.ax_opts["cbar_sci_notation"]:
                fmt = pu.FlexibleOOMFormatter(
                    min_val=data2d.min().compute().item(),
                    max_val=data2d.max().compute().item(),
                    math_text=True,
                )
            else:
                fmt = pu.OOMFormatter(prec=self.ax_opts["clevs_prec"], math_text=True)

            if not fig.use_cartopy:
                cbar = fig.colorbar(cfilled)
            else:
                cbar = fig.colorbar(
                    cfilled,
                    ax=ax,
                    orientation="vertical"
                    if config.compare or config.compare_diff
                    else "horizontal",
                    pad=pu.cbar_pad(fig.subplots),
                    fraction=pu.cbar_fraction(fig.subplots),
                    ticks=self.ax_opts.get("clevs", None),
                    format=fmt,
                    shrink=pu.cbar_shrink(fig.subplots),
                )

            if self.ax_opts["clabel"] is None:
                cbar_label = self.units
            else:
                cbar_label = self.ax_opts["clabel"]
            self.style_colorbar(
                cbar, data2d, fmt=fmt, fontsize=8, label=cbar_label
            )

            for t in cbar.ax.get_xticklabels():
                t.set_fontsize(pu.contour_tick_font_size(fig.subplots))
            for t in cbar.ax.get_yticklabels():
                t.set_fontsize(pu.contour_tick_font_size(fig.subplots))

            return cbar

        except Exception as e:
            self.logger.error(f"Failed to add colorbar: {e}")
            return None

    def add_shared_colorbar(self, fig, cfilled_objects, field_name, config):
        """Add a shared colorbar for all plots.

        Args:
            fig: The figure object
            cfilled_objects: List of filled contour objects
            field_name: Name of the field being plotted
            config: Configuration manager

        Returns:
            The created colorbar object
        """
        self.logger.debug(f"Adding shared colorbar for {field_name}")

        # First, check if we already have a shared colorbar and remove it
        if hasattr(fig, "_shared_colorbar_ax") and fig._shared_colorbar_ax in fig.axes:
            self.logger.debug("Removing existing shared colorbar")
            fig._shared_colorbar_ax.remove()

        # Filter out None values
        valid_contours = [c for c in cfilled_objects if c is not None]

        if not valid_contours:
            self.logger.warning("No valid contours for shared colorbar")
            return None

        self.logger.debug(
            f"Found {len(valid_contours)} valid contours for shared colorbar"
        )
        for i, contour in enumerate(valid_contours):
            self.logger.debug(f"Contour {i} clim: {contour.get_clim()}")

        # Get the min and max values across all contours for THIS field only
        vmin = min(c.get_clim()[0] for c in valid_contours)
        vmax = max(c.get_clim()[1] for c in valid_contours)

        self.logger.debug(f"Shared colorbar range for {field_name}: {vmin} to {vmax}")

        # Create a new axes for the colorbar
        colorbar_width = getattr(config, "colorbar_width", 0.02)
        cbar_ax = fig.add_axes([0.92, 0.15, colorbar_width, 0.7])

        fig._shared_colorbar_ax = cbar_ax

        # Create the colorbar using the first valid contour
        cbar = fig.colorbar(valid_contours[0], cax=cbar_ax)

        # Encompass all data for this field
        cbar.mappable.set_clim(vmin, vmax)

        tick_font_size = 8  # Fixed size for shared colorbar
        cbar.ax.tick_params(labelsize=tick_font_size)
        cbar.set_label(self.units, size=10)

        return cbar

    @staticmethod
    def set_const_colorbar(cfilled, fig, ax):
        _ = fig.colorbar(cfilled, ax=ax, shrink=0.5)

    def get_long_name(self, config, data2d, findex):
        """Get long or descriptive name for the field."""
        try:
            # User-provided name
            user_spec = config.spec_data.get(data2d.name, {})
            if 'name' in user_spec:
                self.logger.debug(f"Using user-provided name for {data2d.name}")
                return user_spec['name']

            # Attribute names
            for attr_key in ['long_name', 'standard_name', 'description']:
                if attr_key in getattr(data2d, 'attrs', {}):
                    self.logger.debug(f"Using {attr_key} from attrs for {data2d.name}")
                    return data2d.attrs[attr_key]

            # Fallback: use variable name
            self.logger.debug(f"No descriptive name found; using variable name {data2d.name}")
            return data2d.name

        except Exception as e:
            self.logger.error(f"Error getting long name for {getattr(data2d, 'name', 'unknown')}: {e}")
            return None

    def get_units(self, config, field_name, data2d, findex):
        """Get units for the field."""
        self.logger.debug(f"Get units for {field_name}")
        try:
            if (
                field_name in config.spec_data
                and "units" in config.spec_data[field_name]
            ):
                return config.spec_data[field_name]["units"]

            if hasattr(data2d, "attrs") and "units" in data2d.attrs:
                return data2d.attrs["units"]
            elif hasattr(data2d, "units"):
                return data2d.units
            else:
                self.logger.warning(f"Could not find units for {field_name}")
                return "n.a."
        except Exception as e:
            self.logger.warning(f"Error getting units: {e}")
            return "n.a."

    def set_cartopy_ticks(self, ax, extent, labelsize=10):
        """Add gridlines and tick labels to a Cartopy map."""

        # Sanity check
        if not extent or len(extent) != 4:
            extent = [-180, 180, -90, 90]

        try:
            ax.set_extent(extent, crs=ccrs.PlateCarree())
        except Exception as e:
            self.logger.warning(f"Could not set extent: {e}")

        try:
            gl = ax.gridlines(
                crs=ccrs.PlateCarree(),
                draw_labels=True,
                linewidth=0.8,
                color="gray",
                alpha=0.6,
                linestyle="--",
            )

            gl.top_labels = False
            gl.bottom_labels = True
            gl.left_labels = True
            gl.right_labels = False

            gl.xlabel_style = {"size": labelsize, "rotation": 0}
            gl.ylabel_style = {"size": labelsize, "rotation": 0}

            return True
        except Exception as e:
            self.logger.error(f"Could not set ticks and labels: {e}")
            return False

    def _set_cartopy_ticks_alt(self, ax, extent, labelsize=10):
        """
        Adds gridlines and tick labels (in degrees) outside the map for Lambert and PlateCarree.
        Places longitude labels below the map, latitude on the left.
        """

        # Sanity check
        if not extent or len(extent) != 4:
            extent = [-180, 180, -90, 90]

        try:
            ax.set_extent(extent, crs=ccrs.PlateCarree())
        except Exception as e:
            self.logger.warning(f"Could not set extent: {e}")

        try:
            xticks_deg = np.arange(extent[0], extent[1] + 1, 10)
            yticks_deg = np.arange(extent[2], extent[3] + 1, 10)

            # Use Cartopy's gridlines just for visual grid, no labels
            gl = ax.gridlines(
                crs=ccrs.PlateCarree(),
                draw_labels=False,
                linewidth=0.8,
                color="gray",
                alpha=0.6,
                linestyle="--",
            )
            gl.xlocator = FixedLocator(xticks_deg)
            gl.ylocator = FixedLocator(yticks_deg)

            # Compute projected x/y positions of tick lines
            x_tick_positions = []
            for lon in xticks_deg:
                try:
                    x, _ = ax.projection.transform_point(
                        lon, extent[2], ccrs.PlateCarree()
                    )
                    x_tick_positions.append(x)
                except:
                    continue

            y_tick_positions = []
            for lat in yticks_deg:
                try:
                    _, y = ax.projection.transform_point(
                        extent[0], lat, ccrs.PlateCarree()
                    )
                    y_tick_positions.append(y)
                except:
                    continue

            # Now map projected positions to geographic labels using the original values
            ax.set_xticks(x_tick_positions)
            ax.set_xticklabels([f"{lon}°" for lon in xticks_deg], fontsize=labelsize)
            ax.tick_params(axis="x", direction="out", pad=5)

            ax.set_yticks(y_tick_positions)
            ax.set_yticklabels([f"{lat}°" for lat in yticks_deg], fontsize=labelsize)
            ax.tick_params(axis="y", direction="out", pad=5)

            return True

        except Exception as e:
            self.logger.error(f"Could not set ticks and labels: {e}")
            return False

    def show(self):
        """Display the plot."""
        pass

    def save(self, filename, **kwargs):
        """Save the plot to a file."""
        pass

    @staticmethod
    def _legend_font_size(subplots):
        """Determine appropriate font size for legends based on subplot layout."""
        return pu.legend_font_size(subplots)

    @staticmethod
    def _image_font_size(subplots):
        """Get appropriate font size based on subplot layout."""
        return pu.image_font_size(subplots)

    @staticmethod
    def clabel_with_default_fontsize_mpl(contour, **kwargs):
        """Label contours with a default font size if not specified (QuadContourSet)."""
        if "fontsize" not in kwargs:
            kwargs["fontsize"] = 12
        return contour.ax.clabel(contour, **kwargs)

    @staticmethod
    def clabel_with_default_fontsize(ax, contour, **kwargs):
        """Label contours with a default font size if not specified (GeoContourSet)."""
        kwargs.setdefault("fontsize", DEFAULT_CONTOUR_LABELSIZE)
        return ax.clabel(contour, **kwargs)

    def style_colorbar(self, cbar, data, fmt="%.1f", fontsize=8, label=None):
        """Style the colorbar with a given format and font size."""
        # Set tick label font size
        cbar.ax.tick_params(labelsize=fontsize)

        # Set the formatter properly
        if isinstance(fmt, str):
            formatter = FormatStrFormatter(fmt)
        else:
            formatter = FuncFormatter(fmt)

        cbar.ax.xaxis.set_major_formatter(formatter)
        cbar.ax.yaxis.set_major_formatter(formatter)
        cbar.update_ticks()

        # Set label if provided
        if label:
            cbar.set_label(label, fontsize=fontsize)

        vmin = np.nanmin(data)
        vmax = np.nanmax(data)
        max_val = max(abs(vmin), abs(vmax))

        clevs = self.ax_opts.get("clevs", None)
        num_clevs = len(clevs) if clevs is not None else 0

        really_small_vals = max_val < 1e-3 or num_clevs > 10
        really_large_vals = max_val >= 1e3 or num_clevs > 10

        # Rotate labels for horizontal colorbars with really small/large values
        if really_small_vals or really_large_vals:
            if cbar.orientation == "horizontal":
                for label in cbar.ax.get_xticklabels():
                    label.set_rotation(45)

        # Add scientific notation if requested
        if self.ax_opts["cbar_sci_notation"]:
            cbar.ax.text(
                1.05,
                -0.5,
                r"$\times 10^{%d}$" % fmt.oom,
                transform=cbar.ax.transAxes,
                va="center",
                ha="left",
                fontsize=8,
            )

    def plot_text(self, config, field_name, pid, level=None, data=None, *args, **kwargs):
        """Add text to a map.

        Parameters:
            config (ConfigManager): configuration object for the plot
            field_name (str): Name of the field
            pid (str): Plot type identifier
            level (int): Vertical level (optional, default=None)
            data (Any): xarray Data for basic stats (optional)
            *args: Additional positional arguments for customization
            **kwargs: Additional keyword arguments for customization
        """
        if isinstance(self.ax, list):  # Check if ax is a list
            for single_ax in self.ax:
                self._plot_text(config, field_name, pid, level, data, **kwargs)
        else:
            self._plot_text(config, field_name, pid, level, data, **kwargs)

    def _plot_text(self, config, field_name, pid, level=None, data=None, **kwargs):
        """Add text to a single axes."""
        font_size = None
        title_size = None

        ax = self.ax
        if pid == 'tx':
            ax = self.ax[0]
            
        # Extract properties from rc_params
        if 'rc_params' in self.ax_opts:
            font_size = self.ax_opts['rc_params'].get('font.size', None)
            title_size = self.ax_opts['rc_params'].get('axes.titlesize', None)
        else:
            self.ax_opts['rc_params'] = {}
        fontsize = font_size or pu.subplot_title_font_size(self.fig.subplots)
        title_fontsize = title_size or fontsize
        loc = kwargs.get('location', 'left')

        findex = config.findex
        sname = config.config.map_params[findex]['source_name']
        geom = pu.get_subplot_geometry(ax) if config.compare or config.compare_diff else None

        # Handle plot titles for comparison cases
        if config.compare or config.compare_diff:
            if geom and geom[0] == (3, 1):  # (3,1) subplot structure
                if geom[1:] == (0, 1, 1, 1):  # Bottom plot
                    title_string = "Difference (top - middle)"
                elif geom[1:] in [(1, 1, 0, 1), (0, 1, 0, 1)]:  # Top/Middle plots
                    title_string = self._set_axes_title(config, findex)
            elif self.fig.subplots == (2, 2):  # (2,2) subplot structure
                if geom[1:] == (0, 1, 1, 0):
                    title_string = "Difference (left - right)"
                elif geom[1:] == (0, 0, 1, 1):  # Extra diff plot
                    diff_labels = {
                        "percd": ("% Diff", "%"),
                        "percc": ("% Change", "%"),
                        "ratio": ("Ratio Diff", "ratio"),
                    }
                    diff_type = config.extra_diff_plot
                    title_string, self.ax_opts['clabel'] = diff_labels.get(
                        diff_type, ("Difference (left - right)", None))
                    self.ax_opts['line_contours'] = False
                else:  # Default case
                    title_string = self._set_axes_title(config, findex)
            elif geom and (geom[0] == (1, 2) or geom[0] == (1, 3)):
                title_string = self._set_axes_title(config, findex)
            ax.set_title(title_string, loc=loc, fontsize=title_fontsize)
            return

        # Non-comparison case
        level_text = self._format_level_text(config, level)
        long_name = self.get_long_name(config, data, findex)
        if not long_name:
            long_name = field_name

        left, width = 0, 1.0
        bottom, height = 0, 1.0
        right = left + width
        top = bottom + height
        title_string = self._set_axes_title(config, findex)
        if 'yz' in pid:
            if config.print_basic_stats:
                # plt.rc('text', usetex=True)
                fmt = self._basic_stats(data)
                ax.text(right, top, fmt, transform=ax.transAxes,
                        ha='right', va='bottom', fontsize=10)

            if config.use_history:
                ax.set_title(config.history_expid + " (" + config.history_expdsc + ")")
            else:
                ax.set_title(title_string, loc=loc, fontsize=10)

            ax.text(0.5 * (left + right), bottom + top + 0.1,
                    long_name, fontweight='bold',
                    fontstyle='italic',
                    horizontalalignment='center',
                    verticalalignment='center',
                    fontsize=14,
                    transform=ax.transAxes)

        elif 'xy' in pid or 'sc' in pid:
            if config.print_basic_stats:
                fmt = self._basic_stats(data)
                ax.text(right, top, fmt, transform=ax.transAxes,
                        ha='right', va='bottom', fontsize=10)
                loc = 'left'

            if config.real_time and not config.print_basic_stats:
                ax.text(right, top, config.real_time,
                        ha='right', va='bottom', fontsize=10,
                        transform=ax.transAxes)
            if config.use_history:
                ax.set_title(
                    config.history_expid + " (" + config.history_expdsc + ")",
                    fontsize=title_fontsize
                )
            else:
                ax.set_title(title_string, loc=loc, fontsize=10)

            ax.text(0.5 * (left + right), bottom + top + 0.1,
                    long_name + level_text, 
                    fontweight=kwargs.get('fontweight', 'bold'),
                    fontstyle=kwargs.get('fontstyle', 'italic'),
                    fontsize=kwargs.get('fontsize', 14),
                    horizontalalignment=kwargs.get('ha', 'center'),
                    verticalalignment=kwargs.get('va', 'center'),
                    transform=ax.transAxes)

        elif 'tx' in pid:
            if config.use_history:
                ax.set_title(
                    config.history_expid + " (" + config.history_expdsc + ")",
                    fontsize=10
                )
            else:
                ax.set_title(
                    title_string, loc=kwargs.get('loc', 'right'),
                    fontsize=kwargs.get('fontsize', 10)
                )

            ax.text(0.5 * (left + right), bottom + top + 0.5,
                    long_name,
                    fontweight=kwargs.get('fontweight', 'bold'),
                    fontstyle=kwargs.get('fontstyle', 'normal'),
                    fontsize=kwargs.get('fontsize', 12),
                    horizontalalignment=kwargs.get('ha', 'center'),
                    verticalalignment=kwargs.get('va', 'center'),
                    transform=ax.transAxes)
        elif 'po' in pid:
            pass
        elif 'corr' in pid:
            ax.text(0.5 * (left + right), bottom + top + 0.1,
                    long_name + level_text, 
                    fontweight=kwargs.get('fontweight', 'bold'),
                    fontstyle=kwargs.get('fontstyle', 'italic'),
                    fontsize=kwargs.get('fontsize', 12),
                    horizontalalignment=kwargs.get('ha', 'center'),
                    verticalalignment=kwargs.get('va', 'center'),
                    transform=ax.transAxes)
        else:  # 'xt' and others
            if config.use_history:
                ax.set_title(config.history_expid + " (" + config.history_expdsc + ")")
            else:
                ax.set_title(title_string, loc=loc, fontsize=10)

            if self.ax_opts['custom_title']:
                long_name = self.ax_opts['custom_title']

            ax.text(0.5 * (left + right), bottom + top + 0.1,
                    long_name,
                    fontweight=kwargs.get('fontweight', 'bold'),
                    fontstyle=kwargs.get('fontstyle', 'italic'),
                    fontsize=fontsize,
                    horizontalalignment=kwargs.get('ha', 'center'),
                    verticalalignment=kwargs.get('va', 'center'),
                    transform=ax.transAxes)
        
    def _set_axes_title(self, config, findex):
        if config.overlay:
            return None
        if config.get_file_description(findex):
            return config.get_file_description(findex)
        elif config.get_file_exp_name(findex):
            return config.get_file_exp_name(findex)
        elif config.get_file_exp_id(findex):
            return config.get_file_exp_id(findex)

        return None
        
    @staticmethod
    def _basic_stats(data):
        """ Basic stats for a given field """
        # datamin = data.min().values
        # datamax = data.max().values
        datamean = data.mean().values
        datastd = data.std().values
        return f"\nMean:{datamean:.2e}\nStd:{datastd:.2e}"

    def _format_level_text(self, config, level):
        """Format level annotation text based on level value."""
        if self.ax_opts.get('zave'):
            return ' (Column Mean)'
        if self.ax_opts.get('zsum'):
            return ' (Total Column)'
        if level is None or str(level) == '0':
            return ''
        return f"@ {level} {'Pa' if level > 10000 else 'mb'}"
