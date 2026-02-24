# Chapter 6: Data Source (DataSource)

Welcome back! In our last chapter, [Chapter 5: Model Source (GenericDataSource / GriddedDataSource / ObservationalDataSource)](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md), we learned about the specialized "data experts" (like `GriddedDataSource`) that prepare different kinds of scientific data for visualization. These experts know *how* to process the data, but they still need to *get* that data from somewhere – from actual files stored on your computer or a remote server.

Think of it like this: a chef (our Model Source) knows how to prepare a delicious meal. But first, they need someone to go to the pantry and actually fetch the ingredients from their various containers (boxes, bags, jars). This "someone" is the **Data Source (DataSource)**.

## Overview

### What Problem Does DataSource Solve?

Scientific data comes in many different file formats, each like a different type of container:
*   **NetCDF:** A very common, self-describing format for array-oriented scientific data (like weather model outputs).
*   **HDF5:** Another popular, versatile format for large, complex datasets.
*   **CSV:** Simple text files, often used for observational data or tables.
*   **GRIB:** A specialized format for meteorological data (like weather forecasts).

Each of these file types needs a slightly different "key" and "method" to open and read its contents. If every part of EViz had to know how to open *all* these different file types, it would become very messy and complicated.

**DataSource solves this by being the universal "file opener" and "ingredient fetcher" for EViz.** It provides a common blueprint for how to handle *any* type of data file. When a [Model Source](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md) needs data, it simply asks the `DataSource` to load it, without needing to know the specific file format. The `DataSource` then handles all the technical details of opening that specific file type and putting the data into a standardized container that EViz can easily work with.

#### Our Use Case: Loading a NetCDF Data File

Let's say you have a standard NetCDF file, `output.nc`, which contains your model's temperature and pressure. Your [GriddedDataSource](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md) needs this data. You want to:
1.  **Tell EViz the path to your `output.nc` file.**
2.  **Have EViz automatically open this NetCDF file.**
3.  **Load its contents into a standard format** that the `GriddedDataSource` can understand and work with.

The `NetCDFDataSource` is the expert for this task. It knows exactly how to open a NetCDF file and prepare its contents for EViz.

## Core Concepts

### Key Concepts: The Universal File Opener

DataSource is all about providing a consistent way to get data, no matter its origin.

*   **`DataSource` (The Blueprint):** This is the **abstract base class**, meaning it's a general idea or template. It defines a set of actions (like "load data," "validate data," "get a specific field") that *all* specific data sources must implement. It's like the general instruction: "open the container and get the ingredients."
*   **Specific Data Sources (e.g., `NetCDFDataSource`, `HDF5DataSource`, `CSVDataSource`, `GRIBDataSource`):** These are the concrete "keys" for specific "doors" (file types). Each of these classes inherits from the `DataSource` blueprint and knows *exactly* how to open and read its particular file format.
    *   `NetCDFDataSource` knows how to use `xarray` to open NetCDF files.
    *   `HDF5DataSource` knows how to open HDF5 files.
    *   `CSVDataSource` knows how to read CSV files using `pandas`.
    *   `GRIBDataSource` knows how to open GRIB files.
*   **`xarray.Dataset` (The Standard Container):** No matter what file type `DataSource` opens, it always puts the data into an `xarray.Dataset` object. Think of `xarray.Dataset` as a standardized, labeled "bowl" that holds all your ingredients (variables, dimensions, attributes) in an organized way. This is critical because once data is in this `xarray` "bowl," all other EViz components (like the [Data Processing Pipeline](07_data_processing_pipeline__datapipeline__.md) and [Plot Manager](08_plot_manager__plotmanager__.md)) can easily work with it, regardless of where it originally came from.
*   **Common Actions:** Besides `load_data`, `DataSource` defines actions like `validate_data` (check if the loaded data makes sense), `get_field` (grab a specific variable like 'temperature'), and `get_metadata` (get information about the data).

## Getting Started

### How to Use DataSource (Through Model Sources)

As a user, you usually won't directly create a `NetCDFDataSource` object and call `load_data`. Instead, the [Model Source](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md) (which `Autoviz` selected for you) takes care of this.

