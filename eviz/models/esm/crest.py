import logging
import warnings
from dataclasses import dataclass

import numpy as np

from eviz.lib.autoviz.figure import Figure
from eviz.models.gridded_source import GriddedSource
from eviz.models.obs_source import ObsSource
from eviz.models.source_base import GenericSource

warnings.filterwarnings("ignore")


@dataclass
class Crest(GenericSource):
    """The Crest class contains definitions for handling CREST data. This is data
    produced by the Coupled Reusable Earth System Tensor-framework.
    """

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

    def __post_init__(self):
        self.logger.info("Start init")
        super().__post_init__()
        self.comparison_plot = False
        self.source_name = "crest"

        # Create instances of both source types
        self.gridded_handler = GriddedSource(self.config_manager)
        self.obs_handler = ObsSource(self.config_manager)

    def process_plot(self, data_array, field_name, file_index, plot_type):
        """Process a plot, delegating to the appropriate handler based on data type."""
        self.register_plot_type(field_name, plot_type)

        figure = Figure.create_eviz_figure(self.config_manager, plot_type)
        self.config_manager.ax_opts = figure.init_ax_opts(field_name)

        is_obs = self._is_observational_data(data_array)

        # For observational data, extract extent information early
        if is_obs:
            self.logger.info(f"Processing {field_name} as observational data")
            handler = self.obs_handler

            # Extract and apply extent information
            extent = handler.get_data_extent(data_array)
            self.config_manager.ax_opts["extent"] = extent
            self.config_manager.ax_opts["central_lon"] = (extent[0] + extent[1]) / 2
            self.config_manager.ax_opts["central_lat"] = (extent[2] + extent[3]) / 2
        else:
            self.logger.info(f"Processing {field_name} as gridded data")
            handler = self.gridded_handler

        # Call the appropriate method on the selected handler
        if plot_type == "xy":
            if hasattr(handler, "_process_xy_plot"):
                handler._process_xy_plot(
                    data_array, field_name, file_index, plot_type, figure
                )
            else:
                self.logger.warning(
                    f"_process_xy_plot not implemented for {handler.__class__.__name__}"
                )
        if plot_type == "sc":
            if hasattr(handler, "_process_scatter_plot"):
                handler._process_scatter_plot(
                    data_array, field_name, file_index, plot_type, figure
                )
            else:
                self.logger.warning(
                    f"_process_scatter_plot not implemented for {handler.__class__.__name__}"
                )
        elif plot_type == "polar":
            if hasattr(handler, "_process_polar_plot"):
                handler._process_polar_plot(
                    data_array, field_name, file_index, plot_type, figure
                )
            else:
                self.logger.warning(
                    f"_process_polar_plot not implemented for {handler.__class__.__name__}"
                )
        elif plot_type == "xt":
            if hasattr(handler, "_process_xt_plot"):
                handler._process_xt_plot(
                    data_array, field_name, file_index, plot_type, figure
                )
            else:
                self.logger.warning(
                    f"_process_xt_plot not implemented for {handler.__class__.__name__}"
                )
        elif plot_type == "box":
            if hasattr(handler, "_process_box_plot"):
                handler._process_box_plot(
                    data_array, field_name, file_index, plot_type, figure
                )
            else:
                self.logger.warning(
                    f"_process_box_plot not implemented for {handler.__class__.__name__}"
                )
        elif plot_type == "line":
            if hasattr(handler, "_process_line_plot"):
                handler._process_line_plot(
                    data_array, field_name, file_index, plot_type, figure
                )
            else:
                self.logger.warning(
                    f"_process_line_plot not implemented for {handler.__class__.__name__}"
                )
        elif plot_type == "corr":
            if hasattr(handler, "_process_corr_plot"):
                handler._process_corr_plot(
                    data_array, field_name, file_index, plot_type, figure
                )
            else:
                self.logger.warning(
                    f"_process_corr_plot not implemented for {handler.__class__.__name__}"
                )

    def _process_xy_side_by_side_plots(
        self,
        current_field_index,
        field_name1,
        field_name2,
        plot_type,
        sdat1_dataset,
        sdat2_dataset,
    ):
        """Process side-by-side comparison plots for xy plot types.

        This method delegates to either the gridded_handler or obs_handler based on the data type.
        """
        is_obs1 = self._is_observational_data(sdat1_dataset[field_name1])
        is_obs2 = self._is_observational_data(sdat2_dataset[field_name2])

        if is_obs1 and is_obs2:
            self.logger.info(
                f"Processing side-by-side comparison of {field_name1} vs {field_name2} as observational data"
            )
            return self.obs_handler._process_xy_side_by_side_plots(
                current_field_index,
                field_name1,
                field_name2,
                plot_type,
                sdat1_dataset,
                sdat2_dataset,
            )
        elif not is_obs1 and not is_obs2:
            self.logger.info(
                f"Processing side-by-side comparison of {field_name1} vs {field_name2} as gridded data"
            )
            return self.gridded_handler._process_xy_side_by_side_plots(
                current_field_index,
                field_name1,
                field_name2,
                plot_type,
                sdat1_dataset,
                sdat2_dataset,
            )
        else:
            self.logger.warning(
                f"Mixed data types in comparison: {field_name1} is {'observational' if is_obs1 else 'gridded'} "
                f"and {field_name2} is {'observational' if is_obs2 else 'gridded'}"
            )

            orig_obs_handler = self.obs_handler
            orig_gridded_handler = self.gridded_handler

            # Create temporary handlers for mixed data
            if is_obs1:
                # First dataset is observational, second is gridded
                # Use observational handler but give it access to gridded methods
                self.obs_handler.file_indices = self.file_indices
                self.obs_handler.field_names = self.field_names
                return self.obs_handler._process_xy_side_by_side_plots(
                    current_field_index,
                    field_name1,
                    field_name2,
                    plot_type,
                    sdat1_dataset,
                    sdat2_dataset,
                )
            else:
                # First dataset is gridded, second is observational
                # Use gridded handler but give it access to observational methods
                self.gridded_handler.file_indices = self.file_indices
                self.gridded_handler.field_names = self.field_names
                return self.gridded_handler._process_xy_side_by_side_plots(
                    current_field_index,
                    field_name1,
                    field_name2,
                    plot_type,
                    sdat1_dataset,
                    sdat2_dataset,
                )

    def _process_other_side_by_side_plots(
        self,
        current_field_index,
        field_name1,
        field_name2,
        plot_type,
        sdat1_dataset,
        sdat2_dataset,
    ):
        """Process side-by-side comparison plots for non-xy plot types.

        This method delegates to either the gridded_handler or obs_handler based on the data type.
        """
        is_obs1 = self._is_observational_data(sdat1_dataset[field_name1])
        is_obs2 = self._is_observational_data(sdat2_dataset[field_name2])

        if is_obs1 and is_obs2:
            self.logger.info(
                f"Processing side-by-side comparison of {field_name1} vs {field_name2} as observational data"
            )
            return self.obs_handler._process_other_side_by_side_plots(
                current_field_index,
                field_name1,
                field_name2,
                plot_type,
                sdat1_dataset,
                sdat2_dataset,
            )
        elif not is_obs1 and not is_obs2:
            self.logger.info(
                f"Processing side-by-side comparison of {field_name1} vs {field_name2} as gridded data"
            )
            return self.gridded_handler._process_other_side_by_side_plots(
                current_field_index,
                field_name1,
                field_name2,
                plot_type,
                sdat1_dataset,
                sdat2_dataset,
            )
        else:
            # Mixed data types - this is more complex
            self.logger.warning(
                f"Mixed data types in comparison: {field_name1} is {'observational' if is_obs1 else 'gridded'} "
                f"and {field_name2} is {'observational' if is_obs2 else 'gridded'}"
            )

            orig_obs_handler = self.obs_handler
            orig_gridded_handler = self.gridded_handler

            # Create temporary handlers for mixed data
            if is_obs1:
                # First dataset is observational, second is gridded
                # Use observational handler but give it access to gridded methods
                self.obs_handler.file_indices = self.file_indices
                self.obs_handler.field_names = self.field_names
                return self.obs_handler._process_other_side_by_side_plots(
                    current_field_index,
                    field_name1,
                    field_name2,
                    plot_type,
                    sdat1_dataset,
                    sdat2_dataset,
                )
            else:
                # First dataset is gridded, second is observational
                # Use gridded handler but give it access to observational methods
                self.gridded_handler.file_indices = self.file_indices
                self.gridded_handler.field_names = self.field_names
                return self.gridded_handler._process_other_side_by_side_plots(
                    current_field_index,
                    field_name1,
                    field_name2,
                    plot_type,
                    sdat1_dataset,
                    sdat2_dataset,
                )

    def _process_xy_comparison_plots(
        self,
        file_indices,
        current_field_index,
        field_name1,
        field_name2,
        plot_type,
        sdat1_dataset,
        sdat2_dataset,
    ):
        """Process comparison plots for xy or polar plot types.

        This method delegates to either the gridded_handler or obs_handler based on the data type.
        """
        is_obs1 = self._is_observational_data(sdat1_dataset[field_name1])
        is_obs2 = self._is_observational_data(sdat2_dataset[field_name2])

        if is_obs1 and is_obs2:
            self.logger.info(
                f"Processing comparison of {field_name1} vs {field_name2} as observational data"
            )
            return self.obs_handler._process_xy_comparison_plots(
                file_indices,
                current_field_index,
                field_name1,
                field_name2,
                plot_type,
                sdat1_dataset,
                sdat2_dataset,
            )
        elif not is_obs1 and not is_obs2:
            self.logger.info(
                f"Processing comparison of {field_name1} vs {field_name2} as gridded data"
            )
            return self.gridded_handler._process_xy_comparison_plots(
                file_indices,
                current_field_index,
                field_name1,
                field_name2,
                plot_type,
                sdat1_dataset,
                sdat2_dataset,
            )
        else:
            # Mixed data types - this is more complex
            self.logger.warning(
                f"Mixed data types in comparison: {field_name1} is {'observational' if is_obs1 else 'gridded'} "
                f"and {field_name2} is {'observational' if is_obs2 else 'gridded'}"
            )

            # For mixed data types, use the gridded handler as it's generally more flexible
            self.gridded_handler.field_names = (field_name1, field_name2)
            return self.gridded_handler._process_xy_comparison_plots(
                file_indices,
                current_field_index,
                field_name1,
                field_name2,
                plot_type,
                sdat1_dataset,
                sdat2_dataset,
            )

    def _process_other_comparison_plots(
        self,
        file_indices,
        current_field_index,
        field_name1,
        field_name2,
        plot_type,
        sdat1_dataset,
        sdat2_dataset,
    ):
        """Process comparison plots for other plot types.

        This method delegates to either the gridded_handler or obs_handler based on the data type.
        """
        is_obs1 = self._is_observational_data(sdat1_dataset[field_name1])
        is_obs2 = self._is_observational_data(sdat2_dataset[field_name2])

        if is_obs1 and is_obs2:
            self.logger.info(
                f"Processing comparison of {field_name1} vs {field_name2} as observational data"
            )
            return self.obs_handler._process_other_comparison_plots(
                file_indices,
                current_field_index,
                field_name1,
                field_name2,
                plot_type,
                sdat1_dataset,
                sdat2_dataset,
            )
        elif not is_obs1 and not is_obs2:
            self.logger.info(
                f"Processing comparison of {field_name1} vs {field_name2} as gridded data"
            )
            return self.gridded_handler._process_other_comparison_plots(
                file_indices,
                current_field_index,
                field_name1,
                field_name2,
                plot_type,
                sdat1_dataset,
                sdat2_dataset,
            )
        else:
            # Mixed data types - this is more complex
            self.logger.warning(
                f"Mixed data types in comparison: {field_name1} is {'observational' if is_obs1 else 'gridded'} "
                f"and {field_name2} is {'observational' if is_obs2 else 'gridded'}"
            )

            # For mixed data types, use the gridded handler as it's generally more flexible
            self.gridded_handler.field_names = (field_name1, field_name2)
            return self.gridded_handler._process_other_comparison_plots(
                file_indices,
                current_field_index,
                field_name1,
                field_name2,
                plot_type,
                sdat1_dataset,
                sdat2_dataset,
            )

    def _is_observational_data(self, data_array):
        """
        Determine if the data array should be treated as observational data.

        This method checks various characteristics of the data to determine
        if it should be processed as observational data (e.g., swath format)
        or as standard gridded data.

        Parameters
        ----------
            data_array
                The xarray DataArray to check

        Returns
        -------
            bool
                True if the data should be treated as observational
        """
        if data_array is None:
            return False

        # Check for characteristics of observational data
        try:
            # 2D coordinate arrays (common in swath data)
            for coord_name in data_array.coords:
                if ("lon" in coord_name.lower() or "lat" in coord_name.lower()) and len(
                    data_array[coord_name].shape
                ) == 2:
                    return True

            # Irregular grid spacing
            xc_dim = self.config_manager.get_model_dim_name("xc") or "lon"
            yc_dim = self.config_manager.get_model_dim_name("yc") or "lat"

            if xc_dim in data_array.coords and yc_dim in data_array.coords:
                lon_vals = data_array[xc_dim].values
                if len(lon_vals) > 2:
                    lon_diffs = np.diff(
                        lon_vals
                    )  # Check if longitude spacing is regular
                    if not np.allclose(lon_diffs, lon_diffs[0], rtol=1e-3):
                        return True

                lat_vals = data_array[yc_dim].values
                if len(lat_vals) > 2:
                    lat_diffs = np.diff(
                        lat_vals
                    )  # Check if latitude spacing is regular
                    if not np.allclose(lat_diffs, lat_diffs[0], rtol=1e-3):
                        return True

            # Observational metadata (usually in attributes)
            for attr in ["platform", "instrument", "sensor", "satellite"]:
                if hasattr(data_array, attr) or attr in data_array.attrs:
                    return True

            # Do we have limited geographical coverage (i.e., not global)?
            if xc_dim in data_array.coords and yc_dim in data_array.coords:
                lon_min, lon_max = np.nanmin(data_array[xc_dim]), np.nanmax(
                    data_array[xc_dim]
                )
                lat_min, lat_max = np.nanmin(data_array[yc_dim]), np.nanmax(
                    data_array[yc_dim]
                )

                # Hackish way to check...
                if (lon_max - lon_min < 300) or (lat_max - lat_min < 150):
                    return True

        except Exception as e:
            self.logger.debug(f"Error checking if data is observational: {e}")

        # Default to gridded
        return False
