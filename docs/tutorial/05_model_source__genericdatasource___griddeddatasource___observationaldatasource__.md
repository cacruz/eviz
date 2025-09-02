# Chapter 5: Model Source (GenericDataSource / GriddedDataSource / ObservationalDataSource)

Welcome back! In [Chapter 4: Configuration Manager (ConfigManager)](04_configuration_manager__configmanager__.md), we discovered how `ConfigManager` acts as the "master recipe book," holding all the detailed instructions for our visualizations. Before that, in [Chapter 2: Autoviz Application Core (Autoviz)](02_autoviz_application_core__autoviz__.md), we learned that `Autoviz` is the "chef" that orchestrates the entire visualization process, using these recipes.

Now, imagine our chef `Autoviz` has a recipe to bake a cake. But what if the "ingredients" are very different? One recipe might call for precisely measured, neatly packaged flour and sugar (like regularly gridded weather model data). Another might require fresh, irregularly shaped vegetables straight from the garden (like satellite observations or in-situ measurements). Our chef needs different tools and expertise for each!

## Overview

### What Problem Do Model Sources Solve?

Scientific data comes in many forms. Data from a global weather model is often structured in a very regular grid (like a perfect spreadsheet of temperatures for every latitude and longitude). Satellite measurements, however, might be irregularly sampled along a satellite's path, or come from instruments with varied spatial resolutions.

You wouldn't use the same exact process to prepare *all* these different kinds of data for plotting.
*   **Regularly Gridded Data:** Needs specific operations like averaging over certain grid cells, or slicing along specific dimensions (e.g., a constant altitude).
*   **Irregular / Observational Data:** Might need special handling for missing values, calculating geographical extents for unusual shapes (like a satellite swath), or dealing with non-standard coordinates.

**Model Sources (GenericDataSource, GriddedDataSource, ObservationalDataSource) solve this by being specialized "workers" or "data experts" within EViz.** Each type of Model Source knows the best way to handle its specific kind of scientific data. They take the raw data, apply their specialized knowledge to clean it up and prepare it according to `ConfigManager`'s instructions, and then hand it off for plotting. This ensures that whether your data is a perfectly neat grid or a complex satellite swath, EViz knows how to get it ready for a beautiful visualization.

#### Our Use Case: Preparing Gridded Weather Model Data for a Map

Let's say you have a dataset from a weather model that produces regularly gridded data (e.g., temperature on a latitude-longitude grid). You want to:
1.  **Tell EViz that you have "gridded" data.**
2.  **Have EViz automatically use the correct "expert"** to handle this data.
3.  **Ensure this expert knows how to process gridded data** (like selecting a specific time or vertical level) before it's plotted as a map.

The `GriddedDataSource` is the expert for this task. It understands how to work with regularly gridded data to make it ready for visualization.

## Core Concepts

### Key Concepts: The Specialized Data Experts

Think of Model Sources as a team of data preparation specialists:

*   **`GenericDataSource` (The Generalist):** This is the base "worker." It's like a general-purpose chef who can handle *any* type of data. It provides the fundamental tools and methods that all specialized data sources will use, but it doesn't have deep, specific knowledge about grid structures or observational quirks. It's the fallback if no other specialist is explicitly chosen.
*   **`GriddedDataSource` (The Gridded Data Expert):** This specialist focuses *only* on regularly gridded data, common in climate models, weather forecasts, and ocean simulations. It knows how to intelligently slice, average, and understand data organized by dimensions like `latitude`, `longitude`, `time`, and `level`. For our use case, this is the expert we need!
*   **`ObservationalDataSource` (The Observational Data Expert):** This expert deals with data that is often less structured. This includes data from satellites (which might cover specific "swaths" of Earth at irregular intervals) or ground-based sensors (which provide point measurements). This specialist knows how to figure out the geographical extent of such irregular data, which is crucial for plotting.
*   **Receiving Instructions:** All these Model Sources get their specific instructions (like which variable to process or what region to focus on) from the [Configuration Manager (ConfigManager)](04_configuration_manager__configmanager__.md).
*   **Preparing for Plotting, Not Plotting Itself:** It's important to remember that these Model Sources *prepare* the data. They don't draw the plots themselves! Once the data is perfectly prepared, they hand it over to the [Plot Manager (PlotManager)](08_plot_manager__plotmanager__.md) to do the actual visualization.

## Getting Started

### How Autoviz Uses Model Sources

As a user, you typically don't directly create or call `GenericDataSource`, `GriddedDataSource`, or `ObservationalDataSource`. Instead, `Autoviz` (our "chef") automatically picks the right Model Source based on the `source` type you specify.

When you run `Autoviz` (either through `sViz` or from the command line, as seen in Chapter 2) and specify your data type:

