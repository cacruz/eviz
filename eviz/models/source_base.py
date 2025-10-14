import os
from dataclasses import dataclass
import logging
import matplotlib
import numpy as np
import xarray as xr
import pandas as pd

from eviz.lib.autoviz.plotting.backends.matplotlib.simple_plot import SimplePlotter
from eviz.lib.autoviz.plotting.factory import PlotterFactory
from eviz.lib.autoviz.figure import Figure
import eviz.lib.utils as u
import eviz.lib.autoviz.utils as pu
from eviz.lib.config.config_manager import ConfigManager
from eviz.lib.data import DataSource
from eviz.lib.models.base import GenericDataSource as BaseSource
from eviz.lib.data.utils import apply_conversion, apply_mean, apply_zsum, subset_region
from eviz.lib.data.data_extractor import DataExtractor
from eviz.lib.autoviz.plotting.plot_manager import PlotManager

logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)


@dataclass
class GenericSource(BaseSource):
    """This class defines gridded interfaces and plotting for all supported sources.
       These can be gridded or ungridded (e.g. observational data sources)

    Parameters
        config_manager :
            The ConfigManager instance that provides access to all configuration data.
    """
    config_manager: ConfigManager

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

    def __post_init__(self):
        self.logger.debug("Start init")
        self.config = self.config_manager.config
        self.app = self.config_manager.app_data
        self.specs = self.config_manager.spec_data

        self.use_mp_pool = self.app.system_opts.get('use_mp_pool', False)

        self.dims_name = None
        self.comparison_plot = False
        self.output_fname = None
        self.ax = None
        self.fig = None
        self.data2d_list = [] # This might still be needed if other parts of the code rely on it, or can be removed if fully encapsulated by PlotOrchestrator

        if self.use_mp_pool:
            # Set to avoid establishing a GUI in each sub-process:
            matplotlib.use('agg') # Keep this if matplotlib is still used directly for some reason, otherwise remove
            self.procs = list()
        
        # Initialize plot type registry (keep if config_manager is still the central place for this)
        if not hasattr(self.config_manager, '_plot_type_registry'):
            self.config_manager._plot_type_registry = {}

        # Initialize the new components
        self.data_extractor = DataExtractor(self.config_manager)
        self.plot_manager = PlotManager(self.config_manager, self.data_extractor)

    def process_data(self, dataset: xr.Dataset) -> dict:
        """
        Process raw dataset into visualization-ready format.
        
        Parameters
        ----------
            dataset
                Raw xarray Dataset to process
            
        Returns
        -------
            Dictionary containing processed data and metadata
        """
        self.logger.debug(f"Processing dataset with variables: {list(dataset.data_vars) if dataset else 'None'}")
        
        # Legacy GenericSource doesn't need special data processing
        # The actual processing is handled by DataExtractor and PlotManager
        if dataset is None:
            return {'dataset': None, 'type': 'generic', 'variables': [], 'dimensions': [], 'coordinates': []}
        
        processed_data = {
            'dataset': dataset,
            'type': 'generic',
            'variables': list(dataset.data_vars),
            'dimensions': list(dataset.dims),
            'coordinates': list(dataset.coords)
        }
        
        return processed_data
    
    def validate_data(self, dataset: xr.Dataset) -> bool:
        """
        Validate that the dataset is compatible with this data source.
        
        Parameters
        ----------
            dataset
                Dataset to validate
            
        Returns
        -------
            True if dataset is valid (GenericSource accepts any dataset)
        """
        if dataset is None:
            self.logger.warning("Dataset is None")
            return True  # Allow None datasets for legacy compatibility
        
        if not isinstance(dataset, xr.Dataset):
            self.logger.warning("Input is not an xarray Dataset")
            return True  # Still allow for legacy compatibility
        
        self.logger.debug("Dataset validation passed (GenericSource accepts all data)")
        return True

    def load_data_sources(self, file_list: list):
        pass

    def get_data_source(self, name: str) -> DataSource:
        pass

    def add_data_source(self, name: str, data_source: DataSource):
        pass

    def set_map_params(self, map_params):
        """Set the map parameters for plotting.

        Parameters
        ----------
            map_params
                Dictionary of map parameters from YAML parser
        """
        pass

    def __call__(self):
        self.plot_manager.plot()

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

    def register_plot_type(self, field_name, plot_type):
        """Register the plot type for a field."""
        self.config_manager._plot_type_registry[field_name] = plot_type
        
    def get_plot_type(self, field_name, default='xy'):
        """Get the plot type for a field."""
        return self.config_manager._plot_type_registry.get(field_name, default)
    
