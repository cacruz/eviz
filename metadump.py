#!/usr/bin/env python3
"""
MetaDump - A tool to generate metadata and YAML configuration files for autoviz from NetCDF files.

This module analyzes NetCDF files and generates the necessary configuration files for visualization
with autoviz. It can process single files or pairs of files for comparison, and generates:
- JSON metadata files describing the dataset contents
- YAML specification files for plot configurations  
- YAML application files for autoviz execution parameters

Coordinate System:
    Uses EViz's generic coordinate naming (xc, yc, zc, tc) which map to model-specific 
    coordinate names via meta_coordinates.yaml configuration.

Output Formats:
    - Specs YAML: Variable-specific plot configurations with units, names, and plot types
    - App YAML: Application-level settings including inputs, outputs, and system options
    - JSON: Complete dataset metadata with attributes and variable information
"""
import json
import sys
import uuid
import os
from typing import Optional, Dict, List, Set, Any, Union
from dataclasses import dataclass
import logging
import textwrap
import argparse
import yaml
import numpy as np
import xarray as xr

import eviz.lib.utils as u

logger = logging.getLogger(__name__)

# Constants
MIN_SPATIAL_DIMS = 2
MIN_3D_DIMS = 3
DEFAULT_LEVEL_INDEX = 0
EXP_ID_LENGTH = 10


@dataclass
class MetadumpConfig:
    """Configuration settings for metadata extraction.
    
    Attributes:
        filepath_1: Primary NetCDF file path for analysis
        filepath_2: Optional second NetCDF file for comparison mode
        app_output: Output path for application YAML (autoviz config)
        specs_output: Output path for specifications YAML (plot configs)
        json_output: Output path for JSON metadata dump
        ignore_vars: Variable name substrings to exclude from processing
        vars: Specific variables to include (overrides ignore_vars)
        source: Data source type for coordinate mapping (e.g., 'gridded', 'wrf', 'lis')
    """
    filepath_1: str
    filepath_2: Optional[str] = None
    app_output: Optional[str] = None
    specs_output: Optional[str] = None
    json_output: Optional[str] = None
    ignore_vars: Optional[List[str]] = None
    vars: Optional[List[str]] = None
    source: str = 'gridded'