When a [Model Source](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md) needs to get data from a file, it internally uses a `DataExtractor` object. This `DataExtractor` then selects and uses the appropriate `DataSource` (like `NetCDFDataSource`) based on the file type.

Here's the conceptual flow for our use case (loading `output.nc` for a `GriddedDataSource`):

1.  Your `Autoviz` run starts, and it initializes a `GriddedDataSource` (the "gridded expert").
2.  The `GriddedDataSource` has an internal `DataExtractor` ready.
3.  The `DataExtractor` identifies `output.nc` as a NetCDF file.
4.  It then creates a `NetCDFDataSource` and tells it to `load_data` from `output.nc`.
5.  The `NetCDFDataSource` opens `output.nc` and converts it into an `xarray.Dataset`.
6.  This `xarray.Dataset` is then made available to the `DataExtractor`, which passes it back to the `GriddedDataSource` for further processing.

## Technical Details

### Under the Hood: DataSource's Workflow

Let's look at what happens behind the scenes when a file is loaded.

#### 1. The File Fetcher's Plan (Non-Code Walkthrough)

When a [Model Source](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md) needs data, here's a simplified view of the steps involving `DataSource`:

1.  **`Model Source` needs data:** The `GriddedDataSource` (our data expert) needs to work with a data file (e.g., `output.nc`).
2.  **`DataExtractor` identifies file type:** The `GriddedDataSource` uses its `DataExtractor` component. The `DataExtractor` inspects the file path and determines it's a NetCDF file.
3.  **`DataExtractor` chooses `DataSource`:** Based on the file type, the `DataExtractor` decides it needs to use a `NetCDFDataSource`.
4.  **`NetCDFDataSource` loads data:** The `DataExtractor` tells the `NetCDFDataSource` to `load_data` from `output.nc`.
5.  **`NetCDFDataSource` opens file and creates `xarray.Dataset`:** The `NetCDFDataSource` uses the `xarray` library (a powerful Python tool for scientific data) to open `output.nc`. It reads all the variables, dimensions, and attributes, and puts them into a single, organized `xarray.Dataset` object.
6.  **Data Ready:** This `xarray.Dataset` is then ready for the `DataExtractor` and the `GriddedDataSource` to use for further processing and plotting.

Here's a simple sequence diagram to visualize this:

```{mermaid}
sequenceDiagram
    participant ModelSource as Model Source
    participant DataExtractor as DataExtractor
    participant SpecificDataSource as NetCDFDataSource
    participant XarrayLib as Xarray Library

    ModelSource->>DataExtractor: "Get data from 'output.nc'!"
    DataExtractor->>DataExtractor: Identify file type (NetCDF)
    DataExtractor->>SpecificDataSource: "Create NetCDFDataSource and load 'output.nc'!"
    SpecificDataSource->>XarrayLib: `xr.open_dataset('output.nc')`
    XarrayLib-->>SpecificDataSource: Returns `xarray.Dataset`
    SpecificDataSource-->>DataExtractor: Returns `xarray.Dataset`
    DataExtractor-->>ModelSource: `xarray.Dataset` is ready!
```

#### 2. Diving into the Code

Let's look at the core code that makes this happen.

**The `DataSource` Base Class (`eviz/lib/data/sources/base.py`)**

This is the blueprint that all specific data sources follow.

