# Chapter 7: Data Processing Pipeline (DataPipeline)

Welcome back, data adventurers! In our last chapter, [Chapter 6: Data Source (DataSource)](06_data_source__datasource__.md), we learned how to open various "containers" (file formats like NetCDF, CSV) and fetch our raw "ingredients" (data) into a standardized `xarray.Dataset` "bowl." That was a crucial step!

Now, imagine you've just picked up all your ingredients from the grocery store. They're raw – maybe some vegetables need washing and chopping, meat needs trimming, and some spices need to be mixed. You can't just throw them all together and expect a gourmet meal! Similarly, raw scientific data often needs cleaning, standardizing, and sometimes even combining before it's truly ready for visualization.

This is where the **Data Processing Pipeline (DataPipeline)** comes in. It's like your highly organized kitchen's **assembly line**, ensuring every ingredient is perfectly prepared for cooking (visualization).

## Overview

### What Problem Does DataPipeline Solve?

Raw scientific data, even after being loaded into an `xarray.Dataset`, might still have issues:
*   **Messy Coordinates:** Latitude might be called `y` in one file and `lat` in another. Longitude might range from `0` to `360` degrees in one dataset, and `-180` to `180` in another.
*   **Missing Values:** Gaps in data are common and need to be handled gracefully (e.g., filling them or marking them).
*   **Inconsistent Units:** Temperature could be in Kelvin in one file, Celsius in another. For meaningful comparisons, they need to be the same.
*   **Multiple Files:** Often, the data you need for one plot is spread across several files (e.g., one file for each month, or different models you want to compare).

If [Model Source](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md) objects (our specialized data experts) had to manually handle all these steps every time, it would be a chaotic, error-prone mess.

**DataPipeline solves this by providing a systematic, step-by-step assembly line for data.** It takes the raw `xarray.Dataset` from the `DataSource`, and through a series of specialized "stations" (Reader, Processor, Transformer, Integrator), cleans, prepares, and combines the data. This ensures that by the time data reaches the visualization stage, it's consistent, complete, and perfectly aligned, making your plots accurate and easy to understand.

#### Our Use Case: Preparing Multi-File, Gridded Data for a Map

Let's say you have two NetCDF files, `model_output_day1.nc` and `model_output_day2.nc`, both containing gridded temperature data. You want to:
1.  **Load both files.**
2.  **Standardize their coordinates** (e.g., ensure `lon` is always `-180` to `180`).
3.  **Handle any missing values.**
4.  **Convert temperature units** from Kelvin to Celsius.
5.  **Combine (concatenate) the data** from both files into a single dataset, ordered by time.

The `DataPipeline` orchestrates all these steps to deliver a single, clean, and combined `xarray.Dataset` ready for plotting.

## Core Concepts

### Key Concepts: The Data Assembly Line Components

The `DataPipeline` acts as the overall manager of your data assembly line. It doesn't do the work itself but orchestrates four specialized workers (components):

1.  **`DataReader` (The Fetcher):**
    *   **Job:** This is the *first* station on the assembly line. Its primary job is to find the data files you've specified (even handling wildcards like `*.nc`) and then use the appropriate [Data Source (DataSource)](06_data_source__datasource__.md) (like `NetCDFDataSource`) to actually load the raw data into an `xarray.Dataset` "bowl."
    *   **Analogy:** The person who receives the raw ingredients at the loading dock.

2.  **`DataProcessor` (The Cleaner & Standardizer):**
    *   **Job:** Once data is loaded, `DataProcessor` takes over. It's responsible for the essential cleaning and standardization steps. This includes:
        *   **Standardizing Coordinates:** Renaming dimensions (e.g., `XC` to `lon`, `YC` to `lat`) for consistency.
        *   **Normalizing Longitude:** Ensuring all longitude values are in a consistent range (e.g., -180 to 180 degrees).
        *   **Handling Missing Values:** Making sure missing data points are properly represented.
        *   **Unit Conversions:** Changing units (e.g., Kelvin to Celsius) as needed.
    *   **Analogy:** The prep cook who washes, peels, chops, and seasons the ingredients.