class MetadataExtractor:
    """Main class for extracting metadata and generating configuration files.
    
    This class analyzes NetCDF datasets and generates EViz configuration files.
    It handles coordinate system mapping, variable analysis, and plot type detection
    based on dimensionality and data characteristics.
    
    The class supports both single-dataset analysis and two-dataset comparison mode.
    """
    
    def __init__(self, config: MetadumpConfig):
        """Initialize the metadata extractor with configuration settings.
        
        Args:
            config: Configuration object containing file paths and processing options
            
        Raises:
            FileNotFoundError: If input files don't exist
            ValueError: If datasets are incompatible for comparison
        """
        self.config = config
        self.dataset = self._open_dataset(config.filepath_1)
        self.dataset_2 = self._open_dataset(config.filepath_2) if config.filepath_2 else None
        self.meta_coords = u.read_meta_coords()
        self._setup_coordinates()
        
        if self.dataset_2:
            self._validate_datasets()

    def _open_dataset(self, filepath: Optional[str]) -> Optional[xr.Dataset]:
        """Open an xarray dataset from a file.
        
        Args:
            filepath: Path to the NetCDF file to open
            
        Returns:
            Opened xarray Dataset or None if filepath is None
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
            RuntimeError: For other dataset opening errors
        """
        if not filepath:
            return None
            
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Dataset file not found: {filepath}")
            
        try:
            dataset = xr.open_dataset(filepath, decode_cf=True)
            logger.info(f"Successfully opened dataset: {filepath}")
            return dataset
        except (OSError, ValueError) as e:
            logger.error(f"Invalid file format or corrupted file {filepath}: {e}")
            raise ValueError(f"Could not parse dataset file: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error opening dataset {filepath}: {e}")
            raise RuntimeError(f"Could not open dataset: {e}") from e

    def _setup_coordinates(self) -> None:
        """Set up coordinate references based on the dataset."""
        self.tc = self._get_model_dim_name('tc')
        self.xc = self._get_model_dim_name('xc')
        self.yc = self._get_model_dim_name('yc')
        self.zc = self._get_model_dim_name('zc')
        self.space_coords = {self.xc, self.yc}

    def _get_model_dim_name(self, dim_name: str) -> Optional[str]:
        """Get the model-specific dimension name with logging.
        
        Args:
            dim_name: Generic coordinate name (e.g., 'xc', 'yc', 'zc', 'tc')
            
        Returns:
            Model-specific dimension name or None if not found
        """
        result = get_model_dim_name(self.dataset.dims, dim_name, 
                                  self.meta_coords, self.config.source)
        if result is None:
            logger.warning(f"Could not find {dim_name} coordinate for source '{self.config.source}'. "
                          f"Available dimensions: {list(self.dataset.dims.keys())}")
        else:
            logger.debug(f"Mapped {dim_name} -> {result} for source '{self.config.source}'")
        return result
        
    def _validate_output_path(self, filepath: str) -> None:
        """Validate that output file can be written.
        
        Args:
            filepath: Path to output file
            
        Raises:
            PermissionError: If directory is not writable
            FileNotFoundError: If parent directory doesn't exist
        """
        output_dir = os.path.dirname(os.path.abspath(filepath))
        
        if not os.path.exists(output_dir):
            raise FileNotFoundError(f"Output directory does not exist: {output_dir}")
            
        if not os.access(output_dir, os.W_OK):
            raise PermissionError(f"No write permission for directory: {output_dir}")
            
        # Check if file exists and is writable
        if os.path.exists(filepath) and not os.access(filepath, os.W_OK):
            raise PermissionError(f"No write permission for existing file: {filepath}")
            
        logger.debug(f"Validated output path: {filepath}")

    def _validate_datasets(self) -> None:
        """Validate that two datasets are compatible for comparison.
        
        Allows partial variable overlap but warns about differences.
        Requires at least some common variables for meaningful comparison.
        """
        vars_ds1 = set(self.dataset.data_vars.keys())
        vars_ds2 = set(self.dataset_2.data_vars.keys())
        
        common_vars = vars_ds1.intersection(vars_ds2)
        only_ds1 = vars_ds1 - vars_ds2
        only_ds2 = vars_ds2 - vars_ds1
        
        if not common_vars:
            raise ValueError("Datasets have no common variables for comparison")
            
        logger.info(f"Found {len(common_vars)} common variables for comparison")
        
        if only_ds1:
            logger.warning(f"Variables only in first dataset: {sorted(only_ds1)}")
        if only_ds2:
            logger.warning(f"Variables only in second dataset: {sorted(only_ds2)}")
            
        # Store common variables for later use
        self._common_vars = common_vars

    def process(self) -> None:
        """Main processing method to generate all required outputs.
        
        Validates file write permissions before processing to avoid 
        wasted computation on files that can't be written.
        """
        if self.config.json_output:
            self._validate_output_path(self.config.json_output)
            self._generate_json_metadata()
            return

        specs_dict = self._generate_specs_dict()
        app_dict = self._generate_app_dict()

        # Auto-generate filenames using source name if not provided
        specs_output = self.config.specs_output
        app_output = self.config.app_output
        
        if not specs_output and not app_output:
            # Generate default filenames using source name
            specs_output = f"{self.config.source}_specs.yaml"
            app_output = f"{self.config.source}.yaml"
        elif specs_output and not app_output:
            # If only specs provided, generate app filename
            app_output = f"{self.config.source}.yaml"
        elif app_output and not specs_output:
            # If only app provided, generate specs filename  
            specs_output = f"{self.config.source}_specs.yaml"

        if specs_output:
            self._validate_output_path(specs_output)
            self._write_specs_yaml(specs_dict, specs_output)
            logger.info(f"Generated specs file: {specs_output}")
        if app_output:
            self._validate_output_path(app_output)
            self._write_app_yaml(app_dict, app_output)
            logger.info(f"Generated app file: {app_output}")

        if not (specs_output or app_output):
            filtered_vars = self.get_plottable_vars()
            logger.info(f"Plottable variables: {filtered_vars}")

    def _generate_json_metadata(self) -> None:
        """Generate and save JSON metadata for the dataset."""
        metadata = {
            "global_attributes": self._get_json_compatible_attrs(self.dataset.attrs),
            "variables": {}
        }

        for var_name, da in self.dataset.data_vars.items():
            if self._should_include_var(var_name):
                metadata["variables"][var_name] = {
                    "dimensions": list(da.dims),
                    "data_type": str(da.dtype),
                    "attributes": self._get_json_compatible_attrs(da.attrs)
                }

        with open(self.config.json_output or "ds_metadata.json", "w") as json_file:
            json.dump(metadata, json_file, indent=4)
        logger.debug(f"Saved metadata to {self.config.json_output or 'ds_metadata.json'}")

    def _get_json_compatible_attrs(self, attrs: Dict) -> Dict:
        """Convert attributes to JSON-compatible format."""
        return {k: json_compatible(v) for k, v in attrs.items()}

    def _should_include_var(self, var_name: str) -> bool:
        """Determine if a variable should be included based on configuration."""
        if self.config.vars:
            return var_name in self.config.vars
        if self.config.ignore_vars:
            return not any(substring in var_name for substring in self.config.ignore_vars)
        return True

    def get_plottable_vars(self) -> List[str]:
        """Get list of plottable variables based on configuration.
        
        For comparison mode, only returns variables common to both datasets.
        
        Returns:
            List of variable names that can be plotted
        """
        if self.config.vars:
            vars_to_check = self.config.vars
        else:
            vars_to_check = list(self.dataset.data_vars.keys())
            
        # Filter to common variables if comparing datasets
        if self.dataset_2 and hasattr(self, '_common_vars'):
            vars_to_check = [var for var in vars_to_check if var in self._common_vars]

        plottable = [var for var in vars_to_check 
                    if is_plottable(self.dataset, var, self.space_coords, 
                                  self.zc, self.tc)]
        
        if self.config.ignore_vars:
            plottable = [var for var in plottable 
                        if not any(substring in var 
                                 for substring in self.config.ignore_vars)]
        
        return plottable

    def _generate_specs_dict(self) -> Dict:
        """Generate the specifications dictionary for YAML output."""
        specs_dict = {}
        plottable_vars = self.get_plottable_vars()

        for var_name in plottable_vars:
            var = self.dataset[var_name]
            specs_dict[var_name] = self._process_variable(var_name, var)

        return specs_dict

    def _process_variable(self, var_name: str, var: xr.DataArray) -> Dict:
        """Process a single variable and return its metadata dictionary."""
        temp_dict = {}
        
        # Add metadata if available
        if 'units' in var.attrs:
            temp_dict['units'] = var.attrs['units']
        if 'long_name' in var.attrs:
            temp_dict['name'] = var.attrs['long_name']

        # Add plot configurations based on actual variable capabilities
        if self._can_plot_xt(var_name):
            temp_dict['xtplot'] = {
                "time_lev": "all",
                "grid": "yes",
            }

        if self._can_plot_xy(var_name):
            default_lev = (
                float(self.dataset.coords[self.zc][DEFAULT_LEVEL_INDEX].values) 
                if self.zc and self.zc in self.dataset.coords 
                else 0
            )
            temp_dict['xyplot'] = dict(levels={default_lev: []})
            if self.tc and self.tc in self.dataset.coords and self.dataset[self.tc].ndim > 1:
                temp_dict['xyplot']['time_lev'] = 1

        if self._can_plot_yz(var_name):
            temp_dict['yzplot'] = dict(contours=[])
            if self.tc and self.tc in self.dataset.coords and self.dataset[self.tc].ndim > 1:
                temp_dict['yzplot']['time_lev'] = 1

        return temp_dict
        
    def _can_plot_xt(self, var_name: str) -> bool:
        """Check if variable supports XT (time series) plotting.
        
        Args:
            var_name: Variable name to check
            
        Returns:
            True if variable has multiple time levels
        """
        return has_multiple_time_levels(self.dataset, var_name, self.tc)
        
    def _can_plot_xy(self, var_name: str) -> bool:
        """Check if variable supports XY (spatial) plotting.
        
        Args:
            var_name: Variable name to check
            
        Returns:
            True if variable has required spatial coordinates
        """
        return is_plottable(self.dataset, var_name, self.space_coords, self.zc, self.tc)
        
    def _can_plot_yz(self, var_name: str) -> bool:
        """Check if variable supports YZ (vertical cross-section) plotting.
        
        Args:
            var_name: Variable name to check
            
        Returns:
            True if variable has vertical coordinate and spatial coordinates
        """
        if not self.zc:
            return False
            
        var = self.dataset[var_name]
        var_dims = set(var.dims)
        
        # Must have vertical coordinate in the variable's dimensions
        if self.zc not in var_dims:
            return False
            
        # Must have at least one spatial coordinate (typically yc for YZ plots)
        if not self.space_coords.intersection(var_dims):
            return False
            
        # Skip soil layer variables as they're not suitable for YZ plotting
        if any("soil_layers" in dim for dim in var.dims):
            return False
            
        # Must have sufficient dimensions (at least spatial + vertical)
        min_dims_for_yz = 2  # At least Y + Z
        actual_dims = len(var_dims - {self.tc})  # Exclude time dimension
        
        return actual_dims >= min_dims_for_yz

    def _generate_app_dict(self) -> Dict:
        """Generate the application dictionary for YAML output."""
        app_dict = {
            "inputs": [{
                "name": self.config.filepath_1,
                "to_plot": self._get_plot_types()
            }],
            "outputs": {
                "print_to_file": "yes",
                "output_dir": "./output_plots",
                "print_format": "png",
                "print_basic_stats": True,
                "make_pdf": False
            },
            "system_opts": {
                "use_mp_pool": False,
                "archive_web_results": True
            }
        }

        if self.config.filepath_2:
            self._add_comparison_config(app_dict)

        return app_dict

    def _get_plot_types(self) -> Dict[str, str]:
        """Get plot types for each plottable variable.
        
        Only includes plot types that are actually supported by each variable's dimensions.
        
        Returns:
            Dictionary mapping variable names to comma-separated plot types
        """
        plot_types = {}
        for var_name in self.get_plottable_vars():
            types = []
            
            # Check each plot type individually
            if self._can_plot_xt(var_name):
                types.append("xt")
            if self._can_plot_xy(var_name):
                types.append("xy")
            if self._can_plot_yz(var_name):
                types.append("yz")
                
            plot_types[var_name] = ",".join(types)
            logger.debug(f"Variable {var_name} supports plot types: {plot_types[var_name]}")
        return plot_types

    def _add_comparison_config(self, app_dict: Dict) -> None:
        """Add comparison configuration for two-file cases.
        
        Uses UUID-based IDs to ensure uniqueness and avoid collisions.
        """
        exp_id_1 = uuid.uuid4().hex[:EXP_ID_LENGTH]
        exp_id_2 = uuid.uuid4().hex[:EXP_ID_LENGTH]
        
        app_dict['inputs'][0]['exp_id'] = exp_id_1
        app_dict['inputs'][0]['exp_name'] = None
        
        app_dict['inputs'].append({
            "name": self.config.filepath_2,
            "to_plot": {},
            "location": None,
            "exp_id": exp_id_2,
            "exp_name": None
        })
        
        app_dict['for_inputs'] = {
            "compare": {"ids": f"{exp_id_1}, {exp_id_2}"},
            "cmap": "coolwarm"
        }

    def _write_specs_yaml(self, specs_dict: Dict, output_file: str = None) -> None:
        """Write specifications dictionary to YAML file."""
        filename = output_file or self.config.specs_output
        with open(filename, 'w') as file:
            for key in sorted(specs_dict.keys()):
                yaml_content = yaml.dump({key: specs_dict[key]}, 
                                       default_flow_style=False)
                yaml_content = yaml_content.replace("'yes'", "yes")
                file.write(yaml_content + '\n')

    def _write_app_yaml(self, app_dict: Dict, output_file: str = None) -> None:
        """Write application dictionary to YAML file."""
        filename = output_file or self.config.app_output
        with open(filename, 'w') as file:
            if 'inputs' in app_dict and 'to_plot' in app_dict['inputs'][0]:
                app_dict['inputs'][0]['to_plot'] = \
                    {k: app_dict['inputs'][0]['to_plot'][k] 
                     for k in sorted(app_dict['inputs'][0]['to_plot'])}
            yaml_content = yaml.dump(app_dict, default_flow_style=False)
            yaml_content = yaml_content.replace("'yes'", "yes")
            file.write(yaml_content + '\n')

