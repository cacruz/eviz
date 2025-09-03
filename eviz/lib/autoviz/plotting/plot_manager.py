import logging
import os
import numpy as np
import xarray as xr
import pandas as pd
from eviz.lib.autoviz.plotting.backends.matplotlib.simple_plot import SimplePlotter
from eviz.lib.autoviz.plotting.factory import PlotterFactory
from eviz.lib.autoviz.figure import Figure
import eviz.lib.utils as u
import eviz.lib.autoviz.utils as pu
from eviz.lib.config.config_manager import ConfigManager
from eviz.lib.data.data_extractor import DataExtractor
from eviz.lib.data.utils import subset_region


class PlotManager:
    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

    def __init__(self, config_manager: ConfigManager, data_extractor: DataExtractor):
        self.config_manager = config_manager
        self.data_extractor = data_extractor
        self.data2d_list = []
        self.plot_result = None
        self.field_names = None
        self.file_indices = None
        self.lon = None
        self.lat = None

    def plot(self):
        """
        Generate plots for gridded fields based on current configuration.

        This is the top-level interface for plotting spatial data using one of several
        supported modes. Plotting behavior is determined by the presence or absence of
        SPECS data and by the configuration options set in the `config_manager`.

        Plot Types
        ----------
        - **Simple Plot**: 
            A single-source plot that does not require SPECS data. Used when no 
            `spec_data` is provided.
        
        - **Single Plot**: 
            A standard plot showing one data source per figure. This is the most 
            common type of map.

        - **Comparison Plot**: 
            A plot that includes two or more data sources. These can take the form of:
            
            - *Side-by-side plots*: Multiple plots shown next to each other.
            - *Overlay plots*: All data sources are plotted on a single set of axes 
              (usually for line plots); can include more than two data sources.
            - *Difference plots*: Visualize the difference between datasets.

        Notes
        -----
        The selection of which plot type to generate is controlled by the internal
        state of the configuration manager. This function delegates to private 
        helper methods corresponding to each plot type.
        """
        self.logger.info("Generate plots.")

        if not self.config_manager.spec_data:
            plotter = SimplePlotter()
            self.process_simple_plots(plotter)
        else:
            if self.config_manager.compare and not self.config_manager.compare_diff:
                self.process_side_by_side_plots()
            elif self.config_manager.compare_diff:
                self.process_comparison_plots()
            elif self.config_manager.overlay:
                self.process_side_by_side_plots()
            # TODO: Should be either single or comparison - not a separate category
            elif self.config_manager.correlation:
                self.process_corr_plots()
            else:
                has_corr = False
                for idx, params in self.config_manager.map_params.items():
                    plot_types = params.get('to_plot', ['xy'])
                    if isinstance(plot_types, str):
                        plot_types = [pt.strip() for pt in plot_types.split(',')]
                    if 'corr' in plot_types:
                        has_corr = True
                        break
                if has_corr:
                    self.process_corr_plots()
                else:
                    self.process_single_plots()

        if self.config_manager.print_to_file:
            output_dirs = []
            for i in range(len(self.config_manager.map_params)):
                if self.config_manager.compare or self.config_manager.compare_diff:
                    entry = u.get_nested_key_value(self.config_manager.map_params[i],
                                                   ['outputs', 'output_dir'])
                    if entry:
                        output_dirs.append(entry)
                    break
                else:
                    entry = u.get_nested_key_value(self.config_manager.map_params[i],
                                                   ['outputs', 'output_dir'])
                    if entry:
                        output_dirs.append(entry)
            if not output_dirs:
                output_dirs = [self.config.paths.output_path]

            unique_dirs = set(output_dirs)
            for dir_path in unique_dirs:
                self.logger.info(f"Output files are in {dir_path}")

        self.logger.info("Done.")

    def register_plot_type(self, field_name, plot_type):
        """Register the plot type for a field."""
        if not hasattr(self, '_plot_type_registry'):
            self._plot_type_registry = {}
        self._plot_type_registry[field_name] = plot_type
        
    def get_plot_type(self, field_name, default='xy'):
        """Get the plot type for a field."""
        if not hasattr(self, '_plot_type_registry'):
            self._plot_type_registry = {}
        return self._plot_type_registry.get(field_name, default)
    
    def create_plotter(self, field_name: str, plot_type: str, backend=None):
        """Create a plotter for the given field.
        
        Args:
            field_name: Name of the field to plot
            plot_type: Type of plot to create
            backend: Backend to use (defaults to config_manager.output_backend)
            
        Returns:
            An instance of the appropriate plotter
        """        
        try:
            return PlotterFactory.create_plotter(plot_type, backend)
        except ValueError as e:
            self.logger.error(f"Error creating plotter for {field_name}: {e}")
            return None
    
    def create_plot(self, field_name, data_to_plot, plot_type=None):
        """Create a plot using the appropriate plotter.
        
        Args:
            field_name: Name of the field to plot
            data_to_plot: Tuple containing plot data
            plot_type: Optional plot type to override registry lookup
            
        Returns:
            The created plot object
        """
        backend = getattr(self.config_manager, 'output_backend', 'matplotlib')
        
        if plot_type is None:
            plot_type = self.get_plot_type(field_name)
        plotter = self.create_plotter(field_name, plot_type, backend)
        if plotter is None:
            return None
        
        # Create and return the plot 
        return plotter.plot(self.config_manager, data_to_plot)
    

    def process_plot(self, data_array, field_name, file_index, plot_type):
        """Process a plot for the given field.
        
        This is a base implementation that delegates to subclass methods.
        Subclasses should implement the specific plot type methods.
        """
        self.register_plot_type(field_name, plot_type)
        
        figure = Figure.create_eviz_figure(self.config_manager, plot_type)
        self.config_manager.ax_opts = figure.init_ax_opts(field_name)
        
        # Delegate to the appropriate method based on plot type
        if plot_type == 'xy':
            if hasattr(self, '_process_xy_plot'):
                self._process_xy_plot(data_array, field_name, file_index, plot_type, figure)
            else:
                self.logger.warning(f"_process_xy_plot not implemented for {self.__class__.__name__}")
        elif plot_type == 'polar':
            if hasattr(self, '_process_polar_plot'):
                self._process_polar_plot(data_array, field_name, file_index, plot_type, figure)
            else:
                self.logger.warning(f"_process_polar_plot not implemented for {self.__class__.__name__}")
        elif plot_type == 'xt':
            if hasattr(self, '_process_xt_plot'):
                self._process_xt_plot(data_array, field_name, file_index, plot_type, figure)
            else:
                self.logger.warning(f"_process_xt_plot not implemented for {self.__class__.__name__}")
        elif plot_type == 'tx':
            if hasattr(self, '_process_tx_plot'):
                self._process_tx_plot(data_array, field_name, file_index, plot_type, figure)
            else:
                self.logger.warning(f"_process_tx_plot not implemented for {self.__class__.__name__}")
        elif plot_type == 'sc':
            if hasattr(self, '_process_scatter_plot'):
                self._process_scatter_plot(data_array, field_name, file_index, plot_type, figure)
            else:
                self.logger.warning(f"_process_scatter_plot not implemented for {self.__class__.__name__}")
        elif plot_type == 'corr':
            if hasattr(self, '_process_corr_plot'):
                self._process_corr_plot(data_array, field_name, file_index, plot_type, figure)
            else:
                self.logger.warning(f"_process_corr_plot not implemented for {self.__class__.__name__}")
        elif plot_type == 'box':
            if hasattr(self, '_process_box_plot'):
                self._process_box_plot(data_array, field_name, file_index, plot_type, figure)
            else:
                self.logger.warning(f"_process_box_plot not implemented for {self.__class__.__name__}")
        else:
            if hasattr(self, '_process_other_plot'):
                self._process_other_plot(data_array, field_name, file_index, plot_type, figure)
            else:
                self.logger.warning(f"_process_other_plot not implemented for {self.__class__.__name__}")

    def _is_observational_data(self, data_array):
        """
        Determine if the data array should be treated as observational data.
        
        This method checks various characteristics of the data to determine
        if it should be processed as observational data (e.g., swath format)
        or as standard gridded data.
        
        Args:
            data_array: The xarray DataArray to check
            
        Returns:
            bool: True if the data should be treated as observational
        """
        if data_array is None:
            return False
            
        # Check for characteristics of observational data
        try:
            # 2D coordinate arrays (common in swath data)
            for coord_name in data_array.coords:
                if ('lon' in coord_name.lower() or 'lat' in coord_name.lower()) and len(data_array[coord_name].shape) == 2:
                    return True
            
            # Irregular grid spacing
            xc_dim = self.config_manager.get_model_dim_name('xc') or 'lon'
            yc_dim = self.config_manager.get_model_dim_name('yc') or 'lat'
            
            if xc_dim in data_array.coords and yc_dim in data_array.coords:
                
                lon_vals = data_array[xc_dim].values
                if len(lon_vals) > 2:
                    lon_diffs = np.diff(lon_vals)  # Check if longitude spacing is regular
                    if not np.allclose(lon_diffs, lon_diffs[0], rtol=1e-3):
                        return True
                
                
                lat_vals = data_array[yc_dim].values
                if len(lat_vals) > 2:
                    lat_diffs = np.diff(lat_vals)  # Check if latitude spacing is regular
                    if not np.allclose(lat_diffs, lat_diffs[0], rtol=1e-3):
                        return True
            
            # Observational metadata (usually in attributes)
            for attr in ['platform', 'instrument', 'sensor', 'satellite']:
                if hasattr(data_array, attr) or attr in data_array.attrs:
                    return True
                    
            # Do we have limited geographical coverage (i.e., not global)?
            if xc_dim in data_array.coords and yc_dim in data_array.coords:
                lon_min, lon_max = np.nanmin(data_array[xc_dim]), np.nanmax(data_array[xc_dim])
                lat_min, lat_max = np.nanmin(data_array[yc_dim]), np.nanmax(data_array[yc_dim])
                
                # Hackish way to check...
                if (lon_max - lon_min < 300) or (lat_max - lat_min < 150):
                    return True
            
        except Exception as e:
            self.logger.debug(f"Error checking if data is observational: {e}")
        
        # Not gridded!
        return False

    def _get_filename_for_index(self, file_index: int) -> str:
        """
        Get the filename for a given file index.
        
        Args:
            file_index: The file index to look up
            
        Returns:
            str: The filename or None if not found
        """
        try:
            if file_index is not None and file_index < len(self.config_manager.app_data.inputs):
                file_entry = self.config_manager.app_data.inputs[file_index]
                return os.path.join(file_entry.get('location', ''),
                                    file_entry.get('name', ''))
        except (AttributeError, IndexError, TypeError):
            self.logger.debug(f"Could not get filename for file_index {file_index}")
        return None
    
    def _get_field(self, name, data):
        """
        Compatibility method for extracting fields from data.
        Added to maintain compatibility with any remaining legacy code.
        """
        try:
            return data[name]
        except Exception as e:
            self.logger.error(f'Field access error: {name} not found in data: {e}')
            return None

    def _get_data_extent(self, data_array):
        """
        Extract the geographical extent (bounding box) from an xarray DataArray.
        
        This method determines the geographical boundaries using the domain info
        from the ConfigManager or by analyzing the data array directly.
        
        Args:
            data_array: The data array to extract extent from
            
        Returns:
            list: The geographical extent as [lon_min, lon_max, lat_min, lat_max]
        """
        default_extent = [-180, 180, -90, 90]
        
        if data_array is None:
            self.logger.warning("Cannot extract extent from None data_array")
            return default_extent
        
        # First try to get extent from domain info
        domain_extent = self.config_manager.domain_extent
        if domain_extent is not None:
            return domain_extent
            
        # If domain info not available, extract directly from data array
        try:
            # Find coordinate names
            lon_coord_name = self.config_manager.longitude_coordinate_name
            lat_coord_name = self.config_manager.latitude_coordinate_name
            
            # Fall back to generic dimension names if domain info not available
            if not lon_coord_name:
                lon_coord_name = self.config_manager.get_model_dim_name('xc') or 'lon'
            if not lat_coord_name:
                lat_coord_name = self.config_manager.get_model_dim_name('yc') or 'lat'
            
            # Check if coordinates exist in the DataArray
            if lon_coord_name in data_array.coords and lat_coord_name in data_array.coords:
                lon_vals = data_array[lon_coord_name].values
                lat_vals = data_array[lat_coord_name].values
                
                lon_min = np.nanmin(lon_vals)
                lon_max = np.nanmax(lon_vals)
                lat_min = np.nanmin(lat_vals)
                lat_max = np.nanmax(lat_vals)
                
                # Add a small buffer (5% of range) around the extent for better visualization
                lon_buffer = (lon_max - lon_min) * 0.05
                lat_buffer = (lat_max - lat_min) * 0.05
                
                extent = [
                    lon_min - lon_buffer,
                    lon_max + lon_buffer,
                    lat_min - lat_buffer,
                    lat_max + lat_buffer
                ]
                
                self.logger.debug(f"Extracted extent: {extent}")
                return extent
                
        except Exception as e:
            self.logger.error(f"Error extracting extent: {e}")
        
        self.logger.warning("Could not determine extent, using default global extent")
        return default_extent

    def _prepare_field_to_plot(self, 
                               data_array: xr.DataArray, 
                               field_name: str,
                               file_index: int, 
                               plot_type: str, 
                               figure, 
                               time_level,
                               level=None,
                               global_vmin=None,
                               global_vmax=None) -> tuple:
        """Prepare the 2D data array and coordinates to be plotted."""
        dim1_name, dim2_name = self.config_manager.get_dim_names(plot_type)
        data2d = None

        self.logger.debug(f"Preparing data for: {field_name}, plot_type:{plot_type}, time_level:{time_level}, level:{level}")
        if 'xy' in plot_type or 'polar' in plot_type:
            data2d = self.data_extractor._extract_xy_data(data_array, time_level, level=level)
        elif 'yz' in plot_type:
            data2d = self.data_extractor._extract_yz_data(data_array, time_level)
        elif 'xt' in plot_type:
            data2d = self.data_extractor._extract_xt_data(data_array, time_level)
        elif 'tx' in plot_type:
            data2d = self.data_extractor._extract_tx_data(data_array, time_level, level=level)
        elif 'sc' in plot_type:
            data2d = self.data_extractor._extract_scatter_data(data_array, time_level)
        elif 'line' in plot_type:  # like xt but use in interactive backends
            data2d = self.data_extractor._extract_line_data(data_array, time_level, level=level)
        elif 'box' in plot_type:
            data2d = self.data_extractor._extract_box_data(data_array, time_level, 
                                            exp_id=self.config_manager.get_file_exp_id(file_index))
        elif 'corr' in plot_type:
            data2d = self.data_extractor._extract_corr_data(data_array, time_level, level=level)
        else:
            self.logger.warning(
                f"Unsupported plot type: {plot_type}")
            return None

        if data2d is None:
            self.logger.error(
                f"Failed to prepare 2D data for field {field_name}, plot type {plot_type}")
            return None

        # For these plot types, return without coordinates
        if plot_type in ['line', 'box', 'xt', 'tx']:
            return data2d, None, None, field_name, plot_type, file_index, figure, global_vmin, global_vmax
        elif plot_type in ['sc']:
            # Check if there's already a named extent configured (e.g., "conus", "global")
            current_extent = self.config_manager.ax_opts.get('extent')
            if not isinstance(current_extent, str):
                # Only override extent if no named extent is configured
                extent = self._get_data_extent(data_array)
                self.config_manager.ax_opts['extent'] = extent
                
            self.config_manager.ax_opts['central_lon'] = self.config_manager.central_longitude
            self.config_manager.ax_opts['central_lat'] = self.config_manager.central_latitude
            return data2d[0], data2d[1], data2d[2], field_name, plot_type, file_index, figure

        # Process coordinates based on domain type
        try:
            # Get the current filename for domain lookup
            current_filename = self._get_filename_for_index(file_index)
            
            # If we can't get filename from file_index, try using config_manager's filename
            if not current_filename and hasattr(self.config_manager, 'current_field_name'):
                # Try to get filename from map_params using current field
                for idx, params in self.config_manager.map_params.items():
                    if params.get('field') == field_name:
                        current_filename = params.get('filename')
                        break
            
            domain_info = self.config_manager.get_domain_info(current_filename)
            is_regional = domain_info.get('is_regional', False)
            
            if is_regional:
                if hasattr(self, '_process_coordinates'):
                    self.logger.debug(f"Calling self._process_coordinates for {field_name}")
                    return self._process_coordinates(data2d, 
                                                     dim1_name, dim2_name,
                                                     field_name,
                                                     plot_type, file_index, figure)
                else:                    
                    # Use domain extent from domain_info if available
                    extent = domain_info.get('extent')
                    if extent:
                        lonW, lonE, latS, latN = extent
                        self.config_manager.ax_opts['extent'] = extent
                        self.config_manager.ax_opts['central_lon'] = domain_info.get('central_lon', (lonW + lonE) / 2)
                        self.config_manager.ax_opts['central_lat'] = domain_info.get('central_lat', (latS + latN) / 2)
                        self.logger.debug(f"Using domain extent: {extent}")
                        
                        # Create coordinate arrays for the plot (using data2d dimensions)
                        if hasattr(data2d, 'coords'):
                            # Try to get coordinate arrays from the data
                            lon_coord_name = domain_info.get('lon_coords', 'lon')
                            lat_coord_name = domain_info.get('lat_coords', 'lat')
                            
                            if lon_coord_name in data2d.coords and lat_coord_name in data2d.coords:
                                lon_coords = data2d.coords[lon_coord_name]
                                lat_coords = data2d.coords[lat_coord_name]
                                
                                # For 2D coordinates (like WRF), extract 1D arrays
                                if len(lon_coords.dims) == 2:
                                    xs = np.array(lon_coords.isel({lon_coords.dims[0]: 0}))
                                    ys = np.array(lat_coords.isel({lat_coords.dims[1]: 0}))
                                else:
                                    xs = np.array(lon_coords)
                                    ys = np.array(lat_coords)
                            else:
                                # Fallback: create linear coordinate arrays from extent
                                n_lon = data2d.shape[-1] if data2d.ndim >= 2 else 100
                                n_lat = data2d.shape[-2] if data2d.ndim >= 2 else 100
                                xs = np.linspace(lonW, lonE, n_lon)
                                ys = np.linspace(latS, latN, n_lat)
                        else:
                            # Final fallback: create coordinate arrays from extent
                            xs = np.linspace(lonW, lonE, 100)
                            ys = np.linspace(latS, latN, 100)
                            
                        self.logger.debug(f"Extent: {self.config_manager.ax_opts['extent']} ")
                        return data2d, xs, ys, field_name, plot_type, file_index, figure, global_vmin, global_vmax
                    else:
                        self.logger.warning(f"No domain extent available for regional data {field_name}")
                        # Fall back to non-regional processing by setting is_regional to False
                        is_regional = False
            else:
                if figure.ax_opts['extent']:
                    extent = figure.ax_opts['extent']
                    if extent == 'conus':
                        extent = [-120, -70, 24, 50.5]
                    data2d = subset_region(data2d, extent)
                x = data2d[dim1_name].values if dim1_name in data2d.coords else None
                y = data2d[dim2_name].values if dim2_name in data2d.coords else None

                if x is None or y is None:
                    dims = list(data2d.dims)
                    if len(dims) >= 2:
                        x = data2d[dims[0]].values
                        y = data2d[dims[1]].values
                    else:
                        self.logger.error(
                            "Dataset has fewer than 2 dimensions, cannot plot")
                        return None

                if np.isnan(data2d.values).all():
                    self.logger.error(
                        f"All values are NaN for {field_name}. Using original data.")
                    data2d = data_array.squeeze()
                elif np.isnan(data2d.values).any():
                    self.logger.debug(
                        f"Note: Some NaN values present ({np.sum(np.isnan(data2d.values))} NaNs).")
                    # data2d = data2d.fillna(0)

                return data2d, x, y, field_name, plot_type, file_index, figure, global_vmin, global_vmax

        except Exception as e:
            import traceback
            self.logger.error(f"Error processing coordinates for {field_name}: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _set_time_config(self, time_index, data_var):
        """Set time-related configuration values."""
        self.config_manager.time_level = time_index

        try:
            if 'time' in data_var.coords:
                if isinstance(time_index, int) and time_index < len(data_var.coords['time']):
                    real_time = data_var.coords['time'].values[time_index]
                    real_time_readable = pd.to_datetime(real_time).strftime('%Y-%m-%d %H')
                    self.config_manager.real_time = real_time_readable
                else:
                    self.config_manager.real_time = f"Time level {time_index}"
            else:
                # If 'time' is not a coordinate, try to find a time-like coordinate
                time_coords = [coord for coord in data_var.coords if
                               'time' in coord.lower()]
                if time_coords:
                    time_coord = time_coords[0]
                    if isinstance(time_index, int) and time_index < len(
                            data_var.coords[time_coord]):
                        real_time = data_var.coords[time_coord].values[time_index]
                        real_time_readable = pd.to_datetime(real_time).strftime(
                            '%Y-%m-%d %H')
                        self.config_manager.real_time = real_time_readable
                    else:
                        self.config_manager.real_time = f"Time level {time_index}"
                else:
                    self.config_manager.real_time = f"Time level {time_index}"
        except Exception as e:
            self.config_manager.real_time = f"Time level {time_index}"

    def process_simple_plots(self, plotter):
        """Generate simple plots."""
        self.logger.info("Generating simple plots")
        
        # Get data sources
        all_data_sources_dict = self.config_manager.pipeline.get_all_data_sources()
        if not all_data_sources_dict:
            self.logger.error("No data sources available for simple plots")
            return
        
        all_data_sources = list(all_data_sources_dict.values())
        self.logger.debug(f"Found {len(all_data_sources)} data sources")
            
        # Process each input file and its to_plot fields
        for input_entry in self.config_manager.app_data.inputs:
            to_plot = input_entry.get('to_plot', {})
            
            for field_name, plot_type in to_plot.items():
                self.logger.info(f"Processing simple plot: {field_name} ({plot_type})")
                
                # Get the data from data sources
                data = None
                for i, data_source in enumerate(all_data_sources):
                    self.logger.debug(f"Checking data source {i}: {type(data_source)}")
                    
                    # Check different ways the dataset might be stored
                    dataset = None
                    if hasattr(data_source, 'dataset') and data_source.dataset is not None:
                        dataset = data_source.dataset
                        self.logger.debug(f"Found dataset via .dataset attribute")
                    elif hasattr(data_source, 'data') and data_source.data is not None:
                        dataset = data_source.data
                        self.logger.debug(f"Found dataset via .data attribute")
                    elif hasattr(data_source, '__dict__'):
                        # Check if it's a dictionary-like structure with datasets
                        for key, value in data_source.__dict__.items():
                            if isinstance(value, xr.Dataset):
                                dataset = value
                                self.logger.debug(f"Found dataset via .{key} attribute")
                                break
                    
                    if dataset is not None:
                        self.logger.debug(f"Dataset has {len(dataset.data_vars)} data variables")
                        self.logger.debug(f"Available variables: {list(dataset.data_vars.keys())[:10]}...")
                        
                        if field_name in dataset.data_vars:
                            data = dataset[field_name]
                            self.logger.debug(f"Found field '{field_name}' in data source {i}")
                            break
                        elif field_name in dataset.variables:
                            data = dataset[field_name] 
                            self.logger.debug(f"Found field '{field_name}' in variables of data source {i}")
                            break
                    else:
                        self.logger.debug(f"No dataset found in data source {i}")
                
                if data is not None:
                    try:
                        self.logger.info(f"Creating simple {plot_type} plot for {field_name}")
                        plotter.plot(self.config_manager, field_name, plot_type, data)
                    except Exception as e:
                        self.logger.error(f"Failed to create simple plot for {field_name}: {str(e)}")
                        import traceback
                        self.logger.debug(traceback.format_exc())
                else:
                    self.logger.warning(f"Field '{field_name}' not found in any data source")
                    # Additional debugging
                    self.logger.debug("Debug info:")
                    for i, ds in enumerate(all_data_sources):
                        if hasattr(ds, 'dataset') and ds.dataset is not None:
                            self.logger.debug(f"  Data source {i} has {len(ds.dataset.data_vars)} variables")
                        else:
                            self.logger.debug(f"  Data source {i} has no dataset or dataset is None")

    def process_single_plots(self):
        """Generate single plots."""
        self.logger.info("Generating single plots")

        if not self.config_manager.map_params:
            self.logger.error(
                "No map_params available for plotting. Check your YAML configuration.")
            return

        all_data_sources = self.config_manager.pipeline.get_all_data_sources()
        if not all_data_sources:
            self.logger.error(
                "No data sources available. Check your YAML configuration and ensure data files exist.")
            self.logger.info(
                "Map parameters found but no data sources loaded. Here are the expected files:")

            for i, entry in enumerate(self.config_manager.app_data.inputs):
                file_path = os.path.join(entry.get('location', ''), entry.get('name', ''))
                print(f"  {i + 1}. {file_path}")
            return

        for idx, params in self.config_manager.map_params.items():
            field_name = params.get('field')
            if not field_name:
                continue
            self.config_manager.current_field_name = field_name

            filename = params.get('filename')
            self.config_manager.findex = self.config_manager.get_file_index_by_filename(filename)

            data_source = self.config_manager.pipeline.get_data_source(filename)
            if not data_source:
                self.logger.warning(f"No data source found in pipeline for {filename}")
                continue

            # Extract domain information from the dataset
            if hasattr(data_source, 'dataset') and data_source.dataset is not None:
                self.config_manager.set_domain_info(data_source.dataset, filename)

            if hasattr(data_source, 'dataset') and data_source.dataset is not None:
                field_data = data_source.dataset.get(field_name)
            else:
                field_data = None

            if field_data is None:
                self.logger.warning(
                    f"Field {field_name} not found in data source for {filename}")
                continue

            field_data_array = data_source.dataset[field_name]
            plot_types = params.get('to_plot', ['xy'])
            if isinstance(plot_types, str):
                plot_types = [pt.strip() for pt in plot_types.split(',')]
            for plot_type in plot_types:
                self.logger.info(f"Plotting {field_name}, {plot_type} plot")
                self.process_plot(field_data_array, field_name, idx, plot_type)

        if self.config_manager.make_gif:
            pu.create_gif(self.config_manager)

    def process_comparison_plots(self):
        """Generate comparison plots for paired data sources according to configuration.
        """
        self.logger.info("Generating comparison plots")
        current_field_index = 0
        self.data2d_list = []

        all_data_sources = self.config_manager.pipeline.get_all_data_sources()
        if not all_data_sources:
            self.logger.error("No data sources available for comparison plotting.")
            return

        if not self.config_manager.a_list or not self.config_manager.b_list:
            self.logger.error("a_list or b_list is empty, cannot perform comparison.")
            return

        idx1 = self.config_manager.a_list[0]
        idx2 = self.config_manager.b_list[0]

        # Gather all unique field names from map_params for these files
        fields_file1 = [params['field'] for i, params in
                        self.config_manager.map_params.items() if
                        params['file_index'] == idx1]
        fields_file2 = [params['field'] for i, params in
                        self.config_manager.map_params.items() if
                        params['file_index'] == idx2]

        # Pair fields by order, not by name
        num_pairs = min(len(fields_file1), len(fields_file2))
        field_pairs = list(zip(fields_file1[:num_pairs], fields_file2[:num_pairs]))

        for field1, field2 in field_pairs:
            # Find map_params for this field in both files
            idx1_field = next((i for i, params in self.config_manager.map_params.items()
                               if params['file_index'] == idx1 and params[
                                   'field'] == field1), None)
            idx2_field = next((i for i, params in self.config_manager.map_params.items()
                               if params['file_index'] == idx2 and params[
                                   'field'] == field2), None)
            if idx1_field is None or idx2_field is None:
                continue

            self.config_manager.current_field_name = field1

            map1_params = self.config_manager.map_params[idx1_field]
            map2_params = self.config_manager.map_params[idx2_field]

            filename1 = map1_params.get('filename')
            filename2 = map2_params.get('filename')

            data_source1 = self.config_manager.pipeline.get_data_source(filename1)
            data_source2 = self.config_manager.pipeline.get_data_source(filename2)

            if not data_source1 or not data_source2:
                continue

            sdat1_dataset = data_source1.dataset if hasattr(data_source1,
                                                            'dataset') else None
            sdat2_dataset = data_source2.dataset if hasattr(data_source2,
                                                            'dataset') else None

            if sdat1_dataset is None or sdat2_dataset is None:
                continue

            # Extract domain information from the datasets
            if sdat1_dataset is not None:
                self.config_manager.set_domain_info(sdat1_dataset, filename1)
            if sdat2_dataset is not None:
                self.config_manager.set_domain_info(sdat2_dataset, filename2)

            file_indices = (map1_params['file_index'], map2_params['file_index'])

            self.field_names = (field1, field2)

            # Assuming plot types are the same for comparison
            plot_types = map1_params.get('to_plot', ['xy'])
            if isinstance(plot_types, str):
                plot_types = [pt.strip() for pt in plot_types.split(',')]
            for plot_type in plot_types:
                self.logger.info(f"Plotting {field1} vs {field2}, {plot_type} plot")

                if 'xy' in plot_type or 'po' in plot_type or 'polar' in plot_type:
                    self._process_xy_comparison_plots(file_indices,
                                                      current_field_index,
                                                      field1, field2, plot_type,
                                                      sdat1_dataset, sdat2_dataset)
                else:
                    self._process_other_comparison_plots(file_indices,
                                                         current_field_index,
                                                         field1, field2,
                                                         plot_type, sdat1_dataset,
                                                         sdat2_dataset)
                # Important: Reset for next plot
                self.data2d_list = []

            current_field_index += 1

    def process_side_by_side_plots(self):
        """
        Generate side-by-side comparison plots for the given plotter.
        """
        self.logger.info("Generating side-by-side comparison plots")
        current_field_index = 0
        self.data2d_list = []

        # Get the file indices for the two files being compared
        if not self.config_manager.a_list or not self.config_manager.b_list:
            self.logger.error(
                "a_list or b_list is empty, cannot perform side-by-side comparison.")
            return

        idx1 = self.config_manager.a_list[0]
        idx2 = self.config_manager.b_list[0]

        # Gather all unique field names from map_params for these files
        fields_file1 = [params['field'] for i, params in
                        self.config_manager.map_params.items() if
                        params['file_index'] == idx1]
        fields_file2 = [params['field'] for i, params in
                        self.config_manager.map_params.items() if
                        params['file_index'] == idx2]

        # Pair fields by order, not by name
        num_pairs = min(len(fields_file1), len(fields_file2))
        field_pairs = list(zip(fields_file1[:num_pairs], fields_file2[:num_pairs]))

        for field1, field2 in field_pairs:
            # Find map_params for this field in both files
            idx1_field = next((i for i, params in self.config_manager.map_params.items()
                               if params['file_index'] == idx1 and params[
                                   'field'] == field1), None)
            idx2_field = next((i for i, params in self.config_manager.map_params.items()
                               if params['file_index'] == idx2 and params[
                                   'field'] == field2), None)
            if idx1_field is None or idx2_field is None:
                continue

            self.config_manager.current_field_name = field1
            
            map1_params = self.config_manager.map_params[idx1_field]
            map2_params = self.config_manager.map_params[idx2_field]

            filename1 = map1_params.get('filename')
            filename2 = map2_params.get('filename')

            data_source1 = self.config_manager.pipeline.get_data_source(filename1)
            data_source2 = self.config_manager.pipeline.get_data_source(filename2)

            if not data_source1 or not data_source2:
                continue

            sdat1_dataset = data_source1.dataset if hasattr(data_source1,
                                                            'dataset') else None
            sdat2_dataset = data_source2.dataset if hasattr(data_source2,
                                                            'dataset') else None

            if sdat1_dataset is None or sdat2_dataset is None:
                continue

            # Extract domain information from the datasets
            if sdat1_dataset is not None:
                self.config_manager.set_domain_info(sdat1_dataset, filename1)
            if sdat2_dataset is not None:
                self.config_manager.set_domain_info(sdat2_dataset, filename2)

            self.file_indices = (map1_params['file_index'], map2_params['file_index'])

            self.field_names = (field1, field2)

            plot_types = map1_params.get('to_plot', ['xy'])
            if isinstance(plot_types, str):
                plot_types = [pt.strip() for pt in plot_types.split(',')]

            for plot_type in plot_types:
                self.logger.info(f"Plotting {field1}, {plot_type} plot")
                self.data2d_list = []
                if 'xy' in plot_type or 'polar' in plot_type:
                    self._process_xy_side_by_side_plots(current_field_index,
                                                        field1, 
                                                        field2,
                                                        plot_type,
                                                        sdat1_dataset, 
                                                        sdat2_dataset)
                elif 'corr' in plot_type:
                    self._process_corr_plots(current_field_index,
                                                        field1, 
                                                        field2,
                                                        plot_type,
                                                        sdat1_dataset, 
                                                        sdat2_dataset)
                elif 'box' in plot_type:
                    self._process_box_plots(current_field_index,
                                                        field1, 
                                                        field2,
                                                        plot_type,
                                                        sdat1_dataset, 
                                                        sdat2_dataset)
                else:
                    self._process_other_side_by_side_plots(current_field_index,
                                                           field1, 
                                                           field2,
                                                           plot_type, 
                                                           sdat1_dataset,
                                                           sdat2_dataset)
                self.data2d_list = []
            current_field_index += 1

    def process_corr_plots(self):
        """Generate correlation plots."""
        self.logger.info("Generating correlation plots")

        if not self.config_manager.map_params:
            self.logger.error(
                "No map_params available for plotting. Check your YAML configuration.")
            return

        all_data_sources = self.config_manager.pipeline.get_all_data_sources()
        if not all_data_sources:
            self.logger.error(
                "No data sources available. Check your YAML configuration and ensure data files exist.")
            return

        # Get corr plot settings from for_inputs
        corr_settings = {}
        if self.config_manager.correlation:
            corr_settings = self.config_manager.app_data.for_inputs['correlation']
        else:
            return

        # We're using experiment IDs for correlation
        if 'ids' in corr_settings:
            ids_str = corr_settings.get('ids', '')
            corr_ids = [id.strip() for id in ids_str.split(',') if id.strip()]
            
            if len(corr_ids) != 2:
                self.logger.error(f"Expected exactly 2 experiment IDs for correlation, got {len(corr_ids)}: {corr_ids}")
                return
                
            # Find file indices for these experiment IDs
            file_indices = []
            for exp_id in corr_ids:
                file_indices.append(self.config_manager.get_file_index(exp_id))
            
            if len(file_indices) != 2:
                self.logger.error(f"Could not find file indices for both experiment IDs: {corr_ids}")
                return
                
            # Get the fields from each file index
            field_names = []
            for idx in file_indices:
                fields = [params.get('field') for i, params in 
                        self.config_manager.map_params.items() if 
                        params.get('file_index') == idx]
                if fields:
                    field_names.append(fields[0])  # Use the first field from each experiment
            
            if len(field_names) != 2:
                self.logger.error("Could not find fields for both experiment IDs")
                return
                
            # Process each field pair
            for i, file_idx in enumerate(file_indices):
                field_name = field_names[i]
                params = next((p for _, p in self.config_manager.map_params.items() 
                            if p.get('file_index') == file_idx and p.get('field') == field_name), None)
                
                if params:
                    self.config_manager.current_field_name = field_name
                    filename = params.get('filename')
                    self.config_manager.findex = file_idx
                    
                    data_source = self.config_manager.pipeline.get_data_source(filename)
                    if data_source and hasattr(data_source, 'dataset') and field_name in data_source.dataset:
                        field_data_array = data_source.dataset[field_name]
                        plot_types = params.get('to_plot', ['corr'])
                        
                        if isinstance(plot_types, str):
                            plot_types = [pt.strip() for pt in plot_types.split(',')]
                            
                        for plot_type in plot_types:
                            if plot_type == 'corr':
                                self.logger.info(f"Plotting {field_name}, {plot_type} plot")
                                # For correlation plots, we need to use the model object, not just the data source
                                self.logger.debug(f"Data source type: {type(data_source).__name__}")
                                self.logger.debug(f"Data source has process_plot: {hasattr(data_source, 'process_plot')}")
                                
                                # Get the model name from config manager
                                model_name = getattr(data_source, 'model_name', None)
                                if model_name:
                                    from eviz.lib.models.factory import DataSourceFactory
                                    model_factory = DataSourceFactory()
                                    try:
                                        # Create the model object for correlation processing
                                        model_obj = model_factory.create(model_name, self.config_manager)
                                        if hasattr(model_obj, 'process_plot'):
                                            self.logger.info(f"Using model object ({type(model_obj).__name__}) process_plot method")
                                            model_obj.process_plot(field_data_array, field_name, file_idx, plot_type)
                                        else:
                                            self.logger.warning(f"Model object {type(model_obj).__name__} doesn't have process_plot method")
                                            self.process_plot(field_data_array, field_name, file_idx, plot_type)
                                    except Exception as e:
                                        self.logger.warning(f"Failed to create model object for {model_name}: {e}")
                                        import traceback
                                        self.logger.debug(f"Full traceback: {traceback.format_exc()}")
                                        self.process_plot(field_data_array, field_name, file_idx, plot_type)
                                else:
                                    self.logger.info(f"No model name found, falling back to plot manager process_plot method")
                                    self.process_plot(field_data_array, field_name, file_idx, plot_type)
                                
                        # Only need to process one of the fields for correlation
                        break
        else:
            # Get the fields to correlate
            fields_str = corr_settings.get('fields', '')
            corr_fields = [f.strip() for f in fields_str.split(',') if f.strip()]
            
            if len(corr_fields) != 2:
                self.logger.error(f"Expected exactly 2 fields for correlation, got {len(corr_fields)}: {corr_fields}")
                return
            
            processed_pairs = set()
            
            # Process each field in the map_params
            for idx, params in self.config_manager.map_params.items():
                field_name = params.get('field')
                if not field_name:
                    continue
                    
                if field_name not in corr_fields:
                    continue
                
                # Find the reference field (the other field in the correlation pair)
                reference_field = None
                if field_name == corr_fields[0]:
                    reference_field = corr_fields[1]
                else:
                    reference_field = corr_fields[0]
                
                # Create a unique id for this field pair (sorted to ensure consistency)
                pair_id = tuple(sorted([field_name, reference_field]))
                
                if pair_id in processed_pairs:
                    continue
                
                processed_pairs.add(pair_id)
                    
                self.config_manager.current_field_name = field_name
                
                filename = params.get('filename')
                self.config_manager.findex = self.config_manager.get_file_index_by_filename(filename)
                
                data_source = self.config_manager.pipeline.get_data_source(filename)
                if not data_source:
                    self.logger.warning(f"No data source found in pipeline for {filename}")
                    continue
                    
                if hasattr(data_source, 'dataset') and data_source.dataset is not None:
                    field_data = data_source.dataset.get(field_name)
                else:
                    field_data = None
                    
                if field_data is None:
                    self.logger.warning(f"Field {field_name} not found in data source for {filename}")
                    continue
                    
                field_data_array = data_source.dataset[field_name]
                plot_types = params.get('to_plot', ['corr'])
                
                if isinstance(plot_types, str):
                    plot_types = [pt.strip() for pt in plot_types.split(',')]
                    
                for plot_type in plot_types:
                    if plot_type == 'corr':
                        self.logger.info(f"Plotting {field_name}, {plot_type} plot")
                        # For correlation plots, we need to use the model object, not just the data source
                        model_name = getattr(data_source, 'model_name', None)
                        if model_name:
                            from eviz.lib.models.factory import DataSourceFactory
                            model_factory = DataSourceFactory()
                            try:
                                # Create the model object for correlation processing
                                model_obj = model_factory.create(model_name, self.config_manager)
                                if hasattr(model_obj, 'process_plot'):
                                    self.logger.info(f"Using model object ({type(model_obj).__name__}) process_plot method")
                                    model_obj.process_plot(field_data_array, field_name, idx, plot_type)
                                else:
                                    self.logger.warning(f"Model object {type(model_obj).__name__} doesn't have process_plot method")
                                    self.process_plot(field_data_array, field_name, idx, plot_type)
                            except Exception as e:
                                self.logger.warning(f"Failed to create model object for {model_name}: {e}")
                                self.process_plot(field_data_array, field_name, idx, plot_type)
                        else:
                            self.logger.info(f"No model name found, falling back to plot manager process_plot method")
                            self.process_plot(field_data_array, field_name, idx, plot_type)

    def _process_xy_plot(self, 
                         data_array: xr.DataArray, 
                         field_name: str, 
                         file_index: int, 
                         plot_type: str, 
                         figure: Figure):
        """Process an XY plot."""
        levels = self.config_manager.get_levels(field_name, plot_type + 'plot')
        do_zsum = self.config_manager.ax_opts.get('zsum', False)

        time_level_config = self.config_manager.ax_opts.get('time_lev', 0)
        tc_dim = self.config_manager.get_model_dim_name('tc') or 'time'
        zc_dim = self.config_manager.get_model_dim_name_for_data('zc', data_array) or 'lev'
        num_times = data_array[tc_dim].size if tc_dim in data_array.dims else 1
        time_levels = range(num_times) if time_level_config == 'all' else [time_level_config]

        if not levels and not do_zsum:
            return

        # Calculate global min/max for consistent colorbar if creating a GIF
        global_vmin = None
        global_vmax = None
        if self.config_manager.make_gif and len(time_levels) > 1:
            self.logger.info(f"Calculating global colorbar range for GIF consistency across {len(time_levels)} time frames")
            global_vmin, global_vmax = self._calculate_global_minmax(data_array, 
                                                                    field_name, 
                                                                    time_levels, 
                                                                    levels, 
                                                                    tc_dim, 
                                                                    zc_dim)
            if global_vmin is not None and global_vmax is not None:
                self.logger.info(f"Using consistent colorbar range [{global_vmin:.2f}, {global_vmax:.2f}] for all {len(time_levels)} frames")

        self._process_level_plot(data_array, 
                                 field_name, 
                                 file_index, 
                                 plot_type, 
                                 figure, 
                                 time_levels, 
                                 levels, 
                                 global_vmin, 
                                 global_vmax)

    def _calculate_global_minmax(self, data_array, field_name, time_levels, levels, tc_dim, zc_dim):
        """Calculate global min/max values across all time frames for consistent GIF colorbar."""
        global_min = float('inf')
        global_max = float('-inf')
        
        has_vertical_dim = zc_dim and zc_dim in data_array.dims
        
        for level_val in levels.keys():
            for t in time_levels:
                # Extract data at this time step (same logic as in _process_level_plot)
                if tc_dim in data_array.dims:
                    data_at_time = data_array.isel({tc_dim: t})
                else:
                    data_at_time = data_array.squeeze()
                
                if np.isnan(data_at_time).all():
                    continue
                
                # Apply the same data extraction as in _prepare_field_to_plot
                if not has_vertical_dim:
                    data2d = self.data_extractor._extract_xy_data(data_at_time, 0, level=level_val)
                else:
                    data2d = self.data_extractor._extract_xy_data(data_at_time, 0, level=level_val)
                
                if data2d is not None and not np.isnan(data2d).all():
                    field_min = np.nanmin(data2d)
                    field_max = np.nanmax(data2d)
                    
                    if not np.isnan(field_min) and not np.isnan(field_max):
                        global_min = min(global_min, field_min)
                        global_max = max(global_max, field_max)
        
        # Handle case where no valid data was found
        if global_min == float('inf') or global_max == float('-inf'):
            return None, None
            
        return float(global_min), float(global_max)

    def _process_level_plot(self, 
                            data_array, 
                            field_name, 
                            file_index, 
                            plot_type, 
                            figure, 
                            time_levels, 
                            levels, 
                            global_vmin=None, 
                            global_vmax=None):
        """Process plots for specific vertical levels."""
        self.logger.debug("Processing XY level plots")
        # Use the new method that checks against the actual data_array dimensions
        zc_dim = self.config_manager.get_model_dim_name_for_data('zc', data_array) or 'lev'
        tc_dim = self.config_manager.get_model_dim_name_for_data('tc', data_array) or 'time'

        has_vertical_dim = zc_dim and zc_dim in data_array.dims
        self.config_manager.level = None
        for level_val in levels.keys():
            self.config_manager.level = level_val
            for t in time_levels:
                self.logger.debug(f"Processing time level {t} for field {field_name}, level {level_val}")
                if tc_dim in data_array.dims:
                    data_at_time = data_array.isel({tc_dim: t})
                else:
                    data_at_time = data_array.squeeze()  # Assume single time if no time dim
                
                if np.isnan(data_at_time).all():
                    self.logger.debug(f"Skipping time level {t} for {field_name} - all values are NaN")
                    continue
                    
                self._set_time_config(t, data_at_time)
                # Create a new figure for each level to avoid reusing axes
                figure = Figure.create_eviz_figure(self.config_manager, plot_type)
                self.config_manager.ax_opts = figure.init_ax_opts(field_name)

                # If the data doesn't have a vertical dimension, we can't select a level
                # In this case, we'll just use the data as is
                if not has_vertical_dim:
                    field_to_plot = self._prepare_field_to_plot(data_at_time, 
                                                                field_name, 
                                                                file_index, 
                                                                plot_type, 
                                                                figure, 
                                                                time_level=t,
                                                                global_vmin=global_vmin,
                                                                global_vmax=global_vmax)
                else:
                    field_to_plot = self._prepare_field_to_plot(data_at_time, 
                                                                field_name, 
                                                                file_index, 
                                                                plot_type, 
                                                                figure, 
                                                                time_level=t, 
                                                                level=level_val,
                                                                global_vmin=global_vmin,
                                                                global_vmax=global_vmax)

                if field_to_plot and not np.isnan(field_to_plot[0]).all():
                    plot_result = self.create_plot(field_name, field_to_plot)                    
                    pu.print_map(self.config_manager, 
                                 plot_type, 
                                 self.config_manager.findex, 
                                 plot_result, 
                                 level=level_val)
                else:
                    self.logger.warning(f"Skipping plot for time level {t} - no valid data after processing")

    def _process_xt_plot(self, data_array, field_name, file_index, plot_type, figure):
        """Process an XT (time series) plot."""
        self.logger.debug(f"Processing XT plot for {field_name}")
        
        self.config_manager.level = None
        time_level_config = self.config_manager.ax_opts.get('time_lev', 0)
        tc_dim = self.config_manager.get_model_dim_name('tc') or 'time'

        if tc_dim in data_array.dims:
            num_times = data_array[tc_dim].size
            time_levels = range(num_times) if time_level_config == 'all' else [time_level_config]
        else:
            time_levels = [0]

        field_to_plot = self._prepare_field_to_plot(data_array, 
                                                    field_name, 
                                                    file_index, 
                                                    plot_type, 
                                                    figure, 
                                                    time_level=time_level_config)
        
        if field_to_plot:
            plot_result = self.create_plot(field_name, field_to_plot)
            pu.print_map(self.config_manager, 
                         plot_type, 
                         self.config_manager.findex, 
                         plot_result)

    def _process_tx_plot(self, data_array, field_name, file_index, plot_type, figure):
        """Process a TX (Hovmoller) plot."""
        self.logger.debug(f"Processing TX plot for {field_name}")
        
        self.config_manager.level = None
        time_level_config = self.config_manager.ax_opts.get('time_lev', 0)
        tc_dim = self.config_manager.get_model_dim_name('tc') or 'time'

        if tc_dim in data_array.dims:
            num_times = data_array[tc_dim].size
            time_levels = range(num_times) if time_level_config == 'all' else [time_level_config]
        else:
            time_levels = [0]

        field_to_plot = self._prepare_field_to_plot(data_array, 
                                                    field_name, 
                                                    file_index, 
                                                    plot_type, 
                                                    figure, 
                                                    time_level=time_level_config)
        
        if field_to_plot:
            plot_result = self.create_plot(field_name, field_to_plot)
            pu.print_map(self.config_manager, 
                         plot_type, 
                         self.config_manager.findex, 
                         plot_result)

    def _process_polar_plot(self, data_array, field_name, file_index, plot_type, figure):
        """Process polar plots for specific vertical levels."""
        self.logger.debug(f"Processing polar plot for {field_name}")
        
        levels = self.config_manager.get_levels(field_name, plot_type + 'plot')
        do_zsum = self.config_manager.ax_opts.get('zsum', False)

        time_level_config = self.config_manager.ax_opts.get('time_lev', 0)
        tc_dim = self.config_manager.get_model_dim_name('tc') or 'time'
        num_times = data_array[tc_dim].size if tc_dim in data_array.dims else 1
        time_levels = range(num_times) if time_level_config == 'all' else [time_level_config]

        if not levels and not do_zsum:
            return
        
        self.logger.debug(f' -> Processing {len(time_levels)} time levels')
        zc_dim = self.config_manager.get_model_dim_name('zc') or 'lev'
        tc_dim = self.config_manager.get_model_dim_name('tc') or 'time'

        has_vertical_dim = zc_dim and zc_dim in data_array.dims

        for level_val in levels.keys():
            self.config_manager.level = level_val
            for t in time_levels:
                if tc_dim in data_array.dims:
                    data_at_time = data_array.isel({tc_dim: t})
                else:
                    data_at_time = data_array.squeeze()

                field_to_plot = self._prepare_field_to_plot(data_at_time,
                                                            field_name,
                                                            file_index,
                                                            plot_type,
                                                            figure,
                                                            time_level=t,
                                                            level=level_val)
                if field_to_plot:
                    plot_result = self.create_plot(field_name, field_to_plot)
                    pu.print_map(self.config_manager,
                                 plot_type,
                                 self.config_manager.findex,
                                 plot_result,
                                 level=level_val)
                else:
                    self.logger.warning(f"Skipping plot for time level {t} - no valid data after processing")

    def _process_other_plot(self, data_array, field_name, file_index, plot_type, figure):
        """Process non-xy and non-polar plot types."""
        self.logger.debug(f"Processing other plot type '{plot_type}' for {field_name}")
        
        self.config_manager.level = None
        time_level_config = self.config_manager.ax_opts.get('time_lev', 0)
        tc_dim = self.config_manager.get_model_dim_name('tc') or 'time'

        if tc_dim in data_array.dims:
            num_times = data_array[tc_dim].size
            # TODO: Handle yx_plot Gifs
            time_levels = range(num_times) if time_level_config == 'all' else [time_level_config]
        else:
            time_levels = [0]


        field_to_plot = self._prepare_field_to_plot(data_array, 
                                                    field_name, 
                                                    file_index,
                                                    plot_type, 
                                                    figure,
                                                    time_level=time_level_config)
        if field_to_plot:
            plot_result = self.create_plot(field_name, field_to_plot)
            pu.print_map(self.config_manager, 
                         plot_type, 
                         self.config_manager.findex, 
                         plot_result)

    def _process_zsum_plot(self, data_array, field_name, file_index, plot_type, figure, time_levels):
        """Process plots with vertical summation."""
        self.logger.debug(f"Processing zsum plot for {field_name}")
        
        self.config_manager.level = None
        tc_dim = self.config_manager.get_model_dim_name('tc') or 'time'
        zc_dim = self.config_manager.get_model_dim_name('zc') or 'lev'

        if not zc_dim or zc_dim not in data_array.dims:
            data_array = data_array.squeeze()

        for t in time_levels:
            if tc_dim in data_array.dims:
                data_at_time = data_array.isel({tc_dim: t})
            else:
                data_at_time = data_array.squeeze()  # Assume single time if no time dim

            self._set_time_config(t, data_at_time)
            field_to_plot = self._prepare_field_to_plot(data_at_time, 
                                                        field_name,
                                                        file_index, 
                                                        plot_type, 
                                                        figure, 
                                                        time_level=t)
            if field_to_plot:
                plot_result = self.create_plot(field_name, field_to_plot)
                pu.print_map(self.config_manager, 
                             plot_type, 
                             self.config_manager.findex, 
                             plot_result)

    def _process_scatter_plot(self, data_array, field_name, file_index, plot_type, figure):
        """Process a scatter plot."""
        self.logger.debug("Starting scatter plot processing")
        self.logger.debug(f"ax_opts keys: {list(self.config_manager.ax_opts.keys())}")
        self.logger.debug(f"ax_opts projection: {self.config_manager.ax_opts.get('projection', 'NOT SET')}")
        self.logger.debug(f"ax_opts extent: {self.config_manager.ax_opts.get('extent', 'NOT SET')}")
        self.config_manager.level = None
        time_level_config = self.config_manager.ax_opts.get('time_lev', 0)
        tc_dim = self.config_manager.get_model_dim_name('tc') or 'time'

        if tc_dim in data_array.dims:
            num_times = data_array[tc_dim].size
            self.logger.debug(f"Time dimension '{tc_dim}' has {num_times} levels")
            time_levels = range(num_times) if time_level_config == 'all' else [time_level_config]
            self.logger.debug(f"Will process time levels: {list(time_levels)}")
        else:
            self.logger.debug("No time dimension found, using single time level")
            time_levels = [0]

        for t in time_levels:
            self.logger.debug(f"Processing time level {t} for field {field_name}")
            if tc_dim in data_array.dims:
                data_at_time = data_array.isel({tc_dim: t})
                self.logger.debug(f"Extracted time slice shape: {data_at_time.shape}")
            else:
                data_at_time = data_array.squeeze()
                self.logger.debug(f"Squeezed data shape: {data_at_time.shape}")
            
            # Check for all NaN values
            nan_count = np.isnan(data_at_time.values).sum()
            total_count = data_at_time.size
            self.logger.debug(f"NaN count: {nan_count} out of {total_count} values")
            
            if np.isnan(data_at_time).all():
                self.logger.warning(f"Skipping time level {t} for {field_name} - all values are NaN")
                continue
                
            self._set_time_config(t, data_at_time)
            
            # Create a new figure for each level
            figure = Figure.create_eviz_figure(self.config_manager, plot_type)
            self.config_manager.ax_opts = figure.init_ax_opts(field_name)

            self.logger.debug(f"Preparing field to plot for time level {t}")
            field_to_plot = self._prepare_field_to_plot(data_at_time, 
                                                    field_name, 
                                                    file_index,
                                                    plot_type, 
                                                    figure,
                                                    time_level=t)
            
            if field_to_plot:
                self.logger.debug("Successfully prepared field, creating plot")
                plot_result = self.create_plot(field_name, field_to_plot)
                pu.print_map(self.config_manager, 
                            plot_type, 
                            self.config_manager.findex, 
                            plot_result)
            else:
                self.logger.warning(f"No valid field_to_plot returned for time level {t}")

    def _process_box_plot(self, data_array, field_name, file_index, plot_type, figure):
        """Process a box plot for observational data."""
        self.config_manager.level = None        
        time_level_config = None
        
        if (hasattr(self.config_manager, 'spec_data') and 
            field_name in self.config_manager.spec_data and 
            'boxplot' in self.config_manager.spec_data[field_name] and
            'time_lev' in self.config_manager.spec_data[field_name]['boxplot']):
            
            time_level_config = self.config_manager.spec_data[field_name]['boxplot']['time_lev']
        
        # If not found in field-specific config, check ax_opts
        if time_level_config is None:
            time_level_config = self.config_manager.ax_opts.get('time_lev', -1)  # Default to last time level
        
        if isinstance(time_level_config, str) and time_level_config.strip('-').isdigit():
            time_level_config = int(time_level_config)
        
        tc_dim = self.config_manager.get_model_dim_name('tc') or 'time'
        
        if tc_dim in data_array.dims:
            num_times = data_array[tc_dim].size
            self.logger.debug(f"Time dimension '{tc_dim}' has {num_times} levels")
            if isinstance(time_level_config, int):
                actual_time_lev = time_level_config if time_level_config >= 0 else num_times + time_level_config

        exp_id = self.config_manager.get_file_exp_id(self.config_manager.findex)
        box_data = self.data_extractor._extract_box_data(data_array, time_lev=time_level_config, exp_id=exp_id)
        
        if box_data is None:
            self.logger.error(f"Failed to prepare box plot data for {field_name}")
            return
        
        # Pass both the DataFrame (box_data) and the original DataArray (data_array) for units extraction
        field_to_plot = (box_data, None, None, field_name, plot_type, file_index, figure, data_array)
        
        plot_result = self.create_plot(field_name, field_to_plot)
        
        if isinstance(plot_result, tuple) and len(plot_result) >= 1:
            fig = plot_result[0]  # Extract the figure from the tuple
            pu.print_map(self.config_manager, 
                        plot_type, 
                        self.config_manager.findex, 
                        fig)  # Pass just the figure
        else:
            # If it's not a tuple, pass it directly
            pu.print_map(self.config_manager, 
                        plot_type, 
                        self.config_manager.findex, 
                        plot_result)

    def _process_box_plots(self, current_field_index, field_name1, field_name2, plot_type, sdat1_dataset, sdat2_dataset):
        """Process side-by-side comparison plots for box plot types."""
        # Use a consistent time level for both plots
        if (hasattr(self.config_manager, 'spec_data') and 
            field_name1 in self.config_manager.spec_data and 
            'boxplot' in self.config_manager.spec_data[field_name1] and
            'time_lev' in self.config_manager.spec_data[field_name1]['boxplot']):
            
            time_level_config = self.config_manager.spec_data[field_name1]['boxplot']['time_lev']

        exp_id1 = self.config_manager.get_file_exp_id(self.config_manager.a_list[0])
        
        use_all_times = time_level_config == 'all'
        df1 = self.data_extractor._extract_box_data(sdat1_dataset[field_name1], time_level_config, exp_id1)
        
        all_dfs = [df1] if df1 is not None else []

        # Process second dataset(s)
        for i, file_idx in enumerate(self.config_manager.b_list, start=1):
            map_params = self.config_manager.map_params.get(file_idx)
            if not map_params:
                continue
                
            filename = map_params.get('filename')
            if not filename:
                continue
                
            data_source = self.config_manager.pipeline.get_data_source(filename)
            if not data_source or not hasattr(data_source, 'dataset') or data_source.dataset is None:
                continue
                
            dataset = data_source.dataset            
            exp_id2 = self.config_manager.get_file_exp_id(file_idx)
            df2 = self.data_extractor._extract_box_data(dataset[field_name2], time_level_config, exp_id2)
            
            if df2 is not None:
                all_dfs.append(df2)
        
        # Combine all DataFrames
        if not all_dfs:
            self.logger.error("No valid data for box plots")
            return
            
        combined_df = pd.concat(all_dfs, ignore_index=True)
        # Log the combined DataFrame info
        self.logger.debug(f"Combined DataFrame has {len(combined_df)} rows")
        self.logger.debug(f"Combined DataFrame has experiment column: {'experiment' in combined_df.columns}")
                   
        figure = Figure.create_eviz_figure(self.config_manager, plot_type, nrows=1, ncols=1)
        figure.set_axes()
        
        self.register_plot_type(field_name1, plot_type)
        
        self.config_manager.ax_opts = figure.init_ax_opts(field_name1)
        
        field_to_plot = (combined_df, None, None, field_name1, plot_type, self.config_manager.a_list[0], figure)
        
        self.plot_result = self.create_plot(field_name1, field_to_plot)
        
        pu.print_map(self.config_manager, 
                     plot_type, 
                     self.config_manager.findex, 
                     self.plot_result)

    def _process_xy_side_by_side_plots(self, current_field_index, field_name1, field_name2, plot_type, sdat1_dataset, sdat2_dataset):
        """Process side-by-side comparison plots for xy or polar plot types."""
        self.logger.info(f"Processing side-by-side comparison of {field_name1} vs {field_name2} as gridded data")
        
        num_plots = len(self.config_manager.compare_exp_ids)
        nrows = num_plots
        ncols = 1

        levels = self.config_manager.get_levels(field_name1, plot_type + 'plot')
        if not levels:
            return

        # Hack: Reset comparison colorbar limits for each new field
        if hasattr(self.config_manager, '_comparison_cbar_limits'):
            self.logger.debug(f"Resetting comparison colorbar limits for {field_name1}")
            self.config_manager._comparison_cbar_limits = {}

        for level_val in levels:
            # Set a consistent colorbar width before creating the figure
            if not hasattr(self.config_manager, 'colorbar_width'):
                self.config_manager.colorbar_width = 0.02  # Consistent width for all colorbars
            
            figure = Figure.create_eviz_figure(self.config_manager, plot_type,
                                            nrows=nrows, ncols=ncols)
        
            # Set up axes with proper spacing
            figure.set_axes()
            self.logger.info(f"Figure created with {nrows}x{ncols} layout for {num_plots} datasets")
            self.config_manager.level = level_val

            # Store coordinate information for regional plots if available
            if self.config_manager.is_regional:
                lon_coord_name = self.config_manager.longitude_coordinate_name
                lat_coord_name = self.config_manager.latitude_coordinate_name
                
                # Check if coordinate names exist in the dataset
                if (lon_coord_name and lat_coord_name and 
                    lon_coord_name in sdat1_dataset.coords and lat_coord_name in sdat1_dataset.coords):
                    self.lon = sdat1_dataset.coords[lon_coord_name]
                    self.lat = sdat1_dataset.coords[lat_coord_name]
                    self.logger.debug(f"Set coordinates: lon={lon_coord_name}, lat={lat_coord_name}")
                else:
                    self.logger.debug(f"Coordinate names not found: lon={lon_coord_name}, lat={lat_coord_name}")
                    self.logger.debug(f"Available coordinates: {list(sdat1_dataset.coords.keys())}")

            # Create the side-by-side plots
            self._create_xy_side_by_side_plot(current_field_index,
                                            field_name1, 
                                            field_name2, 
                                            figure,
                                            plot_type, 
                                            sdat1_dataset, 
                                            sdat2_dataset,
                                            level_val)

            # Print the map
            pu.print_map(self.config_manager, 
                        plot_type, 
                        self.config_manager.findex, 
                        self.plot_result,
                        level=level_val)
        
            # Hack: Clear filled contours list after processing each field
            if hasattr(self.config_manager, '_filled_contours'):
                self.logger.debug(f"Clearing filled contours list after processing {field_name1}")
                self.config_manager._filled_contours = []

        self.data2d_list = []

    def _process_other_side_by_side_plots(self, current_field_index, field_name1, field_name2, plot_type, sdat1_dataset, sdat2_dataset):
        """Process side-by-side comparison plots for non-xy plot types (xt, yz, tx, etc.)."""
        self.logger.info(f"Processing side-by-side comparison of {field_name1} vs {field_name2} for {plot_type} plot type")
        
        # For most non-XY plot types, we'll use a generic approach that delegates to the appropriate plotter
        self._process_generic_side_by_side_plots(current_field_index, field_name1, field_name2, plot_type, sdat1_dataset, sdat2_dataset)

    def _process_generic_side_by_side_plots(self, current_field_index, field_name1, field_name2, plot_type, sdat1_dataset, sdat2_dataset):
        """Generic side-by-side processing for non-xy plot types."""
        self.logger.info(f"Processing generic side-by-side comparison of {field_name1} vs {field_name2} as {plot_type} data")
        
        # Check if this is overlay mode
        is_overlay = hasattr(self.config_manager, 'overlay') and self.config_manager.overlay
        
        # Collect datasets
        datasets = []
        
        # Always include the passed datasets first
        if sdat1_dataset is not None:
            datasets.append(sdat1_dataset)
        if sdat2_dataset is not None:
            datasets.append(sdat2_dataset)
        
        # For overlay mode, try to get all datasets from the pipeline
        if is_overlay:
            self.logger.info("Overlay mode - checking all available data sources")
            all_data_sources = self.config_manager.pipeline.get_all_data_sources()
            self.logger.info(f"Found {len(all_data_sources)} data sources from pipeline")
            
            # The pipeline get_all_data_sources() returns a dict with file paths as keys and DataSource objects as values
            # We need to iterate over the values (DataSource objects) directly
            for i, (file_path, data_source) in enumerate(all_data_sources.items()):
                self.logger.debug(f"Checking data source {i}: {file_path}")
                if data_source and hasattr(data_source, 'dataset') and data_source.dataset is not None:
                    dataset = data_source.dataset
                    if field_name1 in dataset:
                        # Check if this dataset is already in our list (avoid duplicates by using id())
                        if not any(id(ds) == id(dataset) for ds in datasets):
                            datasets.append(dataset)
                            self.logger.info(f"Added dataset {i} from {file_path} to overlay list")
                        else:
                            self.logger.debug(f"Dataset {i} from {file_path} already in list (duplicate)")
                    else:
                        self.logger.debug(f"Field {field_name1} not found in dataset from {file_path}")
                else:
                    self.logger.debug(f"Could not load dataset from {file_path}")
        
        if not datasets:
            self.logger.error("No datasets available for side-by-side plotting.")
            return
        
        self.logger.debug(f"Processing {len(datasets)} datasets for {plot_type} comparison")
        
        if is_overlay:
            # For overlay mode, create a single figure and plot all datasets on it
            self._process_overlay_plots(datasets, field_name1, plot_type, current_field_index)
        else:
            # For side-by-side mode, create separate plots for each dataset
            self._process_separate_plots(datasets, field_name1, plot_type)

    def _process_overlay_plots(self, datasets, field_name, plot_type, current_field_index):
        """Process overlay plots where multiple datasets are plotted on the same figure."""
        self.logger.info(f"Creating overlay plot for {len(datasets)} datasets")
        
        # Create a single figure for all datasets
        figure = Figure.create_eviz_figure(self.config_manager, plot_type)
        figure.set_axes()
        self.config_manager.ax_opts = figure.init_ax_opts(field_name)
        
        # Register the plot type
        self.register_plot_type(field_name, plot_type)
        
        # Set total datasets for the plotter (overlay mode is already active from config)
        self.config_manager.total_datasets = len(datasets)
        
        # For overlay plots, calculate global min/max across all datasets to ensure proper y-axis scaling
        global_min, global_max = None, None
        if plot_type == 'xt':  # Only for time series plots
            all_data_values = []
            for dataset in datasets:
                if field_name in dataset:
                    field_data = dataset[field_name]
                    # Extract time series data (assuming time is first dimension)
                    if field_data.ndim >= 1:
                        data_values = field_data.values.flatten()
                        all_data_values.extend(data_values[~np.isnan(data_values)])  # Remove NaN values
            
            if all_data_values:
                global_min = np.min(all_data_values)
                global_max = np.max(all_data_values)
                self.logger.debug(f"Calculated global y-axis range for overlay: [{global_min:.6f}, {global_max:.6f}]")
        
        # Plot each dataset on the same figure
        for i, dataset in enumerate(datasets):
            if field_name not in dataset:
                self.logger.warning(f"Field {field_name} not found in dataset {i}")
                continue
                
            field_data = dataset[field_name]
            self.logger.debug(f"Adding dataset {i} to overlay plot, data shape: {field_data.shape}")
            
            # Set current dataset index for proper styling
            self.config_manager.current_dataset_index = i
            
            # Prepare field data for plotting
            field_to_plot = self._prepare_field_to_plot(field_data, 
                                                       field_name, 
                                                       i, 
                                                       plot_type, 
                                                       figure, 
                                                       time_level=0,
                                                       global_vmin=global_min,
                                                       global_vmax=global_max)
            
            if field_to_plot:
                # Create the plot - this will add to the existing figure
                plot_result = self.create_plot(field_name, field_to_plot)
        
        # Print the final overlay plot
        pu.print_map(self.config_manager, 
                    plot_type, 
                    self.config_manager.findex, 
                    plot_result)

    def _process_separate_plots(self, datasets, field_name, plot_type):
        """Process separate plots for each dataset (non-overlay mode)."""
        for i, dataset in enumerate(datasets):
            if field_name not in dataset:
                self.logger.warning(f"Field {field_name} not found in dataset {i}")
                continue
            
            field_data = dataset[field_name]
            self.logger.debug(f"Processing field {field_name} from dataset {i}, data shape: {field_data.shape}")
            
            # Create a figure for this plot
            figure = Figure.create_eviz_figure(self.config_manager, plot_type)
            figure.set_axes()  # Initialize axes for the plot
            self.config_manager.ax_opts = figure.init_ax_opts(field_name)
            
            # Register the plot type for this field
            self.register_plot_type(field_name, plot_type)
            
            # Use the appropriate plot-specific method
            if hasattr(self, '_process_xt_plot') and 'xt' in plot_type:
                self.logger.debug(f"Processing XT plot for dataset {i}")
                self._process_xt_plot(field_data, field_name, i, plot_type, figure)
            elif hasattr(self, '_process_yz_plot') and 'yz' in plot_type:
                self.logger.info(f"Processing YZ plot for dataset {i}")
                # Check if YZ plot method exists (it might not)
                try:
                    self._process_yz_plot(field_data, field_name, i, plot_type, figure)
                except AttributeError:
                    self.logger.warning("YZ plot method not available, using general approach")
                    self.process_plot(field_data, field_name, i, plot_type)
            elif hasattr(self, '_process_tx_plot') and 'tx' in plot_type:
                self.logger.info(f"Processing TX plot for dataset {i}")
                self._process_tx_plot(field_data, field_name, i, plot_type, figure)
            else:
                # Fallback to general process_plot method
                self.logger.info(f"Using general process_plot for {plot_type} plot type")
                self.process_plot(field_data, field_name, i, plot_type)

    def _create_xy_side_by_side_plot(self, 
                                     current_field_index,
                                     field_name1, 
                                     field_name2, 
                                     figure,
                                     plot_type, 
                                     sdat1_dataset, 
                                     sdat2_dataset, 
                                     level=None):
        """
        Create a side-by-side comparison plot for the given data.
        
        The layout is:
        - Left subplot: First dataset
        - Middle subplot: Second dataset
        - Right subplot: Third dataset (if present)
        """
        num_plots = len(self.config_manager.compare_exp_ids)
        self.comparison_plot = False

        # Plot first dataset (from a_list)
        if self.config_manager.a_list:
            first_file_idx = self.config_manager.a_list[0]
            first_data = sdat1_dataset[field_name1]
            self.logger.info(f"Processing first dataset {first_file_idx} with field {field_name1}")
            self.logger.info(f"First dataset data shape: {first_data.shape}, has data: {not first_data.isnull().all().values}")
            self._process_single_side_by_side_plot(first_file_idx,
                                            current_field_index,
                                            field_name1, 
                                            figure, 
                                            0,
                                            first_data, 
                                            plot_type,
                                            level=level)

        # Plot remaining datasets (from b_list)
        for i, file_idx in enumerate(self.config_manager.b_list, start=1):
            if i < num_plots:  # Only plot if we have a corresponding axis
                map_params = self.config_manager.map_params.get(file_idx)
                filename = map_params.get('filename')
                data_source = self.config_manager.pipeline.get_data_source(filename)
                dataset = data_source.dataset
                
                # Use the same field name for all datasets in the comparison
                # since we're comparing the same variable across different datasets
                field_name_for_dataset = field_name1
                
                # Verify the field exists in this dataset
                if field_name_for_dataset not in dataset.data_vars:
                    self.logger.warning(f"Field '{field_name_for_dataset}' not found in dataset {filename}, skipping this plot")
                    continue
                
                self.logger.info(f"Processing dataset {file_idx}: {filename} with field {field_name_for_dataset}")
                field_data = dataset[field_name_for_dataset]
                self.logger.info(f"Field data shape: {field_data.shape}, has data: {not field_data.isnull().all().values}")

                self._process_single_side_by_side_plot(file_idx,
                                                current_field_index,
                                                field_name_for_dataset, 
                                                figure, 
                                                i,
                                                dataset[field_name_for_dataset], 
                                                plot_type,
                                                level=level)

    def _process_single_side_by_side_plot(self, file_index, 
                                          current_field_index,
                                          field_name, 
                                          figure, 
                                          ax_index, 
                                          data_array, 
                                          plot_type,
                                          level=None):
        """Process a single plot for side-by-side comparison."""
        self.config_manager.findex = file_index
        self.config_manager.pindex = current_field_index
        self.config_manager.axindex = ax_index
        time_level_config = self.config_manager.ax_opts.get('time_lev', -1)

        # Register plot type for field
        if not hasattr(self.config_manager, '_plot_type_registry'):
            self.config_manager._plot_type_registry = {}
        self.config_manager._plot_type_registry[field_name] = plot_type

        # Track which dataset we're currently plotting and how many total
        if self.config_manager.should_overlay_plots(field_name, plot_type[:2]):
            if file_index in self.config_manager.a_list:
                dataset_index = self.config_manager.a_list.index(file_index)
            elif file_index in self.config_manager.b_list:
                dataset_index = len(self.config_manager.a_list) + self.config_manager.b_list.index(file_index)
            else:
                dataset_index = 0
                
            self.config_manager.current_dataset_index = dataset_index
            self.config_manager.total_datasets = len(self.config_manager.a_list) + len(self.config_manager.b_list)
            
        self.config_manager.ax_opts = figure.init_ax_opts(field_name)
        
        field_to_plot = self._prepare_field_to_plot(data_array, 
                                                    field_name,
                                                    file_index,
                                                    plot_type, 
                                                    figure,
                                                    time_level=time_level_config,
                                                    level=level)
        
        self.logger.info(f"field_to_plot result for ax_index {ax_index}: {field_to_plot is not None}")
        if field_to_plot and field_to_plot[0] is not None:
            data2d = field_to_plot[0]
            self.logger.info(f"Data stats for ax_index {ax_index}: min={float(data2d.min()):.6f}, max={float(data2d.max()):.6f}, shape={data2d.shape}")
            if not hasattr(self, 'data2d_list'):
                self.data2d_list = []
            self.data2d_list.append(data2d)
            
        if field_to_plot:
            self.logger.info(f"Creating plot for ax_index {ax_index}, field {field_name}")
            self.plot_result = self.create_plot(field_name, field_to_plot)
            self.logger.info(f"Plot result for ax_index {ax_index}: {self.plot_result is not None}")

    def _process_xy_comparison_plots(self, 
                                     file_indices: tuple,
                                     current_field_index: int,
                                     field_name1: str, 
                                     field_name2: str, 
                                     plot_type: str,
                                     sdat1_dataset: xr.Dataset,
                                     sdat2_dataset: xr.Dataset):
        """Process comparison plots for xy or polar plot types."""
        file_index1, file_index2 = file_indices
        nrows, ncols = self.config_manager.input_config.comp_panels

        levels = self.config_manager.get_levels(field_name1, plot_type + 'plot')
        if not levels:
            return

        for level_val in levels:
            figure = Figure.create_eviz_figure(self.config_manager, 
                                               plot_type,
                                               nrows=nrows, 
                                               ncols=ncols)
            figure.set_axes()
            self.config_manager.level = level_val

            if figure.subplots == (3, 1):
                self._create_3x1_comparison_plot(file_indices,
                                                 current_field_index,
                                                 field_name1, 
                                                 field_name2, 
                                                 figure,
                                                 plot_type, 
                                                 sdat1_dataset, 
                                                 sdat2_dataset,
                                                 level_val)
            elif figure.subplots == (2, 2):
                self._create_2x2_comparison_plot(file_indices,
                                                 current_field_index,
                                                 field_name1, 
                                                 field_name2, 
                                                 figure,
                                                 plot_type, 
                                                 sdat1_dataset, 
                                                 sdat2_dataset,
                                                 level_val)

            # self.config_manager.findex = file_index1
            pu.print_map(self.config_manager, 
                         plot_type, 
                         self.config_manager.findex, 
                         self.plot_result,
                        level=level_val)
            if hasattr(self, 'comparison_plot'):
                self.comparison_plot = False  # Reset comparison flag

    def _process_other_comparison_plots(self, file_indices: tuple,
                                        current_field_index: int,
                                        field_name1: str, field_name2: str,
                                        plot_type: str,
                                        sdat1_dataset: xr.Dataset,
                                        sdat2_dataset: xr.Dataset):
        """Process comparison plots for other plot types."""
        file_index1, file_index2 = file_indices
        nrows, ncols = self.config_manager.input_config.comp_panels

        figure = Figure.create_eviz_figure(self.config_manager, plot_type, nrows=nrows,
                                           ncols=ncols)
        figure.set_axes()
        self.config_manager.level = None

        if figure.subplots == (3, 1):
            self._create_3x1_comparison_plot(file_indices, 
                                             current_field_index,
                                             field_name1, 
                                             field_name2, 
                                             figure,
                                             plot_type, 
                                             sdat1_dataset, 
                                             sdat2_dataset)
        elif figure.subplots == (2, 2):
            self._create_2x2_comparison_plot(file_indices, 
                                             current_field_index,
                                             field_name1, 
                                             field_name2, 
                                             figure,
                                             plot_type, 
                                             sdat1_dataset, 
                                             sdat2_dataset)

        # self.config_manager.findex = file_index1
        pu.print_map(self.config_manager, 
                     plot_type, 
                     self.config_manager.findex, 
                     self.plot_result)
        if hasattr(self, 'comparison_plot'):
            self.comparison_plot = False  # Reset comparison flag

    def _create_3x1_comparison_plot(self, 
                                    file_indices, 
                                    current_field_index,
                                    field_name1, 
                                    field_name2, 
                                    figure,
                                    plot_type, 
                                    sdat1_dataset, 
                                    sdat2_dataset, 
                                    level=None):
        """Create a 3x1 comparison plot."""
        file_index1, file_index2 = file_indices

        # Plot the first dataset
        self._process_3x1_comparison_plot(file_index1, 
                                          current_field_index,
                                          field_name1, 
                                          figure, 
                                          0,
                                          sdat1_dataset[field_name1], 
                                          plot_type,
                                          level=level)

        # Plot the second dataset
        self._process_3x1_comparison_plot(file_index2, 
                                          current_field_index,
                                          field_name2, 
                                          figure, 
                                          1,
                                          sdat2_dataset[field_name2], 
                                          plot_type,
                                          level=level)

        # Plot the comparison (difference)
        if not hasattr(self, 'comparison_plot'):
            self.comparison_plot = False
        self.comparison_plot = True
        self.config_manager.comparison_plot = True
        # For the comparison, we need to pass both datasets
        # The _process_comparison_plot method will need to handle this special case
        self._process_3x1_comparison_plot(file_index1, 
                                          current_field_index,
                                          field_name1, 
                                          figure, 
                                          2,
                                          (sdat1_dataset[field_name1], sdat2_dataset[field_name2]),
                                          plot_type, 
                                          level=level)

    def _create_2x2_comparison_plot(self, 
                                    file_indices, 
                                    current_field_index,
                                    field_name1, 
                                    field_name2, 
                                    figure,
                                    plot_type, 
                                    sdat1_dataset, 
                                    sdat2_dataset, 
                                    level=None):
        """Create a 2x2 comparison plot."""
        file_index1, file_index2 = file_indices

        # Plot the first dataset in the top-left
        self._process_2x2_comparison_plot(file_index1, 
                                          current_field_index,
                                          field_name1, 
                                          figure, 
                                          [0, 0], 
                                          0,
                                          sdat1_dataset[field_name1], 
                                          plot_type,
                                          level=level)

        # Plot the second dataset in the top-right
        self._process_2x2_comparison_plot(file_index2, 
                                          current_field_index,
                                          field_name2, 
                                          figure, 
                                          [0, 1], 
                                          1,
                                          sdat2_dataset[field_name2], 
                                          plot_type,
                                          level=level)

        # Plot comparison in the bottom row
        if not hasattr(self, 'comparison_plot'):
            self.comparison_plot = False
        self.comparison_plot = True
        self.config_manager.comparison_plot = True
        # For the comparison, we need to pass both datasets
        self._process_2x2_comparison_plot(file_index1, 
                                          current_field_index,
                                          field_name1, 
                                          figure, 
                                          [1, 0], 
                                          2,
                                          (sdat1_dataset[field_name1], sdat2_dataset[field_name2]),
                                          plot_type, 
                                          level=level)

        # If extra field type is enabled, plot another comparison view
        # if self.config_manager.ax_opts.get('add_extra_field_type', False):
        self._process_2x2_comparison_plot(file_index1, 
                                          current_field_index,
                                          field_name1, 
                                          figure, 
                                          [1, 1], 
                                          2,
                                          (sdat1_dataset[field_name1], sdat2_dataset[field_name2]),
                                          plot_type, 
                                          level=level)

    def _process_3x1_comparison_plot(self, 
                                     file_index, 
                                     current_field_index,
                                     field_name, 
                                     figure, 
                                     ax_index, 
                                     data_array, 
                                     plot_type,
                                     level=None):
        """Process a 3x1 comparison plot."""
        self.config_manager.findex = file_index
        self.config_manager.pindex = current_field_index
        self.config_manager.axindex = ax_index
        self.config_manager.ax_opts = figure.init_ax_opts(field_name)
        time_level_config = self.config_manager.ax_opts.get('time_lev', 0)
        
        # Register plot type for field
        if not hasattr(self.config_manager, '_plot_type_registry'):
            self.config_manager._plot_type_registry = {}
        self.config_manager._plot_type_registry[field_name] = plot_type

        if ax_index == 2:  # Third panel in 3x1 layout is the difference
            self.config_manager.ax_opts['is_diff_field'] = True
        
        if ax_index == 2:
            # Compute and plot the difference field
            if not hasattr(self, 'data2d_list'):
                self.data2d_list = []
            if len(self.data2d_list) == 2:
                data2d1, data2d2 = self.data2d_list
                proc = self.data_extractor.processor if hasattr(self.data_extractor, 'processor') else None
                if proc is None:
                    from eviz.lib.data.pipeline.processor import DataProcessor
                    proc = DataProcessor(self.config_manager)
                    
                dim1_name, dim2_name = self.config_manager.get_dim_names(plot_type)
                
                self.logger.debug(
                    f"Regridding {field_name} over {dim1_name} and {dim2_name} for difference plot")
                self.logger.debug(f"data2d1 shape: {data2d1.shape}, dims: {data2d1.dims}")
                self.logger.debug(f"data2d2 shape: {data2d2.shape}, dims: {data2d2.dims}")
                
                # Regrid data2d2 to match data2d1's grid
                try:
                    # Regrid data2d2 to match data2d1's grid
                    d2_on_d1 = proc.regrid(data2d1, data2d2, dims=(dim1_name, dim2_name))                    
                    diff_result = proc.compute_difference(data2d1, d2_on_d1)
                    
                    field_to_plot = (diff_result, 
                                    diff_result[dim1_name], 
                                    diff_result[dim2_name], 
                                    field_name, plot_type,
                                    file_index, figure)
                except Exception as e:
                    self.logger.error(f"Error computing difference: {e}")
                    field_to_plot = (xr.zeros_like(data2d1), 
                                    data2d1[dim1_name], 
                                    data2d1[dim2_name], 
                                    field_name, plot_type,
                                    file_index, figure)
            else:
                self.logger.error("Not enough data for difference plot")
                field_to_plot = None
            self.data2d_list = []
        else:
            # For the first two panels, plot as usual and store data for diff
            field_to_plot = self._prepare_field_to_plot(data_array, 
                                                        field_name,
                                                        file_index,
                                                        plot_type, 
                                                        figure,
                                                        time_level=time_level_config,
                                                        level=level)
            if field_to_plot:
                if not hasattr(self, 'data2d_list'):
                    self.data2d_list = []
                self.data2d_list.append(field_to_plot[0])
        if field_to_plot:
            self.plot_result = self.create_plot(field_name, field_to_plot, plot_type)

    def _process_2x2_comparison_plot(self, 
                                     file_index, 
                                     current_field_index,
                                     field_name, 
                                     figure, 
                                     gsi, 
                                     ax_index, 
                                     data_array, 
                                     plot_type,
                                     level=None):
        """Process a 2x2 comparison plot."""
        ax = figure.get_axes()
        self.config_manager.findex = file_index
        self.config_manager.pindex = current_field_index
        self.config_manager.axindex = ax_index
        time_level_config = self.config_manager.ax_opts.get('time_lev', 0)

        # Register plot type for field
        if not hasattr(self.config_manager, '_plot_type_registry'):
            self.config_manager._plot_type_registry = {}
        self.config_manager._plot_type_registry[field_name] = plot_type

        # Initialize ax_opts BEFORE setting flags
        self.config_manager.ax_opts = figure.init_ax_opts(field_name)

        # Set difference field flag if this is a comparison panel (bottom row)
        if gsi[0] == 1:  # Bottom row in 2x2 layout is for differences
            self.config_manager.ax_opts['is_diff_field'] = True
            # Set extra field type flag for the bottom-right panel
            if gsi[1] == 1:
                self.config_manager.ax_opts['add_extra_field_type'] = True

        figure.set_ax_opts_diff_field(ax[ax_index])
        
        # Handle difference calculation for bottom row panels
        if isinstance(data_array, tuple):
            if not hasattr(self, 'data2d_list'):
                self.data2d_list = []
            if len(self.data2d_list) == 2:
                data2d1, data2d2 = self.data2d_list
                proc = self.data_extractor.processor if hasattr(self.data_extractor, 'processor') else None
                if proc is None:
                    from eviz.lib.data.pipeline.processor import DataProcessor
                    proc = DataProcessor(self.config_manager)
                    
                dim1_name, dim2_name = self.config_manager.get_dim_names(plot_type)
                                
                try:
                    # Regrid data2d2 to match data2d1's grid
                    d2_on_d1 = proc.regrid(data2d1, data2d2, dims=(dim1_name, dim2_name))
                    if self.config_manager.ax_opts.get('add_extra_field_type', False):
                        diff_result = proc.compute_difference(data2d1, 
                                                              d2_on_d1, 
                                                              method=self.config_manager.extra_diff_plot)
                    else:
                        diff_result = proc.compute_difference(data2d1, 
                                                              d2_on_d1)
                    
                    self.logger.debug(
                        f"Diff data min/max: {diff_result.min().values}/{diff_result.max().values}")
                    
                    # Create field_to_plot tuple with the difference result
                    field_to_plot = (diff_result, 
                                    diff_result[dim1_name], 
                                    diff_result[dim2_name], 
                                    field_name, plot_type,
                                    file_index, figure)
                                    
                except Exception as e:
                    self.logger.error(f"Error computing difference: {e}")
                    # Create a dummy field with zeros if calculation fails
                    field_to_plot = (xr.zeros_like(data2d1), 
                                    data2d1[dim1_name], 
                                    data2d1[dim2_name], 
                                    field_name, plot_type,
                                    file_index, figure)
            else:
                self.logger.error("Not enough data for difference plot")
                field_to_plot = None
        else:
            # For the top row panels, plot as usual and store data for diff
            field_to_plot = self._prepare_field_to_plot(data_array, 
                                                        field_name,
                                                        file_index,
                                                        plot_type, 
                                                        figure,
                                                        time_level=time_level_config,
                                                        level=level)
            if field_to_plot and field_to_plot[0] is not None:
                if not hasattr(self, 'data2d_list'):
                    self.data2d_list = []
                self.data2d_list.append(field_to_plot[0])

        if field_to_plot:
            self.plot_result = self.create_plot(field_name, field_to_plot, plot_type)