3.  **`DataTransformer` (The Remodeler - *Optional*):**
    *   **Job:** This stage handles more advanced or specific transformations. While not detailed in the provided code snippets (as it's often more specialized), it would be where you might convert data to a different coordinate system, apply smoothing, or perform regridding operations.
    *   **Analogy:** A specialist chef who might ferment vegetables or make a complex sauce.

4.  **`DataIntegrator` (The Blender/Combiner):**
    *   **Job:** If you have multiple datasets or want to create new variables by combining existing ones, the `DataIntegrator` is your go-to. It can:
        *   **Merge Datasets:** Combine datasets that share common dimensions but have different variables (like adding sea-surface temperature data to an existing dataset).
        *   **Concatenate Datasets:** Join datasets along a common dimension (like combining daily files into a single time series).
        *   **Integrate Variables:** Create new variables by performing operations (add, subtract, mean) on existing variables within a dataset.
    *   **Analogy:** The chef who skillfully combines different prepared ingredients into a cohesive dish, or makes a composite spice mix.

Each component passes its output (an `xarray.Dataset`) to the next, ensuring a smooth, systematic flow of data through the entire preparation process.

## Getting Started

### How to Use DataPipeline (Through Model Sources and Autoviz)

You, as a user, typically interact with the `DataPipeline` indirectly. The [Model Source](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md) (like `GriddedDataSource`) is the one that sets up and uses the `DataPipeline`.

Here's how our use case (loading, processing, and combining two gridded NetCDF files) conceptually works:

1.  **`Autoviz` (the overall chef) starts:** You run `Autoviz` and tell it you have `gridded` data and provide your configuration files (Chapter 2, 4).
2.  **`Autoviz` creates `GriddedDataSource`:** It uses the factory to create a `GriddedDataSource` object (our gridded data expert) (Chapter 5).
3.  **`GriddedDataSource` initializes `DataPipeline`:** The `GriddedDataSource` then creates an instance of the `DataPipeline` and hands it the necessary configurations.
4.  **`GriddedDataSource` tells `DataPipeline` to `process_files`:** It passes the list of your two NetCDF file paths (`model_output_day1.nc`, `model_output_day2.nc`) to the `DataPipeline`, along with instructions to `process` and then `integrate` them.
5.  **`DataPipeline` orchestrates:** The `DataPipeline` then directs its internal `DataReader`, `DataProcessor`, and `DataIntegrator` components to perform the specified tasks sequentially.
6.  **Ready for Plotting:** The `DataPipeline` returns a single, clean, and combined `xarray.Dataset` to the `GriddedDataSource`, which is now perfectly ready to be handed off to the [Plot Manager (PlotManager)](08_plot_manager__plotmanager__.md).

You don't need to write code to call each step (`reader.read_file`, `processor.process_data_source`, `integrator.integrate_data_sources`) individually. The `DataPipeline`'s `process_files` and `integrate_data_sources` methods abstract this complexity.

## Technical Details

### Under the Hood: DataPipeline's Workflow

Let's peek behind the scenes to see the `DataPipeline` in action.

#### 1. The Assembly Line's Plan (Non-Code Walkthrough)

When the `GriddedDataSource` asks the `DataPipeline` to prepare and combine files:

1.  **`GriddedDataSource` requests file processing:** It calls `data_pipeline.process_files(['file1.nc', 'file2.nc'])`.
2.  **`DataPipeline` delegates to `DataReader`:** For each file, the `DataPipeline` tells its `DataReader` to `read_file`.
3.  **`DataReader` uses `DataSource`:** The `DataReader` (Chapter 6) then identifies the file type and uses a `NetCDFDataSource` to open it, resulting in an `xarray.Dataset` for each file.
4.  **`DataPipeline` delegates to `DataProcessor`:** After reading, the `DataPipeline` sends each loaded `xarray.Dataset` to its `DataProcessor`.
5.  **`DataProcessor` cleans and standardizes:** The `DataProcessor` applies operations like standardizing coordinate names (`XC` -> `lon`), normalizing longitude range, handling missing values, and converting units (Kelvin -> Celsius).
6.  **`DataPipeline` stores processed data:** Each processed `xarray.Dataset` is stored internally by the `DataPipeline` as a `DataSource` object.
7.  **`GriddedDataSource` requests integration:** Once all files are individually processed, `GriddedDataSource` then tells `DataPipeline` to `integrate_data_sources` (e.g., concatenate them along the time dimension).
8.  **`DataPipeline` delegates to `DataIntegrator`:** The `DataPipeline` passes all the processed `DataSource` objects to its `DataIntegrator`.
9.  **`DataIntegrator` combines:** The `DataIntegrator` then uses `xarray.concat` to combine the `xarray.Dataset` objects from the different `DataSource`s into a single, unified `xarray.Dataset`.
10. **Final Dataset ready:** The `DataPipeline` now holds this single, fully prepared `xarray.Dataset`, which is then accessible to the `GriddedDataSource` for plotting.

Here's a simple sequence diagram for our use case:

```{mermaid}
sequenceDiagram
    participant GriddedDS as GriddedDataSource
    participant DataPipe as DataPipeline
    participant DataRead as DataReader
    participant NetCDFS as NetCDFDataSource
    participant DataProc as DataProcessor
    participant DataInt as DataIntegrator

    GriddedDS->>DataPipe: process_files(['file1.nc', 'file2.nc'])
    DataPipe->>DataRead: read_file('file1.nc')
    DataRead->>NetCDFS: load_data('file1.nc')
    NetCDFS-->>DataRead: Returns xarray.Dataset (file1)
    DataRead-->>DataPipe: Returns DataSource (file1)
    DataPipe->>DataProc: process_data_source(DataSource for file1)
    DataProc-->>DataPipe: Returns processed DataSource (file1)
    DataPipe->>DataRead: read_file('file2.nc')
    DataRead->>NetCDFS: load_data('file2.nc')
    NetCDFS-->>DataRead: Returns xarray.Dataset (file2)
    DataRead-->>DataPipe: Returns DataSource (file2)
    DataPipe->>DataProc: process_data_source(DataSource for file2)
    DataProc-->>DataPipe: Returns processed DataSource (file2)
    DataPipe->>DataPipe: Stores processed DataSources
    GriddedDS->>DataPipe: integrate_data_sources(all processed DataSources)
    DataPipe->>DataInt: integrate_data_sources([DataSource1, DataSource2], method='concatenate')
    DataInt-->>DataPipe: Returns integrated xarray.Dataset
    DataPipe-->>GriddedDS: Returns integrated xarray.Dataset
```

#### 2. Diving into the Code

Let's look at the core code for `DataPipeline` and its components.

**`DataPipeline` - The Orchestrator (`eviz/lib/data/pipeline/pipeline.py`)**

This is the main class that connects all the stages.

```python
# File: eviz/lib/data/pipeline/pipeline.py (simplified)
import logging
from typing import Dict, List, Optional, Any
import xarray as xr
from eviz.lib.data.sources import DataSource
from eviz.lib.data.pipeline.reader import DataReader
from eviz.lib.data.pipeline.processor import DataProcessor
from eviz.lib.data.pipeline.integrator import DataIntegrator # Transformer omitted for brevity

class DataPipeline:
    def __init__(self, config_manager=None):
        """Initializes DataPipeline with its components."""
        self.logger = logging.getLogger(__name__)
        self.reader = DataReader(config_manager)
        self.processor = DataProcessor(config_manager)
        # self.transformer = DataTransformer() # Omitted for this example
        self.integrator = DataIntegrator()
        self.data_sources = {} # To store processed data sources
        self.dataset = None # To store the final integrated dataset
        self.config_manager = config_manager

    def process_file(self, file_path: str, model_name: Optional[str] = None,
                    process: bool = True, transform: bool = False, # transform not shown below
                    metadata: Optional[Dict[str, Any]] = None) -> DataSource:
        """Process a single file through the pipeline stages."""
        self.logger.debug(f"Processing file: {file_path}")

        # 1. Read the file
        data_source = self.reader.read_file(file_path, model_name)

        if metadata and hasattr(data_source, 'metadata'):
            data_source.metadata.update(metadata)

        # 2. Process the data (clean and standardize)
        if process:
            data_source = self.processor.process_data_source(data_source)
        
        # 3. Store the processed data source
        self.data_sources[file_path] = data_source
        
        return data_source

    def integrate_data_sources(self, file_paths: Optional[List[str]] = None,
                              integration_params: Optional[Dict[str, Any]] = None) -> xr.Dataset:
        """Integrate data sources into a single dataset."""
        self.logger.debug("Integrating data sources")
        
        # Get the processed data sources to integrate
        if file_paths:
            data_sources_to_integrate = [self.data_sources[fp] for fp in file_paths if fp in self.data_sources]
        else:
            data_sources_to_integrate = list(self.data_sources.values())
        
        # 4. Integrate them using the Integrator component
        integration_params = integration_params or {}
        self.dataset = self.integrator.integrate_data_sources(data_sources_to_integrate, **integration_params)
        
        return self.dataset
```
**Explanation:**
*   `__init__`: Sets up the `DataReader`, `DataProcessor`, and `DataIntegrator` components.
*   `process_file`: This method shows the sequential flow: first `reader.read_file`, then `processor.process_data_source`. The resulting `DataSource` object (containing the `xarray.Dataset`) is then stored.
*   `integrate_data_sources`: This method gathers the `DataSource` objects that have already been processed and then calls `self.integrator.integrate_data_sources` to combine their underlying `xarray.Dataset`s.

**`DataReader` - The Fetcher (`eviz/lib/data/pipeline/reader.py`)**

This component uses the `DataSourceFactory` (from Chapter 6) to get the right `DataSource` type.

```python
# File: eviz/lib/data/pipeline/reader.py (simplified)
import glob
import os
from typing import Optional
from dataclasses import dataclass, field
import logging
from eviz.lib.data.factory import DataSourceFactory # From Chapter 6
from eviz.lib.data.sources import DataSource

@dataclass
class DataReader:
    config_manager: Optional[object] = None 
    data_sources: dict = field(default_factory=dict, init=False) # Cache for loaded sources
    factory: object = field(init=False) 

    def __post_init__(self):
        self.factory = DataSourceFactory(self.config_manager) # Initialize DataSource factory

    def read_file(self, file_path: str, model_name: Optional[str] = None, file_format: Optional[str] = None) -> DataSource:
        """Read data from a file or URL."""
        self.logger.debug(f"DataReader: Reading file: {file_path}")

        # Handles wildcards and multiple files (simplified below)
        if '*' in file_path:
            files = glob.glob(file_path)
            # Create a DataSource for the first file to determine type
            data_source = self.factory.create_data_source(files[0], model_name, file_format=file_format)
            # If multiple files are found, load them (simplified to just the first for this example)
            data_source.load_data(files[0]) # In real code, it would combine multiple files
            self.data_sources[file_path] = data_source
            return data_source

        # If it's a single file (not a pattern)
        # 1. Use the factory to create the correct DataSource (e.g., NetCDFDataSource)
        data_source = self.factory.create_data_source(file_path, model_name, file_format=file_format)
        # 2. Tell that DataSource to load the actual data
        data_source.load_data(file_path)
        self.data_sources[file_path] = data_source
        return data_source
```
**Explanation:**
*   `self.factory = DataSourceFactory(...)`: `DataReader` uses the `DataSourceFactory` (which we saw in Chapter 6) to figure out which specific `DataSource` type (like `NetCDFDataSource`) is needed for a given file.
*   `data_source = self.factory.create_data_source(...)`: This line creates the correct `DataSource` object.
*   `data_source.load_data(file_path)`: This tells the newly created `DataSource` to perform its specialized loading operation, populating its internal `xarray.Dataset`.

**`DataProcessor` - The Cleaner & Standardizer (`eviz/lib/data/pipeline/processor.py`)**

This component performs operations like coordinate standardization and unit conversion.

```python
# File: eviz/lib/data/pipeline/processor.py (simplified)
import logging
from dataclasses import dataclass
from typing import Optional
import xarray as xr
from eviz.lib.data.sources import DataSource

@dataclass
class DataProcessor:
    config_manager: Optional[object] = None

    def process_data_source(self, data_source: DataSource) -> DataSource:
        """Process a data source by cleaning and standardizing its dataset."""
        if not data_source.validate_data():
            self.logger.error("Data validation failed for data source.")
            return data_source
        
        # Apply core processing steps to the xarray.Dataset
        data_source.dataset = self._process_dataset(data_source.dataset, data_source.model_name)
        
        # (Other GEOS-specific processing for tropopause, humidity, omitted for brevity)
        return data_source

    def _process_dataset(self, dataset: xr.Dataset, model_name: str = None) -> Optional[xr.Dataset]:
        """Apply standardization and cleaning to an xarray Dataset."""
        if dataset is None: return None

        # Skip for certain models (e.g., WRF) that have non-standard coordinates
        if model_name in ['wrf', 'lis']:
            self.logger.debug(f"Skipping processing for model {model_name}")
            return dataset

        # 1. Standardize coordinate names (e.g., 'XC' to 'lon')
        dataset = self._standardize_coordinates(dataset, model_name)
        # 2. Normalize longitude range (e.g., 0-360 to -180-180)
        dataset = self._normalize_longitude(dataset)
        # 3. Handle missing values (e.g., replace NaNs with _FillValue)
        dataset = self._handle_missing_values(dataset)
        # 4. Apply unit conversions (e.g., Kelvin to Celsius)
        dataset = self._apply_unit_conversions(dataset)

        return dataset

    def _standardize_coordinates(self, dataset: xr.Dataset, model_name: str = None) -> xr.Dataset:
        """Rename dimensions to standard names (lon, lat, lev, time)."""
        # ... (complex logic for mapping original names to 'lon', 'lat', 'lev', 'time') ...
        # Simplified: Imagine it renames if 'x' is found, it becomes 'lon'
        if 'x' in dataset.dims and 'lon' not in dataset.dims:
            self.logger.debug("Renaming 'x' to 'lon'")
            dataset = dataset.rename({'x': 'lon'})
        return dataset
    
    def _normalize_longitude(self, data: xr.Dataset, target='-180_180', lon_name=None):
        """Normalize longitude values to a target range."""
        # ... (logic to convert 0-360 to -180-180 or vice versa) ...
        self.logger.debug(f"Normalizing longitude to {target}")
        if 'lon' in data.coords and data['lon'].values.min() >= 0 and data['lon'].values.max() <= 360 and target == '-180_180':
            data = data.assign_coords(lon = ((data['lon'] + 180) % 360) - 180)
            data = data.sortby('lon')
        return data

    def _handle_missing_values(self, dataset: xr.Dataset) -> xr.Dataset:
        """Replace NaN values with _FillValue attribute if present."""
        # ... (logic to identify and replace NaNs based on variable attributes) ...
        self.logger.debug("Handling missing values")
        # For example: dataset['variable'].fillna(var.attrs['_FillValue'])
        return dataset

    def _apply_unit_conversions(self, dataset: xr.Dataset) -> xr.Dataset:
        """Convert units like Kelvin to Celsius or hPa to Pa."""
        # ... (logic to check units attribute and apply conversion formulas) ...
        self.logger.debug("Applying unit conversions")
        if 'temp' in dataset.data_vars and dataset['temp'].attrs.get('units', '').lower() == 'k':
            self.logger.debug("Converting 'temp' from Kelvin to Celsius")
            dataset['temp'] = dataset['temp'] - 273.15
            dataset['temp'].attrs['units'] = 'C'
        return dataset
```
**Explanation:**
*   `process_data_source`: This method calls the main `_process_dataset` function, which orchestrates the cleaning steps.
*   `_process_dataset`: This function shows the sequence of `_standardize_coordinates`, `_normalize_longitude`, `_handle_missing_values`, and `_apply_unit_conversions`.
*   Each of the sub-methods (e.g., `_standardize_coordinates`) contains specific `xarray` operations to perform its task, making the data consistent.

**`DataIntegrator` - The Blender/Combiner (`eviz/lib/data/pipeline/integrator.py`)**

This component combines datasets.

```python
# File: eviz/lib/data/pipeline/integrator.py (simplified)
import logging
from typing import List
import xarray as xr
from dataclasses import dataclass
from eviz.lib.data.sources import DataSource

@dataclass
class DataIntegrator:
    def integrate_data_sources(self, data_sources: List[DataSource], **kwargs) -> xr.Dataset:
        """Integrate multiple data sources into a single dataset."""
        self.logger.debug(f"Integrator: Integrating {len(data_sources)} data sources")
        
        if not data_sources: return None
        
        method = kwargs.get('method', 'merge')
        
        if method == 'merge':
            return self._merge_datasets([ds.dataset for ds in data_sources], **kwargs)
        elif method == 'concatenate':
            return self._concatenate_datasets([ds.dataset for ds in data_sources], **kwargs)
        else:
            self.logger.error(f"Unknown integration method: {method}")
            return None
    
    def _merge_datasets(self, datasets: List[xr.Dataset], **kwargs) -> xr.Dataset:
        """Merge multiple datasets along shared dimensions."""
        self.logger.debug("Merging datasets")
        try:
            return xr.merge(datasets, join=kwargs.get('join', 'outer'))
        except Exception as e:
            self.logger.error(f"Error merging datasets: {e}")
            return datasets[0] # Fallback
    
    def _concatenate_datasets(self, datasets: List[xr.Dataset], **kwargs) -> xr.Dataset:
        """Concatenate multiple datasets along a specified dimension."""
        self.logger.debug("Concatenating datasets")
        dim = kwargs.get('dim', 'time')
        try:
            # Sort datasets by time if concatenating by time (important for correct order)
            sorted_datasets = sorted(datasets, key=lambda d: d[dim].values[0])
            result = xr.concat(sorted_datasets, dim=dim)
            # Remove duplicate time steps if any (common when combining files)
            _, index = result[dim].values.unique(return_index=True)
            result = result.isel({dim: index})
            return result
        except Exception as e:
            self.logger.error(f"Error concatenating datasets: {e}")
            return datasets[0] # Fallback
            
    # Methods for integrating variables (add, subtract, etc.) omitted for brevity
```
**Explanation:**
*   `integrate_data_sources`: This is the main method that chooses between `merge` and `concatenate` based on the `method` parameter.
*   `_merge_datasets`: Uses `xr.merge` to combine datasets.
*   `_concatenate_datasets`: Uses `xr.concat` to join datasets along a dimension (like `time`), and includes important steps like sorting by time and removing duplicates to ensure a clean final dataset.

Together, these components in the `DataPipeline` ensure that the data is meticulously prepared, cleaned, and combined, just like a well-oiled assembly line.

## Summary

### Conclusion

In this chapter, you've learned that the **Data Processing Pipeline (DataPipeline)** is EViz's data assembly line. It systematically moves raw data through crucial stages: **reading** it from files ([DataReader] using [DataSource](06_data_source__datasource__.md)), **processing** it ([DataProcessor] for standardization, cleaning, and unit conversions), **transforming** it (optional, [DataTransformer]), and **integrating** multiple datasets ([DataIntegrator]) into a single, unified, and perfectly prepared `xarray.Dataset`. This ensures your scientific data is always pristine and ready for visualization, no matter its initial state or complexity.

Now that our data is impeccably prepared and ready, the next step is to actually draw the pictures! In the next chapter, we'll dive into the [Plot Manager (PlotManager)](08_plot_manager__plotmanager__.md), which is responsible for orchestrating the creation of all your beautiful visualizations.

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)