def json_compatible(value: Any) -> Any:
    """Convert values to JSON-compatible format."""
    if isinstance(value, (np.float32, np.float64)):
        return float(value)
    elif isinstance(value, (np.int32, np.int64, np.int16)):
        return int(value)
    elif isinstance(value, np.ndarray):
        return [json_compatible(v) for v in value]
    elif isinstance(value, list):
        return [json_compatible(v) for v in value]
    elif isinstance(value, dict):
        return {k: json_compatible(v) for k, v in value.items()}
    return value

def is_plottable(ds: xr.Dataset, var: str, 
                 space_coords: Set[str], zc: Optional[str], 
                 tc: Optional[str]) -> bool:
    """Determine if a variable is plottable based on its dimensions.
    
    A variable is considered plottable if it has spatial coordinates and 
    optionally time/vertical coordinates in supported combinations.
    
    Args:
        ds: xarray Dataset containing the variable
        var: Variable name to check
        space_coords: Set of spatial coordinate names (typically {xc, yc})
        zc: Vertical coordinate name (can be None)
        tc: Time coordinate name (can be None)
        
    Returns:
        True if variable can be plotted, False otherwise
        
    Supported dimension combinations:
        - 2D space: (lon, lat) 
        - 3D space: (lon, lat, lev)
        - 3D space-time: (lon, lat, time)
        - 4D space-time: (lon, lat, lev, time)
    """
    var_dims = set(ds[var].dims)
    
    # Filter out None coordinates
    valid_coords = {coord for coord in [zc, tc] if coord is not None}
    
    # Check for various dimension combinations
    if space_coords.issubset(var_dims) and len(var_dims) == 2:
        return True  # 2D space (lon, lat)
    if zc and space_coords.union({zc}).issubset(var_dims) and len(var_dims) == 3:
        return True  # 3D space (lon, lat, lev)
    if tc and space_coords.union({tc}).issubset(var_dims) and len(var_dims) == 3:
        return True  # 2D space-time (lon, lat, time)
    if (zc and tc and 
        space_coords.union({zc, tc}).issubset(var_dims) and len(var_dims) == 4):
        return True  # 4D space-time (lon, lat, lev, time)
    
    return False

