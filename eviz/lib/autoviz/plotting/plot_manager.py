import logging
import numpy as np
import xarray as xr
from eviz.lib.autoviz.plotter import SimplePlotter
from eviz.lib.autoviz.plotting.factory import PlotterFactory
from eviz.lib.autoviz.figure import Figure
import eviz.lib.utils as u
import eviz.lib.autoviz.utils as pu
from eviz.lib.config.config_manager import ConfigManager
from eviz.lib.data import DataSource # Needed for process_single_plots, process_comparison_plots, etc.
from eviz.lib.data.data_extractor import DataExtractor # Import the new DataExtractor

class PlotManager:
    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

    def __init__(self, config_manager: ConfigManager, data_extractor: DataExtractor):
        self.config_manager = config_manager
        self.data_extractor = data_extractor # Store the DataExtractor instance
        self.data2d_list = [] # Initialize this here as it's used by comparison plots
        self.plot_result = None # Used in _process_box_plots
        self.field_names = None # Used in comparison plots
        self.file_indices = None # Used in comparison plots
        self.lon = None # Used in _process_xy_side_by_side_plots
        self.lat = None # Used in _process_xy_side_by_side_plots

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
        self.config_manager._plot_type_registry[field_name] = plot_type
        
    def get_plot_type(self, field_name, default='xy'):
        """Get the plot type for a field."""
        return self.config_manager._plot_type_registry.get(field_name, default)
    
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
    
    def create_plot(self, field_name, data_to_plot):
        """Create a plot using the appropriate plotter.
        
        Args:
            field_name: Name of the field to plot
            data_to_plot: Tuple containing plot data
            
        Returns:
            The created plot object
        """
        backend = getattr(self.config_manager, 'output_backend', 'matplotlib')
        
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
                               level=None) -> tuple:
        """Prepare the 2D data array and coordinates to be plotted."""
        dim1_name, dim2_name = self.config_manager.get_dim_names(plot_type)
        data2d = None

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
            return data2d, None, None, field_name, plot_type, file_index, figure
        elif plot_type in ['sc']:
            # TODO: temporary:
            extent = self._get_data_extent(data_array)
            self.config_manager.ax_opts['extent'] = extent
            self.config_manager.ax_opts['central_lon'] = self.config_manager.central_longitude
            self.config_manager.ax_opts['central_lat'] = self.config_manager.central_latitude
            return data2d[0], data2d[1], data2d[2], field_name, plot_type, file_index, figure

        # Process coordinates based on domain type
        try:

            if self.config_manager.is_regional:
                if hasattr(self, '_process_coordinates'):
                    return self._process_coordinates(data2d, 
                                                     dim1_name, dim2_name,
                                                     field_name,
                                                     plot_type, file_index, figure)
                else:
                    xs = np.array(self._get_field(dim1_name, data2d)[0, :])
                    ys = np.array(self._get_field(dim2_name, data2d)[:, 0])
                    latN = max(ys[:])
                    latS = min(ys[:])
                    lonW = min(xs[:])
                    lonE = max(xs[:])
                    self.config_manager.ax_opts['extent'] = [lonW, lonE, latS, latN]
                    self.config_manager.ax_opts['central_lon'] = self.config_manager.central_longitude
                    self.config_manager.ax_opts['central_lat'] = self.config_manager.central_latitude
                    self.logger.info(f"Extent: {self.config_manager.ax_opts['extent']} ")
                    return data2d, xs, ys, field_name, plot_type, file_index, figure
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

                return data2d, x, y, field_name, plot_type, file_index, figure

        except Exception as e:
            self.logger.error(f"Error processing coordinates for {field_name}: {e}")
            return None

    def _set_time_config(self, time_index, data_var):
        """Set time-related configuration values."""
        self.config_manager.time_level = time_index

        try:
            if 'time' in data_var.coords:
                if isinstance(time_index, int) and time_index < len(
                        data_var.coords['time']):
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
        num_times = data_array[tc_dim].size if tc_dim in data_array.dims else 1
        time_levels = range(num_times) if time_level_config == 'all' else [time_level_config]

        if not levels and not do_zsum:
            return

        self._process_level_plot(data_array, 
                                 field_name, 
                                 file_index, 
                                 plot_type, 
                                 figure, 
                                 time_levels, 
                                 levels)

    def _process_level_plot(self, 
                            data_array, 
                            field_name, 
                            file_index, 
                            plot_type, 
                            figure, 
                            time_levels, 
                            levels):
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
                    self.logger.warning(f"Skipping time level {t} for {field_name} - all values are NaN")
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
                                                                time_level=t)
                else:
                    field_to_plot = self._prepare_field_to_plot(data_at_time, 
                                                                field_name, 
                                                                file_index, 
                                                                plot_type, 
                                                                figure, 
                                                                time_level=t, 
                                                                level=level_val)

                if field_to_plot and not np.isnan(field_to_plot[0]).all():
                    plot_result = self.create_plot(field_name, field_to_plot)                    
                    pu.print_map(self.config_manager, 
                                 plot_type, 
                                 self.config_manager.findex, 
                                 plot_result, 
                                 level=level_val)
                else:
                    self.logger.warning(f"Skipping plot for time level {t} - no valid data after processing")

    def _process_scatter_plot(self, data_array, field_name, file_index, plot_type, figure):
        """Process a scatter plot."""
        self.logger.debug("Starting scatter plot processing")
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
        
        field_to_plot = (box_data, None, None, field_name, plot_type, file_index, figure)
        
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
        self.logger.info(f"Processing side-by-side comparison of {field_name1} vs {field_name2} as observational data")
        
        num_plots = len(self.config_manager.compare_exp_ids)
        nrows = 1
        ncols = num_plots

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
            self.config_manager.level = level_val

            # Store coordinate information for regional plots if available
            if self.config_manager.is_regional:
                lon_coord_name = self.config_manager.longitude_coordinate_name
                lat_coord_name = self.config_manager.latitude_coordinate_name
                if lon_coord_name and lat_coord_name and hasattr(sdat1_dataset, lon_coord_name) and hasattr(sdat1_dataset, lat_coord_name):
                    self.lon = getattr(sdat1_dataset, lon_coord_name)
                    self.lat = getattr(sdat1_dataset, lat_coord_name)

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
            self._process_single_side_by_side_plot(self.config_manager.a_list[0],
                                            current_field_index,
                                            field_name1, 
                                            figure, 
                                            0,
                                            sdat1_dataset[field_name1], 
                                            plot_type,
                                            level=level)

        # Plot remaining datasets (from b_list)
        for i, file_idx in enumerate(self.config_manager.b_list, start=1):
            if i < num_plots:  # Only plot if we have a corresponding axis
                map_params = self.config_manager.map_params.get(file_idx)
                filename = map_params.get('filename')
                data_source = self.config_manager.pipeline.get_data_source(filename)
                dataset = data_source.dataset

                self._process_single_side_by_side_plot(file_idx,
                                                current_field_index,
                                                field_name2, 
                                                figure, 
                                                i,
                                                dataset[field_name2], 
                                                plot_type,
                                                level=level)