1.  **You specify the `source` type:** For our use case, you'd tell `Autoviz` that your data is `gridded` (e.g., `python autoviz.py -s gridded ...`).
2.  **`Autoviz` creates the correct Model Source:** `Autoviz` uses a "factory" (a clever way to create objects without knowing their exact type beforehand) to create an instance of the `GriddedDataSource` class.
3.  **The Model Source gets to work:** This `GriddedDataSource` object then takes over. It uses the instructions from `ConfigManager` to load the data (with help from other components like the [Data Source (DataSource)](06_data_source__datasource__.md) and [Data Processing Pipeline (DataPipeline)](07_data_processing_pipeline__datapipeline__.md)), processes it according to its specialized knowledge, and then triggers the plotting process using the `PlotManager`.

So, for our use case of plotting gridded weather model data: you tell `Autoviz` it's `gridded` data, and `Autoviz` automatically selects the `GriddedDataSource` expert to prepare your data.

## Technical Details

### Under the Hood: How Model Sources Work

Let's peek behind the scenes to see how `Autoviz` interacts with Model Sources and how they do their job.

#### 1. The Experts' Workflow (Non-Code Walkthrough)

When `Autoviz` runs, and it needs to prepare data for visualization, here's what happens:

1.  **`Autoviz` gets the source type:** From your command line (`-s gridded`) or `sViz` selection, `Autoviz` knows you have `gridded` data.
2.  **`Autoviz` asks for the right expert:** It uses a "Data Source Factory" (introduced in Chapter 2) to find the class specifically designed for `gridded` data, which is `GriddedSourceFactory`.
3.  **The `GriddedSourceFactory` creates a `GriddedDataSource` object:** This is where our specialized worker is created, and it's given the [ConfigManager (ConfigManager)](04_configuration_manager__configmanager__.md) so it knows all the "recipes" (instructions).
4.  **The `GriddedDataSource` object starts its task:** `Autoviz` then tells this `GriddedDataSource` object to begin its processing, usually by calling its special `__call__` method.
5.  **Data Processing & Plotting Delegation:** The `GriddedDataSource` doesn't do everything itself. It:
    *   Initializes a `DataExtractor` (to get the right variables and slices from the actual data files).
    *   Initializes a `PlotManager` (to handle the actual plotting once the data is ready).
    *   Calls the `PlotManager`'s `plot()` method, passing along all the necessary configurations. The `PlotManager` then works with the `DataExtractor` to get and process the data before handing it to the actual plotters.

Here's a simple sequence diagram:

```{mermaid}
sequenceDiagram
    participant Autoviz as Autoviz (Chef)
    participant DataSourceFactory as Data Source Factory
    participant GriddedDataSource as GriddedDataSource (Gridded Expert)
    participant ConfigManager as ConfigManager (Recipe Book)
    participant DataExtractor as DataExtractor (Ingredient Preparer)
    participant PlotManager as PlotManager (Plotting Assistant)

    Autoviz->>DataSourceFactory: "I need an expert for 'gridded' data!"
    DataSourceFactory-->>Autoviz: "Here's the GriddedSourceFactory."
    Autoviz->>GriddedDataSource: "Create a new GriddedDataSource object, and here's the ConfigManager."
    GriddedDataSource->>ConfigManager: Initializes itself with the master recipe book
    GriddedDataSource->>DataExtractor: Initializes DataExtractor (to get raw data)
    GriddedDataSource->>PlotManager: Initializes PlotManager (to draw plots)
    Autoviz->>GriddedDataSource: "Okay, GriddedDataSource, start preparing data and plotting!" (`__call__`)
    GriddedDataSource->>PlotManager: "Plot the data using ConfigManager instructions!" (`plot()`)
    PlotManager->>DataExtractor: "Get me the specific data for this plot from ConfigManager settings."
    DataExtractor-->>PlotManager: Returns prepared data (e.g., a 2D slice)
    PlotManager->>PlotManager: Generates and saves plot (using Plotter, Figure)
    PlotManager-->>GriddedDataSource: Plotting complete
    GriddedDataSource-->>Autoviz: Data prepared and plots generated!
```

#### 2. Diving into the Code

Let's look at the actual code for these Model Source classes.

**`GenericDataSource` - The Base Class (`eviz/lib/models/base.py`)**

This is the foundational class. All other Model Sources inherit from this. It defines what *every* data source must be able to do.