def has_multiple_time_levels(ds: xr.Dataset, var: str, tc: Optional[str]) -> bool:
    """Check if variable has multiple time levels for time series plotting.
    
    Args:
        ds: xarray Dataset containing the variable
        var: Variable name to check  
        tc: Time coordinate name (can be None)
        
    Returns:
        True if variable has more than one time level, False otherwise
    """
    if tc and tc in ds[var].dims:
        time_dim_index = ds[var].dims.index(tc)
        return ds[var].shape[time_dim_index] > 1
    return False

def get_model_dim_name(dims: List[str], dim_name: str, 
                      meta_coords: Dict, source: str = 'gridded') -> Optional[str]:
    """Get the model-specific dimension name from generic coordinate name.
    
    Maps EViz generic coordinate names (xc, yc, zc, tc) to model-specific
    dimension names using the meta_coordinates.yaml configuration.
    
    Args:
        dims: List of dimension names from the dataset
        dim_name: Generic coordinate name ('xc', 'yc', 'zc', 'tc')
        meta_coords: Coordinate mapping configuration from meta_coordinates.yaml
        source: Data source type (e.g., 'gridded', 'wrf', 'lis')
        
    Returns:
        Model-specific dimension name if found, None otherwise
        
    Examples:
        >>> get_model_dim_name(['lon', 'lat'], 'xc', meta_coords, 'gridded')
        'lon'
        >>> get_model_dim_name(['west_east'], 'xc', meta_coords, 'wrf')
        'west_east'
    """
    if dim_name not in meta_coords:
        return None

    dim_data = meta_coords[dim_name]
    if source not in dim_data:
        return None

    source_data = dim_data[source]
    coords = source_data.get('dim', '') if isinstance(source_data, dict) else source_data

    # Handle comma-separated coordinate lists
    if isinstance(coords, str) and ',' in coords:
        coords_list = [coord.strip() for coord in coords.split(',')]
        for coord in coords_list:
            if coord in dims:
                return coord
    elif isinstance(coords, str) and coords in dims:
        return coords

    return None

