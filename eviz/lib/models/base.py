"""
Generic data source base class for EViz library.

This module provides the foundational interface and common functionality
for all data source implementations in the EViz visualization system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
import logging
import xarray as xr

from eviz.lib.config.config_manager import ConfigManager
from eviz.lib.data.data_extractor import DataExtractor
from eviz.lib.autoviz.plotting.plot_manager import PlotManager


@dataclass
class GenericDataSource(ABC):
    """
    Abstract base class for all data source implementations.
    
    This class defines the interface that all data sources must implement
    to work with the EViz visualization system. It provides common
    functionality for data processing, plotting, and configuration management.
    
    Attributes:
        config_manager: Configuration manager instance
        plot_manager: Plot manager for handling visualization
        data_extractor: Data extraction utilities
    """
    
    config_manager: ConfigManager
    plot_manager: Optional[PlotManager] = None
    data_extractor: Optional[DataExtractor] = None
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for this data source."""
        return logging.getLogger(self.__class__.__name__)
    
    def __post_init__(self):
        """Initialize data source components."""
        if self.data_extractor is None:
            self.data_extractor = DataExtractor(self.config_manager)
        
        if self.plot_manager is None:
            self.plot_manager = PlotManager(self.config_manager, self.data_extractor)
    
    @abstractmethod
    def process_data(self, dataset: xr.Dataset) -> Dict[str, Any]:
        """
        Process raw dataset into visualization-ready format.
        
        Args:
            dataset: Input xarray Dataset
            
        Returns:
            Dictionary containing processed data
        """
        pass
    
    @abstractmethod
    def validate_data(self, dataset: xr.Dataset) -> bool:
        """
        Validate that the dataset is compatible with this data source.
        
        Args:
            dataset: Input xarray Dataset
            
        Returns:
            True if dataset is valid, False otherwise
        """
        pass
    
    def create_plots(self, dataset: xr.Dataset, field_name: str, plot_type: str) -> None:
        """
        Create plots for the specified field and plot type.
        
        Args:
            dataset: Input xarray Dataset
            field_name: Name of the field to plot
            plot_type: Type of plot to create (xy, xt, tx, etc.)
        """
        if field_name not in dataset.data_vars:
            raise ValueError(f"Field '{field_name}' not found in dataset")
        
        data_array = dataset[field_name]
        self.plot_manager.process_plot(data_array, field_name, 0, plot_type)
    
    def get_supported_plot_types(self) -> list[str]:
        """
        Get list of plot types supported by this data source.
        
        Returns:
            List of supported plot type strings
        """
        return ['xy', 'xt', 'tx', 'yz', 'scatter', 'box', 'polar']
    
    def __call__(self):
        """
        Execute the data source by running the plot manager.
        
        This method is called by the main Autoviz application to trigger
        the visualization process for this data source.
        """
        if self.plot_manager is None:
            raise RuntimeError("Plot manager not initialized. Call __post_init__ first.")
        
        self.logger.debug("Executing data source visualization")
        self.plot_manager.plot()