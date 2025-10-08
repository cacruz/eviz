"""
Categorical data source for handling tabular/CSV data visualizations.

This module provides functionality for handling categorical and tabular data
from CSV files and similar sources, supporting various statistical plot types
like bar charts, histograms, scatter plots, box plots, and pie charts.
"""

from dataclasses import dataclass
import logging
import pandas as pd
import xarray as xr
from eviz.lib.models.base import GenericDataSource


@dataclass
class CategoricalDataSource(GenericDataSource):
    """
    Data source for categorical and tabular data visualizations.

    This class handles CSV and other tabular data formats, providing
    specialized functionality for statistical and categorical plots:

    - Bar charts (categorical aggregations)
    - Histograms (distribution analysis)
    - Scatter plots (correlation analysis)
    - Box plots (statistical summaries)
    - Pie charts (proportion visualization)

    Unlike gridded data sources which work with multi-dimensional arrays,
    this class is optimized for tabular data with named columns and rows,
    where each column represents a variable and each row an observation.
    """

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

    def __post_init__(self):
        self.logger.debug("Initializing CategoricalDataSource")
        super().__post_init__()

    def process_data(self, dataset: xr.Dataset) -> dict:
        """
        Process raw dataset into visualization-ready format.

        For categorical data, we convert the xarray Dataset to a pandas
        DataFrame for easier manipulation of tabular data.

        Args:
            dataset: Raw xarray Dataset (typically loaded from CSV)

        Returns:
            Dictionary containing processed data and metadata
        """
        self.logger.debug(f"Processing categorical dataset with variables: {list(dataset.data_vars)}")

        # Convert to DataFrame for easier categorical/tabular operations
        df = dataset.to_dataframe().reset_index()

        processed_data = {
            'dataset': dataset,
            'dataframe': df,
            'type': 'categorical',
            'variables': list(dataset.data_vars),
            'columns': list(df.columns),
            'row_count': len(df)
        }

        self.logger.debug(f"Processed categorical data: {len(df)} rows, {len(df.columns)} columns")

        return processed_data

    def validate_data(self, dataset: xr.Dataset) -> bool:
        """
        Validate that the dataset is compatible with categorical data processing.

        Args:
            dataset: Dataset to validate

        Returns:
            True if dataset is valid for categorical operations
        """
        if dataset is None or not isinstance(dataset, xr.Dataset):
            self.logger.error("Invalid dataset: must be an xarray Dataset")
            return False

        # Check that we have at least one data variable
        if len(dataset.data_vars) == 0:
            self.logger.error("Dataset has no data variables")
            return False

        # For categorical data, we expect 1D or 2D data (tabular format)
        # Check dimensions are reasonable
        total_dims = sum(1 for dim in dataset.dims.values() if dim > 1)
        if total_dims > 2:
            self.logger.warning(
                f"Dataset has {total_dims} dimensions with size > 1. "
                "Categorical data typically has 1-2 dimensions."
            )

        return True

    def get_supported_plot_types(self) -> list[str]:
        """
        Get list of plot types supported by categorical data source.

        Returns:
            List of supported plot type strings
        """
        return ['bar', 'hist', 'scatter', 'box', 'pie']

    def __call__(self):
        """Execute the categorical data visualization process."""
        self.logger.debug("Executing categorical data visualization")

        if self.plot_manager is None:
            raise RuntimeError("Plot manager not initialized")

        # Use PlotManager to handle the plotting
        self.plot_manager.plot()
