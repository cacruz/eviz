import pandas as pd
import xarray as xr
import json
import os
from .base import DataSource


class CSVDataSource(DataSource):
    """Data source implementation for CSV and JSON files.

    This class handles loading and processing data from CSV and JSON files.
    JSON files are expected to be in line-delimited JSON format (newline-delimited JSON).
    """
    def __init__(self, model_name: str = None, config_manager=None):
        """Initialize a new CSVDataSource.

        Args:
            model_name: Name of the model this data source belongs to
            config_manager: Configuration manager instance
        """
        super().__init__(model_name, config_manager)

    def load_data(self, file_path: str) -> xr.Dataset:
        """Load data from a CSV/JSON file or a list of files into an Xarray dataset."""
        self.logger.debug(f"Loading data from {file_path}")

        try:
            combined_data = pd.DataFrame()

            if isinstance(file_path, list):
                # Handle multiple files
                for f in file_path:
                    self.logger.debug(f"Reading file: {f}")
                    this_data = self._read_file(f)
                    combined_data = pd.concat([combined_data, this_data], ignore_index=True)
            else:
                # Handle a single file
                self.logger.debug(f"Reading file: {file_path}")
                combined_data = self._read_file(file_path)

            # Normalize any nested dictionaries
            combined_data = self._normalize_nested_dicts(combined_data)

            dataset = combined_data.to_xarray()
            dataset = self._process_data(dataset)
            self.dataset = dataset
            self._extract_metadata(dataset)

            return dataset

        except Exception as exc:
            self.logger.error(f"Error loading file: {file_path}. Exception: {exc}")
            raise

    def _read_file(self, file_path: str) -> pd.DataFrame:
        """Read a single CSV or JSON file.

        Args:
            file_path: Path to the file

        Returns:
            DataFrame containing the file data
        """
        _, ext = os.path.splitext(file_path.lower())

        if ext == '.json':
            self.logger.debug(f"Reading JSON file: {file_path}")
            try:
                # Try reading as line-delimited JSON first
                df = pd.read_json(file_path, lines=True)
                self.logger.debug(f"Successfully read JSON file with {len(df)} records")
                return df
            except Exception as e:
                self.logger.warning(f"Failed to read as line-delimited JSON, trying standard JSON: {e}")
                # Fallback to standard JSON
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        return pd.DataFrame(data)
                    else:
                        return pd.DataFrame([data])
                except Exception as e2:
                    self.logger.error(f"Failed to read JSON file: {e2}")
                    raise
        else:
            # Default to CSV
            return pd.read_csv(file_path)

    def _normalize_nested_dicts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize nested dictionaries in DataFrame columns.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with nested dictionaries expanded into columns
        """
        if df.empty:
            return df

        # Find columns containing dict values
        dict_columns = []
        for col in df.columns:
            # Check if the first non-null value is a dict
            for val in df[col]:
                if pd.notna(val):
                    if isinstance(val, dict):
                        dict_columns.append(col)
                    break

        if not dict_columns:
            return df

        self.logger.debug(f"Normalizing nested dictionaries in columns: {dict_columns}")

        # Normalize each dict column
        for col in dict_columns:
            # Extract the dict column and normalize it
            try:
                normalized = df[col].apply(pd.Series)
                # Prefix the new column names with the original column name
                normalized.columns = [f"{col}_{subcol}" if subcol else col
                                     for subcol in normalized.columns]
                # Drop the original dict column and concat the normalized columns
                df = pd.concat([df.drop(columns=[col]), normalized], axis=1)
                self.logger.debug(f"Expanded {col} into {len(normalized.columns)} columns")
            except Exception as e:
                self.logger.warning(f"Failed to normalize column {col}: {e}")

        return df

    def _process_data(self, dataset: xr.Dataset) -> xr.Dataset:
        """Process the loaded CSV data.
        
        Args:
            dataset: The dataset to process
            
        Returns:
            The processed dataset
        """
        self.logger.debug("Processing CSV data")
        
        for var_name in dataset.variables:
            # Skip coordinate variables
            if var_name in dataset.dims:
                continue
                
            var = dataset[var_name]
            # Is this a date/time column?
            if var_name.lower() in ['date', 'time', 'datetime', 'timestamp']:
                try:
                    # Convert to datetime and set as a coordinate
                    dates = pd.to_datetime(var.values)
                    dataset = dataset.assign_coords(time=dates)
                    self.logger.debug(f"Converted {var_name} to datetime coordinate")
                except Exception as e:
                    self.logger.warning(f"Failed to convert {var_name} to datetime: {e}")
        
        # Check for lat/lon columns and set as coordinates
        lat_names = ['lat', 'latitude', 'y']
        lon_names = ['lon', 'longitude', 'x']
        
        for var_name in dataset.variables:
            if var_name.lower() in lat_names:
                dataset = dataset.assign_coords(lat=dataset[var_name])
                self.logger.debug(f"Set {var_name} as latitude coordinate")
            elif var_name.lower() in lon_names:
                dataset = dataset.assign_coords(lon=dataset[var_name])
                self.logger.debug(f"Set {var_name} as longitude coordinate")
        
        return dataset
    
    def _extract_metadata(self, dataset: xr.Dataset) -> None:
        """Extract metadata from the dataset.
        
        Args:
            dataset: The dataset to extract metadata from
        """
        if dataset is None:
            return
        
        self.metadata["global_attrs"] = dict(dataset.attrs)
        self.metadata["dimensions"] = {dim: dataset.dims[dim] for dim in dataset.dims}
        self.metadata["variables"] = {}
        for var_name, var in dataset.data_vars.items():
            self.metadata["variables"][var_name] = {
                "dims": var.dims,
                "attrs": dict(var.attrs),
                "dtype": str(var.dtype),
                "shape": var.shape
            }
            
            # Add some basic statistics
            try:
                self.metadata["variables"][var_name]["stats"] = {
                    "min": float(var.min().values),
                    "max": float(var.max().values),
                    "mean": float(var.mean().values),
                    "std": float(var.std().values)
                }
            except Exception:
                # Skip statistics if they can't be computed
                pass