```python
# File: eviz/lib/data/sources/base.py (simplified)
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import xarray as xr

@dataclass
class DataSource(ABC):
    """Abstract base class that defines the interface for all data sources."""
    model_name: Optional[str] = None
    config_manager: Optional[object] = None
    dataset: Optional[xr.Dataset] = field(default=None, init=False) # The standard container

    @abstractmethod
    def load_data(self, file_path: str) -> xr.Dataset:
        """
        Load data from the specified file path into an xarray dataset.
        This method MUST be implemented by all specific DataSources.
        """
        raise NotImplementedError("Subclasses must implement load_data.")

    def get_field(self, field_name: str) -> Optional[xr.DataArray]:
        """Get a specific field (variable) from the loaded dataset."""
        if self.dataset is None: return None
        try: return self.dataset[field_name]
        except KeyError: return None

    # These methods make it easy to work with the underlying xarray.Dataset directly
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access (e.g., .mean()) to the underlying dataset."""
        if self.dataset is None: raise AttributeError(...)
        if hasattr(self.dataset, name): return getattr(self.dataset, name)
        raise AttributeError(...)

    def __getitem__(self, key: str) -> Any:
        """Delegate item access (e.g., ['temperature']) to the underlying dataset."""
        if self.dataset is None: raise TypeError(...)
        return self.dataset[key]

    def close(self) -> None:
        """Close the dataset and free resources."""
        if hasattr(self.dataset, 'close'): self.dataset.close()
```
**Explanation:**
*   `@dataclass class DataSource(ABC):`: This declares `DataSource` as an "Abstract Base Class" (`ABC`). You can't directly create a `DataSource` object; you must create a more specific version (like `NetCDFDataSource`).
*   `dataset: Optional[xr.Dataset] = field(default=None, init=False)`: This is where the loaded data will be stored, always as an `xarray.Dataset`.
*   `@abstractmethod def load_data(...)`: This line is key! It says that any class inheriting from `DataSource` *must* provide its own version of the `load_data` method. This is where the magic of handling different file types happens.
*   `__getattr__` and `__getitem__`: These special methods allow you to interact with your `DataSource` object almost as if it *were* an `xarray.Dataset`. For example, instead of `my_data_source.dataset['temp']`, you can just type `my_data_source['temp']`. This makes the code cleaner.

**`NetCDFDataSource` (`eviz/lib/data/sources/netcdf.py`)**

This is the specific "key" for NetCDF files.

```python
# File: eviz/lib/data/sources/netcdf.py (simplified)
import xarray as xr
from .base import DataSource # Inherits from our base DataSource

@dataclass
class NetCDFDataSource(DataSource):
    """Data source implementation for NetCDF files."""
    def __post_init__(self):
        super().__init__(self.model_name, self.config_manager)

    def load_data(self, file_path: str) -> xr.Dataset:
        """Load data from a NetCDF file or OpenDAP URL."""
        self.logger.debug(f"Loading NetCDF data from {file_path}")
        try:
            # The core of loading NetCDF: use xarray's open_dataset
            dataset = xr.open_dataset(file_path, decode_cf=True)
            self.dataset = dataset # Store it in the standard 'dataset' attribute
            return dataset
        except Exception as exc:
            self.logger.error(f"Error loading NetCDF file: {file_path}. Exception: {exc}")
            raise

    # Other methods like _setup_dask_client, _rename_dims, etc., are omitted for simplicity
```
**Explanation:**
*   `class NetCDFDataSource(DataSource):`: This line shows it inherits all the common behaviors from `DataSource`.
*   `def load_data(...)`: This is the *specific implementation* of the abstract `load_data` method.
*   `xr.open_dataset(file_path, decode_cf=True)`: This is the critical line! It uses the `xarray` library to open the NetCDF file, read its contents, and automatically convert them into a beautiful `xarray.Dataset`. `decode_cf=True` helps `xarray` understand common scientific metadata.
*   `self.dataset = dataset`: The loaded `xarray.Dataset` is then stored in the `dataset` attribute, making it accessible through the `DataSource`'s standard interface.

**`HDF5DataSource` (`eviz/lib/data/sources/hdf5.py`)**

For HDF5 files, it's very similar, but might use a different `xarray` engine or a fallback if `xarray` struggles.

```python
# File: eviz/lib/data/sources/hdf5.py (simplified)
import xarray as xr
import h5py # Might be needed for manual fallback
from .base import DataSource

class HDF5DataSource(DataSource):
    """Data source implementation for HDF5 files."""
    # ... (init and logger omitted for brevity) ...

    def load_data(self, file_path: str) -> xr.Dataset:
        """Load data from an HDF5 file into an Xarray dataset."""
        self.logger.debug(f"Loading HDF5 data from {file_path}")
        try:
            # Try xarray with h5netcdf engine first
            dataset = xr.open_dataset(file_path, engine="h5netcdf")
            self.logger.info(f"Loaded HDF5 file using h5netcdf engine: {file_path}")
            self.dataset = dataset
            return dataset
        except Exception as e:
            self.logger.warning(f"Failed with h5netcdf: {e}. Falling back to h5py.")
            # If h5netcdf fails, a more manual conversion from h5py might be used
            # For simplicity, we just raise the error here.
            raise # In actual code, there's a _load_with_h5py method
```
**Explanation:**
*   It also calls `xr.open_dataset`, but explicitly specifies `engine="h5netcdf"`. This tells `xarray` to use a particular backend for HDF5 files.
*   The fallback to `h5py` (if `h5netcdf` fails) shows how specific data sources can implement more robust loading logic for their format.

