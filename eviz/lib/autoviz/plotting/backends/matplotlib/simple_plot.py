"""
Simple plotting functionality for basic visualization without specifications.

This module provides basic plotting capabilities for quick visualization of NetCDF data
when no SPECS file is provided.
"""
import logging
import math
from typing import Tuple, Optional

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

import eviz.lib.utils as u
from eviz.lib.config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


def simple_xy_plot(config: ConfigManager, data2d: xr.DataArray, dim1: xr.DataArray, 
                   dim2: xr.DataArray, field_name: str) -> None:
    """Create a simple xy (lat-lon) plot."""
    logger.debug(f"Creating simple XY plot for {field_name}")
    
    def shift_columns(arr):
        """Shift array columns to center longitude at 0."""
        m, n = arr.shape
        mid = math.ceil(n / 2)
        shifted_arr = np.zeros((m, n), dtype=arr.dtype)
        shifted_arr[:, :mid] = arr[:, mid:]
        shifted_arr[:, mid:] = arr[:, :mid]
        return shifted_arr

    if data2d is None:
        logger.error(f"No data available for field {field_name}")
        return

    if dim1 is None or dim2 is None:
        logger.error(f"Missing coordinate dimensions for field {field_name}")
        return

    # Calculate contour levels
    dmin = data2d.min(skipna=True).values
    dmax = data2d.max(skipna=True).values
    
    if dmin < 1:  # For small values, use more precision
        levels = np.linspace(dmin, dmax, 10)
    else:
        levels = np.around(np.linspace(dmin, dmax, 10), decimals=1)

    # Create the plot
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 6))
    
    # Check if this is global data that needs longitude shifting
    source_name = config.input_config.source_names[0] if config.input_config.source_names else 'gridded'
    
    if source_name in ['lis', 'wrf']:
        # Regional data - no shifting needed
        cf = ax.contourf(dim1.values, dim2.values, data2d.values, cmap=config.output_config.colormap)
        co = ax.contour(dim1.values, dim2.values, data2d.values, levels, 
                       linewidths=(1,), colors='k')
    else:
        # Global data - apply longitude shifting for better display
        cf = ax.contourf(dim1.values, dim2.values, shift_columns(data2d.values), 
                        cmap=config.output_config.colormap)
        co = ax.contour(dim1.values, dim2.values, shift_columns(data2d.values), levels,
                       linewidths=(1,), colors='w')
    
    # Add contour labels
    ax.clabel(co, fmt='%2.1f', fontsize=8)
    
    # Add colorbar
    cbar = fig.colorbar(cf, ax=ax, orientation='vertical', pad=0.05, fraction=0.05)
    
    # Set labels and title
    ax.set_xlabel(dim1.name or 'Longitude')
    ax.set_ylabel(dim2.name or 'Latitude')
    
    # Set title
    if hasattr(data2d, 'long_name') and data2d.long_name:
        ax.set_title(data2d.long_name)
    elif hasattr(data2d, 'standard_name') and data2d.standard_name:
        ax.set_title(data2d.standard_name)
    else:
        ax.set_title(field_name)
    
    # Set colorbar label
    if hasattr(data2d, 'units') and data2d.units:
        cbar.set_label(data2d.units)
    
    # Adjust aspect ratio
    u.squeeze_fig_aspect(fig)
    
    # Save or show the plot
    if config.output_config.print_to_file:
        output_path = f"{config.output_config.output_dir}/{field_name}_xy_simple.{config.output_config.print_format}"
        fig.savefig(output_path, dpi=config.output_config.dpi, bbox_inches='tight')
        logger.info(f"Saved XY plot: {output_path}")
        plt.close(fig)
    else:
        plt.show()


