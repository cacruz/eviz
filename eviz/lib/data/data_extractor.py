import logging
import numpy as np
import pandas as pd
import xarray as xr
from eviz.lib.config.config_manager import ConfigManager
from eviz.lib.data.utils import apply_conversion, apply_mean, apply_zsum, subset_region

class DataExtractor:
    """
    Handles the extraction and preparation of data for various plot types.
    """
    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
    
    def _get_dimension_size(self, data_array, dim_name):
        """
        Safely get the size of a dimension, whether it's a coordinate or just a dimension.
        
        Args:
            data_array: xarray DataArray
            dim_name: Name of dimension
            
        Returns:
            int: Size of dimension, or 0 if not found
        """
        if dim_name is None:
            return 0
            
        # First check if it's a dimension
        if dim_name in data_array.dims:
            return data_array.sizes[dim_name]
        # Then check if it's a coordinate
        elif dim_name in data_array.coords:
            return data_array[dim_name].size
        else:
            self.logger.debug(f"Dimension '{dim_name}' not found in data array. Available dims: {list(data_array.dims)}, Available coords: {list(data_array.coords.keys())}")
            return 0
          
    def _extract_scatter_data(self, data_array, time_level=None):
        """
        Extract data for scatter plot.

        Returns:
            tuple: (values, x, y)
        """
        self.logger.debug(f"Starting scatter data extraction for time_level: {time_level}")
        
        xc_dim = self.config_manager.get_model_dim_name('xc') or 'lon'
        yc_dim = self.config_manager.get_model_dim_name('yc') or 'lat'
        tc_dim = self.config_manager.get_model_dim_name('tc') or 'time'

        d_temp = data_array.copy()

        # Handle time dimension
        if tc_dim in d_temp.dims:
            num_tc = self._get_dimension_size(d_temp, tc_dim)
            self.logger.debug(f"Time dimension has {num_tc} levels")
            
            if time_level == 'all':
                self.logger.debug("'all' time levels requested, processing one at a time")
                time_level = 0
                
            if isinstance(time_level, int):
                actual_time_lev = time_level if time_level >= 0 else num_tc + time_level
                if 0 <= actual_time_lev < num_tc:
                    d_temp = d_temp.isel({tc_dim: actual_time_lev})
                    self.logger.debug(f"Selected time level {actual_time_lev}")
                else:
                    d_temp = d_temp.isel({tc_dim: 0})
                    self.logger.debug("Invalid time level, using first time step")

        # Squeeze to 2D
        d2d = d_temp.squeeze()
        self.logger.debug(f"After squeeze shape: {d2d.shape}")
        
        try:
            # Try to get x/y coordinates
            if xc_dim in d2d.coords and yc_dim in d2d.coords:
                self.logger.debug("Found coordinate dimensions")
                x = d2d[xc_dim].values
                y = d2d[yc_dim].values
                
                self.logger.debug(f"Coordinate shapes - x: {x.shape}, y: {y.shape}")
                
                # If x/y are 2D (swath), flatten both
                if x.ndim == 2 and y.ndim == 2:
                    self.logger.debug("Processing 2D coordinates (swath)")
                    x_flat = x.flatten()
                    y_flat = y.flatten()
                    values = d2d.values.flatten()
                else:
                    # Check if coordinates are already paired (same length as data)
                    data_flat = d2d.values.flatten()
                    if len(x) == len(data_flat) and len(y) == len(data_flat):
                        self.logger.debug("Processing 1D coordinates (already paired)")
                        x_flat = x
                        y_flat = y  
                        values = data_flat
                    else:
                        self.logger.debug("Processing 1D coordinates (regular grid - creating meshgrid)")
                        xx, yy = np.meshgrid(x, y)
                        x_flat = xx.flatten()
                        y_flat = yy.flatten()
                        values = data_flat
            else:
                self.logger.debug("No coordinate dimensions found, using indices")
                values = d2d.values.flatten()
                shape = d2d.shape
                y_grid, x_grid = np.indices(shape)
                x_flat = x_grid.flatten()
                y_flat = y_grid.flatten()

            # Log array lengths before masking
            self.logger.debug(f"Array lengths before masking - x: {len(x_flat)}, y: {len(y_flat)}, values: {len(values)}")

            # Verify all arrays have the same length before masking
            if not (len(x_flat) == len(y_flat) == len(values)):
                self.logger.error(f"Dimension mismatch: x({len(x_flat)}), y({len(y_flat)}), values({len(values)})")
                return None, None, None

            # Remove NaNs
            mask = ~np.isnan(values)
            x_flat = x_flat[mask]
            y_flat = y_flat[mask]
            values = values[mask]

            self.logger.debug(f"After masking - valid points: {len(values)}")

            if len(values) == 0:
                self.logger.warning(f"No valid data points after removing NaNs")
                return None, None, None

            return values, x_flat, y_flat

        except Exception as e:
            self.logger.error(f"Error in _extract_scatter_data: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None, None, None

    # DATA SLICE PROCESSING METHODS
    def _extract_yz_data(self, data_array, time_level):
        """ Extract YZ slice (zonal mean) from a DataArray

        Note:
            Assume input DataArray is at most 4-dimensional (time, lev, lon, lat)
            and return a 2D (lat, lev) slice
        """
        if data_array is None:
            return None

        xc_dim = self.config_manager.get_model_dim_name('xc')
        tc_dim = self.config_manager.get_model_dim_name('tc')
        zc_dim = self.config_manager.get_model_dim_name('zc')

        if not zc_dim or zc_dim not in data_array.dims:
            self.logger.error(
                f"Cannot create YZ plot: no vertical dimension found in data for {data_array.name}")
            return None

        if xc_dim and xc_dim in data_array.dims:
            zonal_mean = data_array.mean(dim=xc_dim)
        else:
            self.logger.error(
                f"Could not find any longitude dimension for zonal mean in {data_array.name}")
            return None

        time_ave = self.config_manager.ax_opts.get('tave', False)
        num_times = zonal_mean[tc_dim].size
        if time_ave:
            self.logger.debug(f"Averaging over {num_times} time levels.")
            zonal_mean = apply_mean(self.config_manager, zonal_mean)
        else:
            if isinstance(time_level, int) and time_level < num_times:
                zonal_mean = zonal_mean.isel({tc_dim: time_level})
            else:
                zonal_mean = zonal_mean.isel({tc_dim: 0})

        zonal_mean = zonal_mean.squeeze()
        zonal_mean.attrs = data_array.attrs.copy()
        zonal_mean = self._select_yrange(zonal_mean, data_array.name)

        return apply_conversion(self.config_manager, zonal_mean, data_array.name)

    def _extract_xy_data(self, data_array, time_level, level=None):
        """ Extract XY slice (latlon) from a DataArray

        Note:
            Assume input DataArray is at most 4-dimensional (time, lev, lon, lat)
            and return a 2D (lon, lat) slice
        """
        if data_array is None:
            return None

        tc_dim = self.config_manager.get_model_dim_name_for_data('tc', data_array)
        zc_dim = self.config_manager.get_model_dim_name_for_data('zc', data_array)

        d_temp = data_array.copy()
        num_tc = self._get_dimension_size(d_temp, tc_dim)
        
        if num_tc == 0:
            # Time dimension not found - data may have already been time-sliced
            self.logger.debug(f"Time dimension '{tc_dim}' not found in data array - assuming data is already time-sliced")
        elif num_tc > 1 and not self.config_manager.ax_opts.get('tave', False):
            self.logger.debug(f"Selecting time level: {time_level}")                
            # Handle negative indices (e.g., -1 for the last time level)
            if isinstance(time_level, int):
                # Convert negative index to positive if needed
                actual_time_lev = time_level if time_level >= 0 else num_tc + time_level
                # Check if the index is valid
                if 0 <= actual_time_lev < num_tc:
                    d_temp = d_temp.isel({tc_dim: actual_time_lev})
                else:
                    d_temp = d_temp.isel({tc_dim: 0})
            else:
                self.logger.warning(f"No time dimension found matching {tc_dim}")

        # Conditionally squeeze: only squeeze dimensions that are not 'zc_dim' if zave/zsum is active
        dims_to_squeeze = [dim for dim in d_temp.dims if d_temp[dim].size == 1]
        if self.config_manager.ax_opts.get('zsum', False) or self.config_manager.ax_opts.get('zave', False):
            if zc_dim and zc_dim in dims_to_squeeze: # Check if zc_dim exists and is a singleton
                dims_to_squeeze.remove(zc_dim) # Do not squeeze zc_dim if zsum/zave is active
 
        d_temp = d_temp.squeeze(dims_to_squeeze) if dims_to_squeeze else d_temp

        has_vertical_dim = zc_dim and zc_dim in d_temp.dims
        if has_vertical_dim:
            self.logger.debug(f"Selected vertical level: {level}")                
            # No level specified, use the first level
            if self.config_manager.ax_opts.get('zsum', False):
                self.logger.debug("Summing over vertical levels.")
                data2d_zsum = apply_zsum(self.config_manager, d_temp, data_array.name)
                data2d_zsum.attrs = data_array.attrs.copy()
                # Now it's 2D:
                return data2d_zsum
            elif self.config_manager.ax_opts.get('zave', False):
                self.logger.debug("Averaging over vertical levels.")
                data2d = apply_mean(self.config_manager, d_temp, level='all')
                data2d.attrs = data_array.attrs.copy()
                # Now it's 2D:
                return data2d
            elif level is not None:
                try:
                    # First try exact matching
                    if level in d_temp[zc_dim].values:
                        lev_idx = np.where(d_temp[zc_dim].values == level)[0][0]
                        d_temp = d_temp.isel({zc_dim: lev_idx})
                    else:
                        # Try nearest neighbor
                        lev_idx = np.abs(d_temp[zc_dim].values - level).argmin()
                        d_temp = d_temp.isel({zc_dim: lev_idx})
                except Exception as e:
                    self.logger.error(f"Error selecting level {level}: {e}")
                    if d_temp[zc_dim].size > 0:
                        d_temp = d_temp.isel({zc_dim: 0})
            else:
                if d_temp[zc_dim].size > 0:
                    d_temp = d_temp.isel({zc_dim: 0})
        elif level is not None:
            self.logger.debug(
                f"Level {level} specified but no vertical dimension found in data. Using data as is.") 

        # Almost done...
        data2d = d_temp
        if self.config_manager.ax_opts.get('tave', False):
            if tc_dim is not None and tc_dim in data2d.dims:
                num_tc = data2d[tc_dim].size
                if num_tc > 1:
                    self.logger.debug(f"Averaging over {num_tc} time levels.")
                    data2d = apply_mean(self.config_manager, data2d, level)
                    data2d.attrs = data_array.attrs.copy()
                    return apply_conversion(self.config_manager, data2d, data_array.name)
            else:
                self.logger.debug(f"Time averaging requested but no time dimension found (tc_dim={tc_dim}). Skipping time averaging.")

        # Check for NaN values only if data is numeric
        if np.issubdtype(data2d.values.dtype, np.number):
            if np.isnan(data2d.values).any():
                self.logger.debug(
                    f"Output contains NaN values: {np.sum(np.isnan(data2d.values))} NaNs")
        else:
            self.logger.debug(f"Skipping NaN check for non-numeric data type: {data2d.values.dtype}")

        data2d.attrs = data_array.attrs.copy()
        return apply_conversion(self.config_manager, data2d, data_array.name)

    def _extract_xt_data(self, data_array, time_lev):
        """ Extract time-series from a DataArray

        Note:
            Assume input DataArray is at most 4-dimensional (time, lev, lon, lat)
            and return a 1D (time) series
        """
        if data_array is None:
            return None

        tc_dim = self.config_manager.get_model_dim_name('tc')
        zc_dim = self.config_manager.get_model_dim_name('zc')
        xc_dim = self.config_manager.get_model_dim_name('xc')
        yc_dim = self.config_manager.get_model_dim_name('yc')
        num_times = self._get_dimension_size(data_array, tc_dim)
        self.logger.debug(f"'{data_array.name}' field has {num_times} time levels")

        data2d = data_array.copy()

        if isinstance(time_lev, list):
            self.logger.debug(f"Computing time series on {time_lev} time range")
            try:
                if tc_dim in data2d.dims:
                    data2d = data2d.isel({tc_dim: slice(*time_lev)})
                else:
                    if 'time' in data2d.dims:
                        data2d = data2d.isel(time=slice(*time_lev))
            except (AttributeError, KeyError, IndexError) as e:
                self.logger.error(f"Error slicing time dimension: {e}")

        # Apply averaging or selection based on specs
        if self.config_manager.spec_data and data_array.name in self.config_manager.spec_data:
            spec = self.config_manager.spec_data[data_array.name]
            if 'xtplot' in spec and 'mean_type' in spec['xtplot']:
                mean_type = spec['xtplot']['mean_type']

                self.logger.info(f"Averaging method: {mean_type}")

                if mean_type == 'point_sel':
                    # Select a single point
                    try:
                        xc = spec['xtplot']['point_sel'][0]
                        yc = spec['xtplot']['point_sel'][1]

                        if xc_dim in data2d.coords and yc_dim in data2d.coords:
                            data2d = data2d.sel({xc_dim: xc, yc_dim: yc},
                                                method='nearest')
                        else:
                            if 'lon' in data2d.coords and 'lat' in data2d.coords:
                                data2d = data2d.sel(lon=xc, lat=yc, method='nearest')
                            else:
                                self.logger.error(
                                    "Could not find coordinates for point selection")
                    except (KeyError, ValueError) as e:
                        self.logger.error(f"Error in point selection: {e}")

                elif mean_type == 'area_sel':
                    # Select an area and compute mean
                    try:
                        x1 = spec['xtplot']['area_sel'][0]
                        x2 = spec['xtplot']['area_sel'][1]
                        y1 = spec['xtplot']['area_sel'][2]
                        y2 = spec['xtplot']['area_sel'][3]
                        if xc_dim in data2d.coords and yc_dim in data2d.coords:
                            data2d = subset_region(data2d, [x1, x2, y1, y2])

                            if xc_dim in data2d.dims and yc_dim in data2d.dims:
                                data2d = data2d.mean(dim=(xc_dim, yc_dim))
                        else:
                            if 'lon' in data2d.coords and 'lat' in data2d.coords:
                                data2d = data2d.sel(lon=slice(x1, x2), lat=slice(y1, y2))

                                # Compute mean over spatial dimensions
                                if 'lon' in data2d.dims and 'lat' in data2d.dims:
                                    data2d = data2d.mean(dim=('lon', 'lat'))
                            else:
                                self.logger.error(
                                    "Could not find coordinates for area selection")
                    except (KeyError, ValueError) as e:
                        self.logger.error(f"Error in area selection: {e}")

                elif mean_type in ['year', 'season', 'month']:
                    # Group by time period
                    try:
                        if tc_dim in data2d.dims:
                            time_attr = f"{tc_dim}.{mean_type}"
                            data2d = data2d.groupby(time_attr).mean(dim=tc_dim)
                        else:
                            if 'time' in data2d.dims:
                                time_attr = f"time.{mean_type}"
                                data2d = data2d.groupby(time_attr).mean(dim='time')
                            else:
                                self.logger.error(
                                    "Could not find time dimension for grouping")
                    except (AttributeError, KeyError) as e:
                        self.logger.error(f"Error in time grouping: {e}")

                elif mean_type == 'rolling':
                    # Apply rolling mean
                    try:
                        window_size = spec['xtplot'].get('window_size', 5)
                        self.logger.debug(f" -- smoothing window size: {window_size}")

                        if tc_dim in data2d.dims:
                            data2d = data2d.rolling({tc_dim: window_size},
                                                    center=True).mean()
                        else:
                            if 'time' in data2d.dims:
                                data2d = data2d.rolling(time=window_size,
                                                        center=True).mean()
                            else:
                                self.logger.error(
                                    "Could not find time dimension for rolling mean")
                    except (AttributeError, KeyError) as e:
                        self.logger.error(f"Error in rolling mean: {e}")

                else:
                    # General mean over all dimensions except time
                    try:
                        # Get all dimensions except time
                        if tc_dim in data2d.dims:
                            non_time_dims = [dim for dim in data2d.dims if dim != tc_dim]
                            if non_time_dims:
                                data2d = data2d.mean(dim=non_time_dims)
                        else:
                            if 'time' in data2d.dims:
                                non_time_dims = [dim for dim in data2d.dims if
                                                 dim != 'time']
                                if non_time_dims:
                                    data2d = data2d.mean(dim=non_time_dims)
                            else:
                                self.logger.error(
                                    "Could not find time dimension for general mean")
                    except (AttributeError, KeyError) as e:
                        self.logger.error(f"Error in general mean: {e}")

            if 'xtplot' in spec and 'level' in spec['xtplot']:
                level = int(spec['xtplot']['level'])
                self.logger.debug(f"Selecting level {level}")

                if zc_dim and zc_dim in data2d.dims:
                    try:
                        # Try exact matching
                        if level in data2d[zc_dim].values:
                            lev_idx = np.where(data2d[zc_dim].values == level)[0][0]
                            data2d = data2d.isel({zc_dim: lev_idx}).squeeze()
                            self.logger.debug(
                                f"Selected exact level {level} at index {lev_idx}")
                        else:
                            # Try nearest neighbor
                            lev_idx = np.abs(data2d[zc_dim].values - level).argmin()
                            data2d = data2d.isel({zc_dim: lev_idx}).squeeze()
                    except (AttributeError, KeyError, IndexError) as e:
                        self.logger.error(f"Error selecting level {level}: {e}")
                        if data2d[zc_dim].size > 0:
                            data2d = data2d.isel({zc_dim: 0}).squeeze()
                else:
                    for lev_name in ['lev', 'level', 'plev']:
                        if lev_name in data2d.dims:
                            try:
                                if level in data2d[lev_name].values:
                                    lev_idx = \
                                        np.where(data2d[lev_name].values == level)[0][0]
                                    data2d = data2d.isel({lev_name: lev_idx}).squeeze()
                                    break
                                else:
                                    lev_idx = np.abs(
                                        data2d[lev_name].values - level).argmin()
                                    data2d = data2d.isel({lev_name: lev_idx}).squeeze()
                                    break
                            except (AttributeError, KeyError, IndexError) as e:
                                self.logger.error(
                                    f"Error selecting level {level} from dimension {lev_name}: {e}")
                                if data2d[lev_name].size > 0:
                                    data2d = data2d.isel({lev_name: 0}).squeeze()
                                    break
                    else:
                        self.logger.debug(
                            f"Level {level} specified but no vertical dimension found")

        dims = list(data2d.dims)
        if len(dims) > 1:
            time_dim = None
            for dim in dims:
                if dim == tc_dim or 'time' in dim.lower():
                    time_dim = dim
                    break

            if time_dim:
                non_time_dims = [dim for dim in dims if dim != time_dim]
                # If there are non-time dimensions, average over them
                if non_time_dims:
                    data2d = data2d.mean(dim=non_time_dims)
            else:
                # Could not identify time dimension. Using first dimension
                other_dims = dims[1:]
                if other_dims:
                    data2d = data2d.mean(dim=other_dims)

        data2d = data2d.squeeze()
        data2d.attrs = data_array.attrs.copy()

        # Check for NaN values only if data is numeric
        if np.issubdtype(data2d.values.dtype, np.number):
            if np.isnan(data2d.values).any():
                self.logger.debug(
                    f"Output contains NaN values: {np.sum(np.isnan(data2d.values))} NaNs")
        else:
            self.logger.debug(f"Skipping NaN check for non-numeric data type: {data2d.values.dtype}")
            
        return apply_conversion(self.config_manager, data2d, data_array.name)

    def _extract_box_data(self, data_array, time_lev=None, exp_id=None):
        """Extract data for a box plot.
        
        This method prepares data for box plots by extracting values across a dimension
        (typically spatial) for statistical analysis.
        
        Args:
            data_array: xarray.DataArray to extract data from
            time_lev: Time level to extract (optional)
            exp_id: Experiment ID for comparison plots (optional)
            
        Returns:
            pandas.DataFrame: DataFrame with columns for categories and values
        """
        tc_dim = self.config_manager.get_model_dim_name('tc') or 'time'
        d_temp = data_array.copy()

        # Handle time dimension selection
        if tc_dim and tc_dim in d_temp.dims:
            num_tc = self._get_dimension_size(d_temp, tc_dim)
            self.logger.debug(f"Time dimension '{tc_dim}' has {num_tc} levels")
            
            if time_lev == 'all' and tc_dim in d_temp.dims:
                time_values = d_temp[tc_dim].values
                num_times = len(time_values)
                all_data = []
                valid_time_count = 0

                for t in range(num_times):
                    time_slice = d_temp.isel({tc_dim: t})
                    time_str = str(time_values[t])

                    if hasattr(time_values[t], 'strftime'):
                        # For full date and hour: '2018-05-23 06'
                        time_str = time_values[t].strftime('%Y-%m-%d %H')
                        # For just month-day-hour: '05-23 06'
                        # time_str = time_values[t].strftime('%m-%d %H')
                    else:
                        # fallback for numpy.datetime64
                        time_str = str(time_values[t])[:13]  # '2018-05-23T06'

                    # if hasattr(time_values[t], 'strftime'):
                    #     time_str = time_values[t].strftime('%Y-%m-%d %H:%M')
                    flat_data = time_slice.values.flatten()
                    # Remove NaNs
                    valid_data = flat_data[~np.isnan(flat_data)]
                    if len(valid_data) == 0:
                        continue
                    if np.min(valid_data) == np.max(valid_data):
                        continue
                    valid_time_count += 1
                    df_time = pd.DataFrame({
                        'time': time_str,
                        'time_idx': t,
                        'value': valid_data,
                        'experiment': exp_id
                    })
                    all_data.append(df_time)
                if all_data:
                    df = pd.concat(all_data, ignore_index=True)
                    self.logger.debug(f"Created DataFrame with {len(df)} rows") 
                    self.logger.debug(f"for {valid_time_count} valid time levels (out of {num_times} total)")
                    return df
                else:
                    return None
            
            elif isinstance(time_lev, int):
                actual_time_lev = time_lev if time_lev >= 0 else num_tc + time_lev
                
                if 0 <= actual_time_lev < num_tc:
                    d_temp = d_temp.isel({tc_dim: actual_time_lev})
                else:
                    d_temp = d_temp.isel({tc_dim: 0})
            else:
                # Default to last time level if not specified
                d_temp = d_temp.isel({tc_dim: -1})

        
        # Check for NaN values only if data is numeric
        if np.issubdtype(d_temp.values.dtype, np.number):
            if np.isnan(d_temp).all():
                return None
            
            if np.isnan(d_temp.values).any():
                self.logger.debug(f"Output contains NaN values: {np.sum(np.isnan(d_temp.values))} NaNs")
        else:
            self.logger.debug(f"Skipping NaN check for non-numeric data type: {d_temp.values.dtype}")
        
        field_name = data_array.name if hasattr(data_array, 'name') else 'unnamed'
        
        # Convert to pandas DataFrame
        try:
            # For spatial data, we want to create a box plot of values across the spatial domain
            # First, flatten the spatial dimensions
            if len(d_temp.dims) > 1:
                # If we have a time dimension and we're using all time steps,
                # we can create a box plot for each time step

                # When creating time-based DataFrames, add a numeric time index
                if tc_dim in d_temp.dims and (time_lev == 'all' or time_lev is None and len(d_temp[tc_dim]) > 1):
                    time_values = d_temp[tc_dim].values
                    num_times = len(time_values)
                    
                    all_data = []
                    
                    for t in range(num_times):
                        time_slice = d_temp.isel({tc_dim: t})
                        
                        # Convert time to string format for better display
                        time_str = str(time_values[t])
                        if hasattr(time_values[t], 'strftime'):
                            time_str = time_values[t].strftime('%Y-%m-%d %H:%M')
                        
                        flat_data = time_slice.values.flatten()
                        
                        if np.isnan(flat_data).all():
                            self.logger.debug(f"Skipping time {time_str} - all values are NaN")
                            continue
                        
                        df_time = pd.DataFrame({
                            'time': time_str,
                            'time_idx': t,  # Add numeric time index for sorting
                            'value': flat_data,
                            'experiment': exp_id or 'default'
                        })
                        
                        all_data.append(df_time)
                    
                    # Combine all time steps
                    if all_data:
                        df = pd.concat(all_data, ignore_index=True)
                    else:
                        self.logger.warning(f"No valid data for box plot of {field_name}")
                        return None

                else:
                    flat_data = d_temp.values.flatten()
                    
                    if tc_dim in d_temp.dims and len(d_temp[tc_dim]) == 1:
                        time_value = d_temp[tc_dim].values[0]
                        time_str = str(time_value)
                        if hasattr(time_value, 'strftime'):
                            time_str = time_value.strftime('%Y-%m-%d %H:%M')
                        category = f"Time: {time_str}"
                    else:
                        category = "All Data"
                    
                    df = pd.DataFrame({
                        'category': category,
                        'value': flat_data,
                        'experiment': exp_id or 'default'
                    })
            else:
                # For single time level or no time dimension
                flat_data = d_temp.values.flatten()

                if np.isnan(flat_data).all():
                    self.logger.warning(f"All values are NaN for {data_array.name if hasattr(data_array, 'name') else 'unnamed field'}")
                    return None
                
                df = pd.DataFrame({
                    'category': "All Data",
                    'value': flat_data,
                    'experiment': exp_id or 'default'
                })
            
            if hasattr(self.config_manager, 'spec_data') and field_name in self.config_manager.spec_data:
                if 'boxplot' in self.config_manager.spec_data[field_name]:
                    if 'fill_value' in self.config_manager.spec_data[field_name]['boxplot']:
                        fill_value = self.config_manager.spec_data[field_name]['boxplot']['fill_value']
                        df = df[df['value'] != fill_value]
            
            df = df.dropna(subset=['value'])
            
            if len(df) == 0:
                self.logger.warning(f"No valid data for box plot of {field_name}")
                return None
            
            # Sample the data if it's too large (for better performance)
            max_points = 10000  # Maximum number of points to include in the box plot
            if len(df) > max_points:
                self.logger.debug(f"Sampling {max_points} points from {len(df)} total points")
                df = df.sample(max_points, random_state=42)
            
            self.logger.debug(f"Created DataFrame with {len(df)} rows for box plot")

            return df
        
        except Exception as e:
            self.logger.error(f"Error creating box plot data: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def _extract_line_data(self, data_array, time_lev=None, level=None):
        """Extract data for a line plot.
        
        This method prepares data for line plots, typically extracting a time series
        or a spatial transect.
        
        Args:
            data_array: xarray.DataArray to extract data from
            time_lev: Time level to extract (optional)
            level: Vertical level to extract (optional)
            
        Returns:
            tuple: (data_df, x_col, y_col, field_name, plot_type, file_index)
                data_df: pandas DataFrame with x and y columns
                x_col: Name of the x-axis column
                y_col: Name of the y-axis column
                field_name: Name of the field being plotted
                plot_type: Type of plot ('line')
                file_index: Index of the file being plotted
        """        
        tc_dim = self.config_manager.get_model_dim_name('tc') or 'time'
        zc_dim = self.config_manager.get_model_dim_name('zc') or 'lev'
        xc_dim = self.config_manager.get_model_dim_name('xc') or 'lon'
        yc_dim = self.config_manager.get_model_dim_name('yc') or 'lat'
        
        field_name = data_array.name if hasattr(data_array, 'name') else 'unnamed'
        
        try:
            # Determine the type of line plot based on available dimensions
            
            # Case 1: Time series (most common)
            if tc_dim in data_array.dims:
                # If we have spatial dimensions, we need to select a point or average
                spatial_dims = [dim for dim in [xc_dim, yc_dim, zc_dim] if dim in data_array.dims]
                
                if spatial_dims:
                    # If level is specified and vertical dimension exists, select that level
                    if level is not None and zc_dim in data_array.dims:
                        data_array = data_array.sel({zc_dim: level}, method='nearest')
                    
                    # For spatial dimensions, we have options:
                    # 1. Select a specific point (if coordinates are provided in config)
                    # 2. Average over the spatial domain
                    
                    x_point = self.config_manager.ax_opts.get('x_point', None)
                    y_point = self.config_manager.ax_opts.get('y_point', None)
                    
                    if x_point is not None and y_point is not None and xc_dim in data_array.dims and yc_dim in data_array.dims:
                        data_array = data_array.sel({xc_dim: x_point, yc_dim: y_point}, method='nearest')
                        point_label = f"({x_point}, {y_point})"
                    else:
                        for dim in spatial_dims:
                            if dim in data_array.dims:
                                data_array = data_array.mean(dim=dim)
                        point_label = "Spatial Average"
                
                df = data_array.to_dataframe()
                # Reset index to make time a column
                df = df.reset_index()                
                x_col = tc_dim
                y_col = field_name
                
                # Format time column if it's datetime
                if pd.api.types.is_datetime64_any_dtype(df[x_col]):
                    df[x_col] = df[x_col].dt.strftime('%Y-%m-%d %H:%M')
                
                # Add a label column if we have point information
                if 'point_label' in locals():
                    df['label'] = point_label
            
            # Case 2: Spatial transect (e.g., along longitude)
            elif xc_dim in data_array.dims:
                # If we have a vertical dimension, select the specified level
                if level is not None and zc_dim in data_array.dims:
                    data_array = data_array.sel({zc_dim: level}, method='nearest')
                
                # If we have a latitude dimension, we need to select a specific latitude
                if yc_dim in data_array.dims:
                    # Check if a specific latitude is provided
                    y_point = self.config_manager.ax_opts.get('y_point', None)
                    
                    if y_point is not None:
                        data_array = data_array.sel({yc_dim: y_point}, method='nearest')
                        lat_label = f"Latitude: {y_point}"
                    else:
                        data_array = data_array.mean(dim=yc_dim)
                        lat_label = "Latitude Average"
                
                df = data_array.to_dataframe()
                df = df.reset_index()
    
                # Rename columns for clarity
                x_col = xc_dim
                y_col = field_name
                
                if 'lat_label' in locals():
                    df['label'] = lat_label
            
            # Case 3: Vertical profile
            elif zc_dim in data_array.dims:
                # If we have horizontal dimensions, we need to select a point or average
                if xc_dim in data_array.dims or yc_dim in data_array.dims:
                    # Check if specific coordinates are provided
                    x_point = self.config_manager.ax_opts.get('x_point', None)
                    y_point = self.config_manager.ax_opts.get('y_point', None)
                    
                    if x_point is not None and xc_dim in data_array.dims:
                        data_array = data_array.sel({xc_dim: x_point}, method='nearest')
                    elif xc_dim in data_array.dims:
                        data_array = data_array.mean(dim=xc_dim)
                    
                    if y_point is not None and yc_dim in data_array.dims:
                        data_array = data_array.sel({yc_dim: y_point}, method='nearest')
                    elif yc_dim in data_array.dims:
                        data_array = data_array.mean(dim=yc_dim)
                    
                    if x_point is not None and y_point is not None:
                        point_label = f"({x_point}, {y_point})"
                    else:
                        point_label = "Horizontal Average"
                
                df = data_array.to_dataframe()                
                df = df.reset_index()
                # Rename columns for clarity
                x_col = field_name
                y_col = zc_dim  # For vertical profiles, we typically put height/pressure on y-axis
                
                # Add a label column if we have point information
                if 'point_label' in locals():
                    df['label'] = point_label
            
            # Case 4: Simple 1D array (just plot as is)
            else:
                df = data_array.to_dataframe()
                df = df.reset_index()
                
                # If there's only one column besides the index, create an index column
                if len(df.columns) == 1:
                    df['index'] = np.arange(len(df))
                    x_col = 'index'
                    y_col = df.columns[0]
                else:
                    # Try to find suitable x and y columns
                    numeric_cols = [col for col in df.columns 
                                if np.issubdtype(df[col].dtype, np.number)]
                    
                    if len(numeric_cols) >= 2:
                        x_col = numeric_cols[0]
                        y_col = numeric_cols[1]
                    elif len(numeric_cols) == 1:
                        df['index'] = np.arange(len(df))
                        x_col = 'index'
                        y_col = numeric_cols[0]
                    else:
                        # Fallback
                        df['index'] = np.arange(len(df))
                        df['value'] = 0
                        x_col = 'index'
                        y_col = 'value'
            
            if hasattr(self.config_manager, 'spec_data') and field_name in self.config_manager.spec_data:
                if 'fill_value' in self.config_manager.spec_data[field_name].get('lineplot', {}):
                    fill_value = self.config_manager.spec_data[field_name]['lineplot']['fill_value']
                    df = df[df[y_col] != fill_value]
            
            df = df.dropna(subset=[x_col, y_col])
            
            if len(df) == 0:
                self.logger.warning(f"No valid data for line plot of {field_name}")
                return None
            
            # Sort by x column for proper line plotting
            df = df.sort_values(by=x_col)
            
            self.logger.debug(f"Created DataFrame with {len(df)} rows for line plot")
            return df, x_col, y_col, field_name, 'line', self.config_manager.findex
        
        except Exception as e:
            self.logger.error(f"Error creating line plot data: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def _extract_tx_data(self, data_array, time_lev=0, level=None):
        """ Extract a time-series map from a DataArray

        Note:
            Assume input DataArray is at most 4-dimensional (time, lev, lon, lat)
            and return a 2D Hovmoller plot field where time is plotted on one axis (default y-axis)
            and the spatial dimension (either lon or lat)) is plotted on the other axis  (default x-axis)
        """
        if data_array is None:
            return None

        data2d = data_array.squeeze()

        tc_dim = self.config_manager.get_model_dim_name('tc') or 'time'
        zc_dim = self.config_manager.get_model_dim_name('zc') or 'lev'
        xc_dim = self.config_manager.get_model_dim_name('xc') or 'lon'
        yc_dim = self.config_manager.get_model_dim_name('yc') or 'lat'

        if zc_dim in data2d.dims:
            if level is not None:
                # Try to select the specified level
                try:
                    if level in data2d[zc_dim].values:
                        lev_idx = np.where(data2d[zc_dim].values == level)[0][0]
                        data2d = data2d.isel({zc_dim: lev_idx})
                    else:
                        # Try nearest neighbor
                        lev_idx = np.abs(data2d[zc_dim].values - level).argmin()
                        self.logger.debug(
                            f"Level {level} not found exactly, using nearest level {data2d[zc_dim].values[lev_idx]}")
                        data2d = data2d.isel({zc_dim: lev_idx})
                except Exception as e:
                    self.logger.error(f"Error selecting level {level}: {e}")
                    if data2d[zc_dim].size > 0:
                        data2d = data2d.isel({zc_dim: 0})
            else:
                if data2d[zc_dim].size > 0:
                    data2d = data2d.isel({zc_dim: 0})
        elif level is not None:
            self.logger.debug(
                f"Level {level} specified but no vertical dimension found in data. Using data as is.")

        if self.config_manager.spec_data and data_array.name in self.config_manager.spec_data:
            spec = self.config_manager.spec_data[data_array.name]
            if 'txplot' in spec:
                if 'trange' in spec['txplot']:
                    start_time = spec['txplot']['trange'][0]
                    end_time = spec['txplot']['trange'][1]
                    try:
                        data2d = data2d.sel({tc_dim: slice(start_time, end_time)})
                    except Exception as e:
                        self.logger.error(f"Error applying time range selection: {e}")

                if 'yrange' in spec['txplot']:
                    lat_min = spec['txplot']['yrange'][0]
                    lat_max = spec['txplot']['yrange'][1]
                    try:
                        data2d = data2d.sel({yc_dim: slice(lat_min, lat_max)})
                        self.logger.debug(
                            f"Applied latitude range selection: {lat_min} to {lat_max}")
                    except Exception as e:
                        self.logger.error(f"Error applying latitude range selection: {e}")

                if 'xrange' in spec['txplot']:
                    lon_min = spec['txplot']['xrange'][0]
                    lon_max = spec['txplot']['xrange'][1]
                    try:
                        data2d = data2d.sel({xc_dim: slice(lon_min, lon_max)})
                        self.logger.debug(
                            f"Applied longitude range selection: {lon_min} to {lon_max}")
                    except Exception as e:
                        self.logger.error(
                            f"Error applying longitude range selection: {e}")

        data2d = data2d.squeeze()

        if len(data2d.dims) > 2:
            # For Hovmoller plots, we typically want time and longitude
            dims = list(data2d.dims)
            time_dim = None
            lon_dim = None
            for dim in dims:
                if dim == tc_dim or 'time' in dim.lower():
                    time_dim = dim
                elif dim == xc_dim or 'lon' in dim.lower():
                    lon_dim = dim

            if time_dim and lon_dim:
                for dim in dims:
                    if dim != time_dim and dim != lon_dim:
                        data2d = data2d.mean(dim=dim)
            else:
                for dim in dims[2:]:
                    data2d = data2d.mean(dim=dim)

            data2d = data2d.squeeze()

        # Compute weighted mean over latitude if latitude dimension exists
        if yc_dim in data2d.dims:
            try:
                weights = np.cos(np.deg2rad(data2d[yc_dim].values))
                # Make sure weights have the right shape for broadcasting
                # Create a weights array with the same shape as the data
                weight_array = xr.ones_like(data2d)
                weighted_data = data2d * weight_array * weights
                # Sum over latitude and normalize by the sum of weights
                data2d = weighted_data.sum(dim=yc_dim) / weights.sum()
            except Exception as e:
                self.logger.error(f"Error applying latitude weighting: {e}")
                self.logger.debug("Falling back to simple mean over latitude")
                if yc_dim in data2d.dims:
                    data2d = data2d.mean(dim=yc_dim)

        # Check for NaN values only if data is numeric
        if np.issubdtype(data2d.values.dtype, np.number):
            if np.isnan(data2d.values).any():
                self.logger.debug(
                    f"Output contains NaN values: {np.sum(np.isnan(data2d.values))} NaNs")
        else:
            self.logger.debug(f"Skipping NaN check for non-numeric data type: {data2d.values.dtype}")
            
        data2d.attrs = data_array.attrs.copy()

        return apply_conversion(self.config_manager, data2d, data_array.name)

    def _select_yrange(self, data2d, name):
        """ Select a range of vertical levels"""
        if 'zrange' in self.config_manager.spec_data[name]['yzplot']:
            if not self.config_manager.spec_data[name]['yzplot']['zrange']:
                return data2d
            lo_z = self.config_manager.spec_data[name]['yzplot']['zrange'][0]
            hi_z = self.config_manager.spec_data[name]['yzplot']['zrange'][1]
            if hi_z >= lo_z:
                self.logger.error(
                    f"Upper level value ({hi_z}) must be less than low level value ({lo_z})")
                return data2d
            lev = self.config_manager.get_model_dim_name('zc')
            min_index, max_index = 0, len(data2d.coords[lev].values) - 1
            for k, v in enumerate(data2d.coords[lev]):
                if data2d.coords[lev].values[k] == lo_z:
                    min_index = k
            for k, v in enumerate(data2d.coords[lev]):
                if data2d.coords[lev].values[k] == hi_z:
                    max_index = k
            return data2d[min_index:max_index + 1, :]
        else:
            return data2d

    def _extract_corr_data(self, data_array, time_lev=None, level=None):
        """ Extract data for a Pearson correlation plot
        
        This method prepares data for Pearson correlation analysis by extracting
        the appropriate slice of data based on level and time specifications.
        
        Args:
            data_array: The xarray DataArray to process
            level: Vertical level to extract (optional)
            time_lev: Time level to extract (optional)
            
        Returns:
            xarray.DataArray: The processed data array ready for correlation analysis
        """
        if data_array is None:
            return None

        # Determine correlation type (time or space)
        do_time_corr = self.config_manager.time_corr
        
        # For correlation analysis, we typically want to preserve the time dimension
        # if it exists, as we'll correlate across time at each grid point
        tc_dim = self.config_manager.get_model_dim_name('tc') or 'time'
        zc_dim = self.config_manager.get_model_dim_name('zc') or 'lev'
        
        d_temp = data_array.copy()
        
        has_vertical_dim = zc_dim and zc_dim in d_temp.dims
        if has_vertical_dim:
            if level is not None:
                try:
                    if level in d_temp[zc_dim].values:
                        lev_idx = np.where(d_temp[zc_dim].values == level)[0][0]
                        d_temp = d_temp.isel({zc_dim: lev_idx})
                    else:
                        lev_idx = np.abs(d_temp[zc_dim].values - level).argmin()
                        d_temp = d_temp.isel({zc_dim: lev_idx})
                except Exception as e:
                    self.logger.error(f"Error selecting level {level}: {e}")
                    if d_temp[zc_dim].size > 0:
                        d_temp = d_temp.isel({zc_dim: 0})
            else:
                # No level specified, use the first level
                if d_temp[zc_dim].size > 0:
                    d_temp = d_temp.isel({zc_dim: 0})
        
        # For time correlation, we want to keep the time dimension
        # For spatial correlation, we select a specific time point
        if tc_dim in d_temp.dims:
            if do_time_corr:
                self.logger.debug("Keeping all time points for time correlation")
                # No need to select a specific time level
            elif time_lev != 'all' and isinstance(time_lev, (int, np.integer)):
                # For spatial correlation, select a specific time point
                num_tc = self._get_dimension_size(d_temp, tc_dim)
                actual_time_lev = time_lev if time_lev >= 0 else num_tc + time_lev
                
                if 0 <= actual_time_lev < num_tc:
                    d_temp = d_temp.isel({tc_dim: actual_time_lev})
                else:
                    d_temp = d_temp.isel({tc_dim: 0})
        
        data2d = apply_conversion(self.config_manager, d_temp, data_array.name)
        
        # Check for NaN values only if data is numeric
        if np.issubdtype(data2d.values.dtype, np.number):
            if np.isnan(data2d.values).all():
                self.logger.warning(f"All values are NaN for {data_array.name if hasattr(data_array, 'name') else 'unnamed field'}")
        else:
            self.logger.debug(f"Skipping NaN check for non-numeric data type: {data2d.values.dtype}")
        
        return data2d