**`CSVDataSource` (`eviz/lib/data/sources/csv.py`)**

For CSV files, the approach uses `pandas` first, then converts to `xarray`.

```python
# File: eviz/lib/data/sources/csv.py (simplified)
import pandas as pd # For reading CSVs
import xarray as xr
from .base import DataSource

class CSVDataSource(DataSource):
    """Data source implementation for CSV files."""
    # ... (init and logger omitted for brevity) ...

    def load_data(self, file_path: str) -> xr.Dataset:
        """Load data from a CSV file into an Xarray dataset."""
        self.logger.debug(f"Loading CSV data from {file_path}")
        try:
            # Use pandas to read CSV, then convert to xarray
            combined_data = pd.read_csv(file_path)
            dataset = combined_data.to_xarray() # Convert pandas DataFrame to xarray Dataset
            self.dataset = dataset
            # The _process_data method (omitted) would further clean up CSV data
            return dataset
        except Exception as exc:
            self.logger.error(f"Error loading CSV file: {file_path}. Exception: {exc}")
            raise
```
**Explanation:**
*   `pd.read_csv(file_path)`: Uses the `pandas` library to read the CSV file into a `DataFrame`.
*   `combined_data.to_xarray()`: This is the key step! It converts the `pandas.DataFrame` into an `xarray.Dataset`, again ensuring consistency for EViz.

**`GRIBDataSource` (`eviz/lib/data/sources/grib.py`)**

And finally, for GRIB files:

```python
# File: eviz/lib/data/sources/grib.py (simplified)
import xarray as xr
from .base import DataSource

class GRIBDataSource(DataSource):
    """Data source implementation for GRIB files."""
    # ... (init and logger omitted for brevity) ...

    def load_data(self, file_path: str) -> xr.Dataset:
        """Load data from a GRIB file into an Xarray dataset."""
        self.logger.debug(f"Loading GRIB data from {file_path}")
        try:
            # Use xarray with cfgrib engine, or pynio as fallback
            dataset = xr.open_dataset(file_path, engine="cfgrib")
            self.logger.info(f"Loaded GRIB file using cfgrib engine: {file_path}")
            self.dataset = dataset
            # The _process_data method (omitted) would rename GRIB-specific dims
            return dataset
        except Exception as exc: # Catches ImportError for cfgrib/pynio as well
            self.logger.error(f"Error loading GRIB file: {file_path}. Exception: {exc}")
            raise
```
**Explanation:**
*   Similar to HDF5, it uses `xr.open_dataset` but specifies `engine="cfgrib"` (or `pynio` as a fallback). This tells `xarray` to use the appropriate library for GRIB files.

## Summary

### Conclusion

In this chapter, you've learned that the **Data Source (DataSource)** is the universal "file opener" in EViz. It acts as a blueprint (`DataSource` base class) for handling any data file type, with specific implementations (`NetCDFDataSource`, `HDF5DataSource`, `CSVDataSource`, `GRIBDataSource`) knowing how to open their particular format. Crucially, all these specific Data Sources convert the raw file contents into a standardized `xarray.Dataset`, providing a consistent "bowl" of ingredients for all subsequent EViz operations. This abstraction allows [Model Source](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md) objects to fetch data without worrying about the file's original format.

Now that we know how to fetch data, the next logical step is to understand how that data is prepared, cleaned, and transformed before it's ready for plotting. That's what we'll explore in the next chapter: [Data Processing Pipeline (DataPipeline)](07_data_processing_pipeline__datapipeline__.md).

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)