```python
# File: eviz/lib/models/base.py (simplified)
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
import xarray as xr
from eviz.lib.config.config_manager import ConfigManager
from eviz.lib.data.data_extractor import DataExtractor
from eviz.lib.autoviz.plotting.plot_manager import PlotManager

@dataclass
class GenericDataSource(ABC):
    """Abstract base class for all data source implementations."""
    config_manager: ConfigManager
    plot_manager: PlotManager = None
    data_extractor: DataExtractor = None # Initialized here to be available to subclasses

    def __post_init__(self):
        """Initialize data source components."""
        # Initialize DataExtractor and PlotManager if they haven't been passed in
        if self.data_extractor is None:
            self.data_extractor = DataExtractor(self.config_manager)
        if self.plot_manager is None:
            self.plot_manager = PlotManager(self.config_manager, self.data_extractor)

    @abstractmethod
    def process_data(self, dataset: xr.Dataset) -> dict:
        """Process raw dataset into visualization-ready format."""
        pass

    @abstractmethod
    def validate_data(self, dataset: xr.Dataset) -> bool:
        """Validate that the dataset is compatible with this data source."""
        pass
    
    def __call__(self):
        """Execute the data source by running the plot manager."""
        self.logger.debug("Executing data source visualization")
        self.plot_manager.plot() # Delegates the plotting to PlotManager
```
**Explanation:**
*   `GenericDataSource` is an `ABC` (Abstract Base Class), meaning it cannot be used directly. You *must* create a specialized class that inherits from it.
*   It takes `config_manager` as input and automatically initializes `data_extractor` and `plot_manager` in its `__post_init__` method. This sets up the essential tools for any data source.
*   `@abstractmethod` for `process_data` and `validate_data` means that any class inheriting from `GenericDataSource` *must* provide its own specific implementation for these methods. This is where the specialization happens!
*   The `__call__` method makes the object "callable" like a function. When `Autoviz` runs the Model Source, it essentially calls `model()`, which then tells the `plot_manager` to do its job.

**`GriddedDataSource` - The Gridded Data Expert (`eviz/lib/models/gridded.py`)**

This class inherits from `GenericDataSource` and adds specific logic for gridded data.

```python
# File: eviz/lib/models/gridded.py (simplified)
from dataclasses import dataclass
import logging
import xarray as xr
from eviz.lib.models.base import GenericDataSource

@dataclass
class GriddedDataSource(GenericDataSource):
    """Specialized functionality for handling gridded Earth System Model (ESM) data."""

    def __post_init__(self):
        super().__post_init__() # Call the initializer of the parent class!
        self.logger.debug("GriddedDataSource initialized")

    def process_data(self, dataset: xr.Dataset) -> dict:
        """
        Processes raw gridded dataset.
        
        Args:
            dataset: Raw xarray Dataset to process
        Returns:
            Dictionary containing processed data and metadata
        """
        self.logger.debug(f"Processing gridded dataset with variables: {list(dataset.data_vars)}")
        # In a more complex scenario, this is where gridded-specific
        # transformations, like vertical interpolation or zonal means, would happen.
        # For now, it largely passes the dataset through.
        processed_data = {
            'dataset': dataset,
            'type': 'gridded',
            'variables': list(dataset.data_vars),
            'dimensions': list(dataset.dims)
        }
        return processed_data
    
    def validate_data(self, dataset: xr.Dataset) -> bool:
        """
        Validates if the dataset is compatible with gridded data processing.
        Checks for spatial coordinates like 'lat'/'lon' or 'x'/'y'.
        """
        if not isinstance(dataset, xr.Dataset):
            self.logger.error("Input is not an xarray Dataset")
            return False
        
        # Specific check for gridded data: look for standard spatial coordinates
        coords = set(dataset.coords.keys())
        has_spatial = ('lat' in coords or 'latitude' in coords) and \
                      ('lon' in coords or 'longitude' in coords)
        
        if not has_spatial:
            self.logger.warning("Gridded dataset missing standard lat/lon coordinates.")
            # Still return True, as some gridded data might use 'x'/'y' or 'i'/'j'
            # and further processing can identify those.
        
        return True

    def __call__(self):
        """Make the GriddedDataSource callable, delegating to plot_manager."""
        self.logger.debug("GriddedDataSource: Triggering plot manager.")
        self.plot_manager.plot() # Still delegates to the PlotManager
```
**Explanation:**
*   `super().__post_init__()`: This is crucial! It calls the `__post_init__` method of the `GenericDataSource` (its parent) to ensure `data_extractor` and `plot_manager` are set up first.
*   `process_data`: This method now contains logic specific to gridded data. While simplified here, in a real scenario, this is where operations like calculating area-weighted averages or selecting a specific vertical level would occur.
*   `validate_data`: This method provides a specific check for gridded data, looking for common coordinate names like `lat` and `lon`. This helps ensure the data is indeed gridded.
*   The `__call__` method still ultimately delegates to `plot_manager.plot()`, as the Model Source's job is preparation, not drawing.