def simple_yz_plot(config: ConfigManager, data2d: xr.DataArray, dim1: xr.DataArray, 
                   dim2: xr.DataArray, field_name: str) -> None:
    """Create a simple yz (vertical profile) plot."""
    logger.debug(f"Creating simple YZ plot for {field_name}")
    
    if data2d is None:
        logger.error(f"No data available for field {field_name}")
        return

    # Create the plot
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 6))
    
    # For yz plots, we need to handle multi-dimensional data intelligently
    plot_data = data2d
    
    # Reduce to 2D if necessary
    if len(plot_data.dims) > 2:
        logger.debug(f"Data has {len(plot_data.dims)} dimensions: {plot_data.dims}")
        # Take first time slice if present
        if 'time' in plot_data.dims:
            plot_data = plot_data.isel(time=0)
            logger.debug("Selected first time slice")
        
        # If still more than 2D, take mean over longitude for zonal mean
        if len(plot_data.dims) > 2 and 'lon' in plot_data.dims:
            plot_data = plot_data.mean(dim='lon', skipna=True)
            logger.debug("Averaged over longitude")
        
        # If still more than 2D, take first slice of remaining dimensions
        while len(plot_data.dims) > 2:
            dim_to_slice = plot_data.dims[0]
            plot_data = plot_data.isel({dim_to_slice: 0})
            logger.debug(f"Selected first slice of {dim_to_slice}")
    
    # Now we should have 2D data
    if len(plot_data.dims) == 2:
        # Find which dimensions we have
        dims = plot_data.dims
        coords = plot_data.coords
        
        # Try to identify vertical and horizontal coordinates
        lat_dim = None
        lev_dim = None
        
        for dim in dims:
            if 'lat' in dim.lower() or 'y' in dim.lower():
                lat_dim = dim
            elif 'lev' in dim.lower() or 'z' in dim.lower() or 'level' in dim.lower():
                lev_dim = dim
        
        if lat_dim and lev_dim:
            # Create lat-level cross section
            lat_coord = coords[lat_dim]
            lev_coord = coords[lev_dim]
            
            # Transpose data if needed to match coordinate order
            if plot_data.dims[0] != lat_dim:
                plot_data = plot_data.transpose(lat_dim, lev_dim)
            
            cf = ax.contourf(lat_coord.values, lev_coord.values, plot_data.values.T, 
                           cmap=config.output_config.colormap, levels=15)
            co = ax.contour(lat_coord.values, lev_coord.values, plot_data.values.T, 
                          colors='k', linewidths=0.5, levels=15)
            
            ax.set_xlabel('Latitude')
            ax.set_ylabel('Level')
            
            # Add colorbar
            cbar = fig.colorbar(cf, ax=ax, orientation='vertical', pad=0.05, fraction=0.05)
            if hasattr(plot_data, 'units') and plot_data.units:
                cbar.set_label(plot_data.units)
        else:
            # Fallback: just plot as line plot of the first dimension
            if len(plot_data.shape) == 2:
                # Take mean over one dimension
                plot_1d = plot_data.mean(dim=plot_data.dims[0])
                coord_1d = plot_data.coords[plot_data.dims[1]]
            else:
                plot_1d = plot_data
                coord_1d = plot_data.coords[plot_data.dims[0]]
            
            ax.plot(plot_1d.values, coord_1d.values)
            ax.set_xlabel(field_name)
            ax.set_ylabel(coord_1d.name or 'Coordinate')
    
    elif len(plot_data.dims) == 1:
        # 1D profile plot
        coord = plot_data.coords[plot_data.dims[0]]
        ax.plot(plot_data.values, coord.values)
        ax.set_xlabel(field_name)
        ax.set_ylabel(coord.name or plot_data.dims[0])
    
    else:
        logger.error(f"Cannot plot data with shape {plot_data.shape}")
        plt.close(fig)
        return
    
    # Set title
    if hasattr(plot_data, 'long_name') and plot_data.long_name:
        ax.set_title(plot_data.long_name)
    elif hasattr(plot_data, 'standard_name') and plot_data.standard_name:
        ax.set_title(plot_data.standard_name)
    else:
        ax.set_title(field_name)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save or show the plot
    if config.output_config.print_to_file:
        output_path = f"{config.output_config.output_dir}/{field_name}_yz_simple.{config.output_config.print_format}"
        fig.savefig(output_path, dpi=config.output_config.dpi, bbox_inches='tight')
        logger.info(f"Saved YZ plot: {output_path}")
        plt.close(fig)
    else:
        plt.show()