def parse_command_line() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate metadata and YAML configuration files for autoviz from NetCDF files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
        Examples:
          # Generic NetCDF files (uses gridded source by default)
          python metadump.py /path/to/file.nc
          python metadump.py /path/to/file.nc --json
          python metadump.py /path/to/file.nc --app foo.yaml --specs foo_specs.yaml
          
          # WRF model output files (use --source wrf)
          python metadump.py /path/to/wrfout_d01 --source wrf
          
          # Filter variables
          python metadump.py /path/to/file.nc --ignore Var --vars var1 var2 var3
        ''')
    )
    
    parser.add_argument('filepaths', nargs='+', 
                       help='The netCDF file(s) to process. Provide one or two file paths.')
    parser.add_argument('--specs', nargs='?', const=True, default=None,
                       help='Specs file to output to. If not provided, it will be the filename with a _specs.yaml extension.')
    parser.add_argument('--app', nargs='?', const=True, default=None,
                       help='App file to output to. If not provided, it will be the filename with a .yaml extension.')
    parser.add_argument('--json', nargs='?', const='ds_metadata.json', default=None,
                       help='JSON file to output to (default is ds_metadata.json).')
    parser.add_argument('--ignore', nargs='*', default=None,
                       help='Variables to ignore when generating YAML files.')
    parser.add_argument('--vars', nargs='*', default=None,
                       help='Variables to include when generating YAML files. If not provided, all variables are included.')
    parser.add_argument('--source', nargs='?', default='gridded',
                       help='Source type: gridded (default, for generic NetCDF files), wrf (for WRF model output), lis (for LIS model output), etc.')
    
    return parser.parse_args()

def main():
    """Main entry point for the metadump tool.
    
    Sets up logging, parses command line arguments, validates inputs,
    and orchestrates the metadata extraction process.
    
    Exit codes:
        0: Success
        1: Error (invalid arguments, file errors, processing failures)
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s :: (%(funcName)s:%(lineno)d) : %(message)s"
    )
    
    try:
        args = parse_command_line()

        if len(args.filepaths) > 2:
            logger.error("Error: Only one or two file paths are allowed.")
            sys.exit(1)

        config = MetadumpConfig(
            filepath_1=args.filepaths[0],
            filepath_2=args.filepaths[1] if len(args.filepaths) == 2 else None,
            app_output=args.app,
            specs_output=args.specs,
            json_output=args.json,
            ignore_vars=args.ignore,
            vars=args.vars,
            source=args.source
        )
        
        extractor = MetadataExtractor(config)
        extractor.process()
        logger.info("Processing completed successfully")
        
    except (FileNotFoundError, PermissionError, ValueError) as e:
        logger.error(f"Input/output error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error processing metadata: {e}")
        logger.debug("Full traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