**`ObservationalDataSource` - The Observational Data Expert (`eviz/lib/models/observational.py`)**

This class also inherits from `GenericDataSource` but focuses on observational data.

```python
# File: eviz/lib/models/observational.py (simplified)
from dataclasses import dataclass
import logging
import numpy as np
import xarray as xr
from eviz.lib.models.base import GenericDataSource

@dataclass
class ObservationalDataSource(GenericDataSource):
    """Specialized functionality for handling observational data (gridded or swath)."""

    def __post_init__(self):
        super().__post_init__()
        self.logger.debug("ObservationalDataSource initialized")

    def process_data(self, dataset: xr.Dataset) -> dict:
        """
        Processes raw observational dataset. May include handling for swath data,
        irregular grids, or quality flags.
        """
        self.logger.debug(f"Processing observational dataset with variables: {list(dataset.data_vars)}")
        processed_data = {
            'dataset': dataset,
            'type': 'observational',
            'variables': list(dataset.data_vars),
            'dimensions': list(dataset.dims)
        }
        # Observational data often needs its geographical extent calculated dynamically
        if dataset.data_vars:
            self.apply_extent_to_config(dataset[list(dataset.data_vars)[0]])
        return processed_data
    
    def validate_data(self, dataset: xr.Dataset) -> bool:
        """
        Validates if the dataset is compatible with observational data processing.
        More flexible than gridded validation.
        """
        if not isinstance(dataset, xr.Dataset):
            self.logger.error("Input is not an xarray Dataset")
            return False
        
        # Observational data can be very diverse, so validation is more lenient.
        # We mainly check if there are any data variables.
        if len(dataset.data_vars) == 0:
            self.logger.error("Observational dataset has no data variables")
            return False
        
        return True

    def get_data_extent(self, data_array: xr.DataArray) -> list:
        """
        Extracts geographical extent (bounding box) from an xarray DataArray.
        Crucial for plotting irregular observational data.
        """
        default_extent = [-180, 180, -90, 90]
        if data_array is None: return default_extent
            
        try:
            # Tries to find lat/lon coordinates, even if irregular
            xc_dim = self.config_manager.get_model_dim_name('xc') or 'lon'
            yc_dim = self.config_manager.get_model_dim_name('yc') or 'lat'
            
            if xc_dim in data_array.coords and yc_dim in data_array.coords:
                lon_vals = data_array[xc_dim].values
                lat_vals = data_array[yc_dim].values
                return [np.nanmin(lon_vals), np.nanmax(lon_vals), 
                        np.nanmin(lat_vals), np.nanmax(lat_vals)]
            # ... (more complex logic for other extent-finding methods omitted) ...
        except Exception as e:
            self.logger.error(f"Error extracting extent: {e}")
        return default_extent

    def apply_extent_to_config(self, data_array: xr.DataArray):
        """Extract extent from data_array and apply it to the configuration."""
        extent = self.get_data_extent(data_array)
        self.config_manager.ax_opts['extent'] = extent # Update the ConfigManager!
        self.config_manager.ax_opts['central_lon'] = (extent[0] + extent[1]) / 2
        self.config_manager.ax_opts['central_lat'] = (extent[2] + extent[3]) / 2
```
**Explanation:**
*   `super().__post_init__()` is called first, as always.
*   `process_data`: This method for observational data might include handling specific quality flags or applying custom filters. It also calls `apply_extent_to_config`.
*   `validate_data`: This is more flexible, recognizing that observational data can have many structures.
*   `get_data_extent` and `apply_extent_to_config`: These methods are excellent examples of observational data specialization. They actively determine the geographical boundaries of the data (even if it's an irregular "swath") and then update the `ConfigManager` so that the `PlotManager` knows how to set up the map properly.

These Model Sources ensure that EViz can adapt to the specific needs of different scientific data types, leading to accurate and relevant visualizations.

## Summary

### Conclusion

In this chapter, you've learned that **Model Sources (GenericDataSource, GriddedDataSource, and ObservationalDataSource)** are the specialized "data experts" within EViz. They are crucial for handling the diverse types of scientific data, from regularly gridded model outputs to irregularly sampled observational measurements. `Autoviz` automatically selects the appropriate Model Source, which then takes instructions from the `ConfigManager` to prepare the data using its specialized knowledge, before delegating the actual plotting to the `PlotManager`.

You now understand how EViz smartly adapts its data handling based on the nature of your scientific inputs. Next, we'll dive even deeper into the data side, exploring the [Data Source (DataSource)](06_data_source__datasource__.md) – the component that the Model Sources use to actually read and access the raw data files.

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)