class SimplePlotter:
    """Simple plotter for basic visualization without specifications."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def plot(self, config: ConfigManager, field_name: str, plot_type: str, data: xr.DataArray, dataset: xr.Dataset = None):
        """Create a simple plot based on plot type."""
        self.logger.info(f"Creating simple {plot_type} plot for {field_name}")

        # Handle CSV plot types (bar, pie, hist)
        if plot_type in ['bar', 'pie', 'hist']:
            return self._plot_csv(config, field_name, plot_type, data, dataset)

        if data is None:
            self.logger.error(f"No data provided for field {field_name}")
            return

        # Get coordinate dimensions
        dims = data.dims
        coords = data.coords
        
        if plot_type == 'xy':
            # Find longitude and latitude coordinates
            lon_coord = None
            lat_coord = None
            
            for dim in dims:
                coord = coords[dim]
                if 'lon' in dim.lower() or 'x' in dim.lower():
                    lon_coord = coord
                elif 'lat' in dim.lower() or 'y' in dim.lower():
                    lat_coord = coord
            
            if lon_coord is not None and lat_coord is not None:
                # For xy plots, we need 2D data
                if len(dims) > 2:
                    # Take first time slice and/or first level
                    for dim in dims:
                        if dim not in [lon_coord.name, lat_coord.name]:
                            data = data.isel({dim: 0})
                
                simple_xy_plot(config, data, lon_coord, lat_coord, field_name)
            else:
                self.logger.error(f"Could not find longitude/latitude coordinates for {field_name}")
                
        elif plot_type == 'yz':
            # Find vertical and horizontal coordinates
            vert_coord = None
            other_coord = None
            
            for dim in dims:
                coord = coords[dim]
                if 'lev' in dim.lower() or 'z' in dim.lower() or 'level' in dim.lower():
                    vert_coord = coord
                elif other_coord is None:
                    other_coord = coord
            
            if vert_coord is not None and other_coord is not None:
                # For yz plots, we need 2D data
                if len(dims) > 2:
                    # Take slices of other dimensions
                    for dim in dims:
                        if dim not in [vert_coord.name, other_coord.name]:
                            data = data.isel({dim: 0})
                
                simple_yz_plot(config, data, other_coord, vert_coord, field_name)
            else:
                self.logger.error(f"Could not find appropriate coordinates for YZ plot of {field_name}")
                
        else:
            self.logger.warning(f"Simple plot type '{plot_type}' not supported. Defaulting to XY plot.")
            # Default to xy plot
            self.plot(config, field_name, 'xy', data, dataset)

    def _plot_csv(self, config: ConfigManager, field_name: str, plot_type: str, data: xr.DataArray, dataset: xr.Dataset):
        """Create CSV plots (bar, pie, hist) using the PlotterFactory."""
        import pandas as pd
        from eviz.lib.autoviz.plotting.factory import PlotterFactory
        from unittest.mock import MagicMock

        self.logger.info(f"Creating CSV {plot_type} plot for {field_name}")

        # Convert xarray Dataset to pandas DataFrame
        if dataset is not None:
            df = dataset.to_dataframe().reset_index()
            self.logger.debug(f"Converted dataset to DataFrame with shape {df.shape}")
            self.logger.debug(f"DataFrame columns: {list(df.columns)}")
        elif data is not None:
            df = data.to_dataframe().reset_index()
            self.logger.debug(f"Converted data to DataFrame with shape {df.shape}")
        else:
            self.logger.error(f"No data available for {field_name}")
            return

        # Create plotter using factory
        try:
            plotter = PlotterFactory.create_plotter(plot_type, 'matplotlib')
        except ValueError as e:
            self.logger.error(f"Cannot create plotter: {e}")
            return

        # Create figure
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)

        # Mock figure object for compatibility
        mock_fig = MagicMock()
        mock_fig.get_axes = MagicMock(return_value=[ax])

        # Get plot options from config if available
        plot_options = {}

        # Prepare data tuple
        data_to_plot = (df, field_name, plot_type, 0, mock_fig, plot_options)

        # Create the plot
        try:
            plotter.plot(config, data_to_plot)
        except Exception as e:
            self.logger.error(f"Error creating {plot_type} plot: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            plt.close(fig)
            return

        # Save the plot
        if config.output_config.print_to_file:
            output_path = f"{config.output_config.output_dir}/{field_name}_{plot_type}.{config.output_config.print_format}"
            fig.savefig(output_path, dpi=config.output_config.dpi, bbox_inches='tight')
            self.logger.info(f"Saved {plot_type} plot: {output_path}")
            plt.close(fig)
        else:
            plt.show()