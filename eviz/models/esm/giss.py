"""
GISS ModelE support for EViz.

This module provides support for GISS ModelE output files which have a unique structure:
- Dimensions: im (longitude), jm (latitude), lm (vertical), ntimemax (time)
- No coordinate arrays - only dimension sizes
- Variables may not have time dimension (single time slice)
"""

import logging
from dataclasses import dataclass

import numpy as np
import xarray as xr

from eviz.models.gridded_source import GriddedSource


@dataclass
class Giss(GriddedSource):
    """Define GISS ModelE-specific model data and functions.

    GISS ModelE has a unique NetCDF structure:
    - Uses dimension names: im, jm, lm, ntimemax instead of standard names
    - No coordinate arrays (lat, lon, lev, time) - only dimension sizes
    - Variables may be 3D (lm, jm, im) without time dimension
    """

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

    def __post_init__(self):
        self.logger.info("Initializing GISS ModelE data source")
        self.season = None
        super().__post_init__()

    def post_process_dataset(self, dataset: xr.Dataset) -> xr.Dataset:
        """Post-process GISS dataset to add missing coordinate arrays.

        Parameters
        ----------
            dataset
                Raw GISS dataset

        Returns
        -------
            Dataset with synthetic coordinate arrays added
        """
        self.logger.info("Post-processing GISS dataset to add coordinate arrays")

        # Create synthetic coordinate arrays based on dimension sizes
        coords_to_add = {}

        # Longitude coordinate (im dimension)
        if "im" in dataset.dims and "im" not in dataset.coords:
            im_size = dataset.dims["im"]
            # Standard global longitude grid: 0 to 360-dx
            lon_values = np.linspace(0, 360 - 360 / im_size, im_size)
            coords_to_add["lon"] = ("im", lon_values)
            self.logger.debug(
                f"Created longitude coordinate: {im_size} points, range {lon_values.min():.1f} to {lon_values.max():.1f}"
            )

        # Latitude coordinate (jm dimension)
        if "jm" in dataset.dims and "jm" not in dataset.coords:
            jm_size = dataset.dims["jm"]
            # Standard global latitude grid: -90 to 90
            lat_values = np.linspace(-90 + 90 / jm_size, 90 - 90 / jm_size, jm_size)
            coords_to_add["lat"] = ("jm", lat_values)
            self.logger.debug(
                f"Created latitude coordinate: {jm_size} points, range {lat_values.min():.1f} to {lat_values.max():.1f}"
            )

        # Vertical coordinate (lm dimension)
        if "lm" in dataset.dims and "lm" not in dataset.coords:
            lm_size = dataset.dims["lm"]
            # Use level indices as pressure levels (could be improved with actual values)
            lev_values = np.arange(1, lm_size + 1)
            coords_to_add["lev"] = ("lm", lev_values)
            self.logger.debug(f"Created level coordinate: {lm_size} levels")

        # Time coordinate (ntimemax dimension)
        if "ntimemax" in dataset.dims and "ntimemax" not in dataset.coords:
            ntimemax_size = dataset.dims["ntimemax"]
            # Create time indices
            time_values = np.arange(ntimemax_size)
            coords_to_add["time"] = ("ntimemax", time_values)
            self.logger.debug(f"Created time coordinate: {ntimemax_size} time steps")

        # Add the coordinate arrays to the dataset
        if coords_to_add:
            dataset = dataset.assign_coords(coords_to_add)
            self.logger.info(
                f"Added {len(coords_to_add)} coordinate arrays: {list(coords_to_add.keys())}"
            )

        # Handle variables that don't have time dimension but should
        dataset = self._add_time_dimension_if_needed(dataset)

        return dataset

    def _add_time_dimension_if_needed(self, dataset: xr.Dataset) -> xr.Dataset:
        """Add time dimension to variables that should have it but don't.

        For GISS data, some variables like 't' are 3D (lm, jm, im) but represent
        a single time slice. For plotting purposes, we may need to add a time dimension.

        Parameters
        ----------
            dataset
                Dataset to process

        Returns
        -------
            Dataset with time dimensions added where appropriate
        """
        variables_to_process = []

        for var_name, var in dataset.data_vars.items():
            # Check if variable has spatial dimensions but no time dimension
            has_spatial = any(dim in var.dims for dim in ["lm", "jm", "im"])
            has_time = "ntimemax" in var.dims

            if has_spatial and not has_time:
                # This is likely a 3D spatial variable that represents a time slice
                variables_to_process.append(var_name)

        if variables_to_process:
            self.logger.debug(
                f"Variables without time dimension: {variables_to_process}"
            )
            # Note: We don't automatically add time dimensions since it changes the data structure
            # The plotting system should handle 3D variables appropriately

        return dataset

    def preprocess_data(self, data_array: xr.DataArray) -> xr.DataArray:
        """Preprocess individual data arrays for GISS-specific handling.

        Parameters
        ----------
            data_array
                Input data array

        Returns
        -------
            Processed data array
        """
        # If the data array has no time dimension but plotting expects one,
        # we can add a singleton time dimension
        if hasattr(data_array, "dims"):
            has_spatial = any(dim in data_array.dims for dim in ["lm", "jm", "im"])
            has_time = any(dim in data_array.dims for dim in ["ntimemax", "time"])

            if has_spatial and not has_time:
                self.logger.debug(
                    f"Variable {data_array.name} has spatial dimensions but no time - treating as single time slice"
                )
                # Add a singleton time dimension
                data_array = data_array.expand_dims({"time": 1})
                self.logger.debug(
                    f"Added singleton time dimension, new shape: {data_array.shape}"
                )

        return data_array
