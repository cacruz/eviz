# Chapter 8: Plot Manager (PlotManager)

Welcome back, future visualization expert! In our previous chapter, [Chapter 7: Data Processing Pipeline (DataPipeline)](07_data_processing_pipeline__datapipeline__.md), we learned how EViz meticulously prepares raw scientific data, cleaning, standardizing, and combining it into a pristine `xarray.Dataset`. By now, our data is sparkling clean, perfectly organized, and ready to be seen!

But what happens next? How do we actually turn that perfectly prepared data into a beautiful, insightful map or graph? This is where the **Plot Manager (PlotManager)** steps in.

## Overview

### What Problem Does PlotManager Solve?

Imagine you're the head chef (our [Model Source](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md)) in a busy kitchen. You've received all your perfectly prepped ingredients (the `xarray.Dataset` from the [Data Processing Pipeline](07_data_processing_pipeline__datapipeline__.md)). Now it's time to plate the dish for your guests (the users).

But there are many ways to plate a dish:
*   Should it be a fancy, artistic arrangement (a Matplotlib map)?
*   A clean, interactive display (an HvPlot time series)?
*   A minimalist, informative chart (an Altair box plot)?
*   You also need to know *exactly* what kind of dish to make (an XY map, a time series, a profile plot).
*   And once it's made, you need to decide if it's served immediately (displayed) or packaged for later (saved as a file).

If the head chef had to know all the intricate details of every plating style, every dish type, and every serving method, they'd be overwhelmed!

**PlotManager solves this by acting like the "director" or "art curator" of all visualization efforts.** It receives the perfectly prepared data and all the plotting instructions (from the [Configuration Manager](04_configuration_manager__configmanager__.md)). Then, it intelligently decides:
1.  **Which specific plotting "artist" (tool)** to use (like Matplotlib, HvPlot, or Altair).
2.  **Which "style of art" (plot type)** to create (like an XY map, a time series, or a box plot).
It then orchestrates the entire plot creation process and handles saving or displaying the final image according to your preferences. It makes sure your beautiful data gets the perfect visual presentation.

#### Our Use Case: Creating and Saving an XY Map of Temperature

Let's say you have a beautifully prepared 2D slice of temperature data (e.g., from `model_output_day1.nc`, after being processed by the [Data Processing Pipeline](07_data_processing_pipeline__datapipeline__.md)). You want to:
1.  **Generate an XY map** (a geographical map) of this temperature data.
2.  **Save this map as a PNG image** file.
3.  **Ensure it uses the correct backend** (e.g., Matplotlib) and styling as defined in your configurations.

The `PlotManager` is the central component that will make this happen, directing the entire visualization process.

## Core Concepts

### Key Concepts: Your Visualization's Director

The PlotManager is the central figure in turning processed data into visible plots.

*   **The "Director":** This is the core role of `PlotManager`. It doesn't actually *draw* anything itself, just like a movie director doesn't act in the movie. Instead, it makes all the high-level decisions and tells the specialized actors (the "Plotters") exactly what to do.
*   **Receiving Instructions:** It gets its detailed "script" (what to plot, how it should look, where to save it) from the [Configuration Manager (ConfigManager)](04_configuration_manager__configmanager__.md). This includes information about variables, plot types, titles, color maps, and output settings.
*   **Delegating Data Retrieval:** When it needs a specific piece of data for a plot, it asks the [Data Extractor](07_data_processing_pipeline__datapipeline__.md) to fetch the right slice or variable from the prepared `xarray.Dataset`.
*   **Choosing the Right Plotting Tool (Backend):** EViz can use different Python libraries for plotting (Matplotlib, HvPlot, etc.). The `PlotManager` decides which one to use based on your configuration or the type of plot requested. It then uses a "Plotter Factory" to get an instance of the specific "Plotter" (e.g., a `MatplotlibPlotter`).
*   **Choosing the Right Plot Type:** Is it a 2D map (`xy` plot)? A time series (`xt` plot)? A vertical profile (`yz` plot)? The `PlotManager` interprets the configuration to choose the correct visualization style.
*   **Orchestrating Creation & Output:** Once it has the data, the Plotter, and the plot type, the `PlotManager` tells the chosen Plotter to create the actual [Figure](10_figure__eviz_figure__.md) and draw the plot. Finally, it handles saving the generated image or GIF to the specified output directory.

## Getting Started

### How Model Source Uses PlotManager

As a user, you typically don't directly call `PlotManager` methods. Instead, the [Model Source](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md) (like `GriddedDataSource`), which `Autoviz` selected for you, handles this.

The `GenericDataSource` (the base class for all Model Sources) is responsible for setting up and then initiating the `PlotManager`.

1.  **`PlotManager` Initialization:** When `Autoviz` creates a `GriddedDataSource`, the `GriddedDataSource` itself creates an instance of `PlotManager`, passing it the `ConfigManager` (for instructions) and `DataExtractor` (for data).

    ```python
    # From: eviz/lib/models/base.py (simplified)
    # ...
    from eviz.lib.autoviz.plotting.plot_manager import PlotManager
    # ...
    @dataclass
    class GenericDataSource(ABC):
        config_manager: ConfigManager
        plot_manager: Optional[PlotManager] = None
        data_extractor: Optional[DataExtractor] = None

        def __post_init__(self):
            # ...
            if self.data_extractor is None:
                self.data_extractor = DataExtractor(self.config_manager)
            
            if self.plot_manager is None:
                # PlotManager is created here, given the config and data_extractor
                self.plot_manager = PlotManager(self.config_manager, self.data_extractor)
    ```
    **Explanation:**
    *   In the `__post_init__` method (which runs when a `GenericDataSource` object is created), the `PlotManager` is initialized. This means our "director" is ready to receive instructions.
    *   It's given `self.config_manager` (the "script" for what to do) and `self.data_extractor` (the "assistant" to fetch specific data).

2.  **Triggering Plot Generation:** Once the data is prepared, the `GriddedDataSource` triggers the `PlotManager` to begin creating all the configured plots. This happens when `Autoviz` calls the `GriddedDataSource` object itself (using its `__call__` method).

    ```python
    # From: eviz/lib/models/base.py (simplified)
    # ...
    @dataclass
    class GenericDataSource(ABC):
        # ... (attributes and __post_init__ as above) ...

        def __call__(self):
            """Execute the data source by running the plot manager."""
            self.logger.debug("Executing data source visualization")
            # The PlotManager's 'plot' method is called to start the show!
            self.plot_manager.plot()
    ```
    **Explanation:**
    *   When the `GenericDataSource` is "called" (e.g., by `autoviz.run()` which calls `model()`), it simply delegates the main plotting task to `self.plot_manager.plot()`. This method will then iterate through all the plot instructions in the `ConfigManager` and create each plot.

3.  **Creating a Specific Plot (Internal Helper):** Sometimes, a Model Source might want to create just one specific plot rather than iterating through all configurations. It can use `create_plots` which in turn calls a specific method of `PlotManager`.

    ```python
    # From: eviz/lib/models/base.py (simplified)
    # ...
    @dataclass
    class GenericDataSource(ABC):
        # ... (attributes and methods) ...

        def create_plots(self, dataset: xr.Dataset, field_name: str, plot_type: str) -> None:
            """Create plots for the specified field and plot type."""
            if field_name not in dataset.data_vars:
                raise ValueError(f"Field '{field_name}' not found in dataset")
            
            data_array = dataset[field_name]
            # This is how a specific plot can be requested from the PlotManager
            self.plot_manager.process_plot(data_array, field_name, 0, plot_type)
    ```
    **Explanation:**
    *   The `create_plots` helper method gets a specific `field_name` (like 'temp') and `plot_type` ('xy').
    *   It then calls `self.plot_manager.process_plot()`, directly telling the `PlotManager` to make one specific plot with the provided `data_array`. The `0` is likely an index for plot parameters, but we can simplify its role for this tutorial.

For our use case, when `plot_manager.plot()` is called, it will look at the `ConfigManager`, find the instruction to plot 'temperature' as an 'xy' map, and then orchestrate that specific plot.

## Technical Details

### Under the Hood: PlotManager's Workflow

Let's peek behind the scenes to see how our "Director" `PlotManager` orchestrates the creation of a plot.

#### 1. The Director's Plan (Non-Code Walkthrough)

When `PlotManager.plot()` is called (by the [Model Source](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md)), here's a simplified step-by-step of what happens for each plot instruction found in the configuration:

1.  **Get Plot Instructions:** `PlotManager` consults the [Configuration Manager](04_configuration_manager__configmanager__.md) to get the detailed "recipe" for the next plot. This includes the variable name (e.g., 'temp'), the desired plot type (e.g., 'xy'), and all the styling/output options.
2.  **Fetch Data:** `PlotManager` asks the `DataExtractor` (its "assistant") to retrieve the specific data for this plot. This usually involves getting the correct `xarray.DataArray` slice (e.g., the 2D temperature map for a specific time and level) from the processed `xarray.Dataset`.
3.  **Identify Plotting Backend:** Based on the configuration (or sometimes the plot type), `PlotManager` determines which underlying plotting library to use (e.g., Matplotlib).
4.  **Get the Right Plotter:** `PlotManager` uses a `PlotterFactory` (a clever tool for creating objects) to create an instance of the correct "Plotter" object (e.g., `MatplotlibPlotter`). This Plotter is our "artist" who knows how to draw with a specific tool.
5.  **Create the Plot:** `PlotManager` then tells this `MatplotlibPlotter` to `create_plot()`, passing it the prepared data, the plot type, and all the specific styling instructions.
6.  **Handle Output:** Once the plot is created, `PlotManager` checks the configuration to see if the plot should be saved to a file (and in what format, like PNG, GIF) or displayed on the screen. It then handles the saving process.
7.  **Loop:** `PlotManager` repeats this process for every plot instruction found in the configuration.

Here's a simple sequence diagram for our use case (plotting temperature as an XY map):

```{mermaid}
sequenceDiagram
    participant ModelSource as Model Source
    participant PlotManager as PlotManager (Director)
    participant ConfigManager as ConfigManager (Recipe Book)
    participant DataExtractor as DataExtractor (Assistant)
    participant PlotterFactory as Plotter Factory
    participant MatplotlibPlotter as MatplotlibPlotter (Artist)

    ModelSource->>PlotManager: plot() (Start visualization)
    PlotManager->>ConfigManager: Get next plot instruction (e.g., 'temp', 'xy', save as PNG)
    ConfigManager-->>PlotManager: Returns instructions
    PlotManager->>DataExtractor: Get data for 'temp' (2D slice)
    DataExtractor-->>PlotManager: Returns xarray.DataArray (prepared data)
    PlotManager->>PlotterFactory: "Give me a MatplotlibPlotter for 'xy' plot."
    PlotterFactory-->>PlotManager: Returns MatplotlibPlotter
    PlotManager->>MatplotlibPlotter: create_plot(data, 'temp', 'xy', all_styling_options)
    MatplotlibPlotter-->>PlotManager: Plot generated (internal Figure object)
    PlotManager->>MatplotlibPlotter: Save plot to file (PNG)
    MatplotlibPlotter-->>PlotManager: File saved
    PlotManager-->>ModelSource: Plotting cycle complete
```

#### 2. Diving into the Code

Let's look at the (simplified) core code for `PlotManager`.

**`PlotManager` - The Director (`eviz/lib/autoviz/plotting/plot_manager.py`)**

This class orchestrates everything. We'll simplify its methods significantly to focus on the core responsibilities.

```python
# File: eviz/lib/autoviz/plotting/plot_manager.py (simplified)
import logging
from typing import Dict, Any, Optional
import xarray as xr

# We'll need these components
from eviz.lib.config.config_manager import ConfigManager
from eviz.lib.data.data_extractor import DataExtractor
from eviz.lib.autoviz.plotting.factory import PlotterFactory # The factory to get Plotters
from eviz.lib.autoviz.figure import Figure # To create the plot canvas

class PlotManager:
    """
    Manages the creation and output of all plots.
    Acts as the director, coordinating data, plotters, and configurations.
    """
    def __init__(self, config_manager: ConfigManager, data_extractor: DataExtractor):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_manager = config_manager
        self.data_extractor = data_extractor
        # The PlotterFactory will help us get the right plotting 'artist'
        self.plotter_factory = PlotterFactory(config_manager) 
        self.output_files = [] # To keep track of generated files

    def plot(self):
        """
        Main entry point for PlotManager. Iterates through all configured plots
        and orchestrates their creation.
        """
        self.logger.info("PlotManager: Starting plot generation.")

        # Loop through each plot instruction in the configuration
        # map_params comes from ConfigManager, contains details for each plot
        for plot_idx, plot_config in self.config_manager.map_params.items():
            field_name = plot_config.get('field')
            plot_type = plot_config.get('to_plot', 'xy') # Default to XY map
            # We assume for simplicity that `compare` implies multiple datasets
            # and that `data_extractor` can handle retrieving the correct one.

            self.logger.debug(f"PlotManager: Processing plot for '{field_name}' ({plot_type})")
            
            # 1. Fetch the prepared data using the DataExtractor
            # This is a simplification; in reality, data_extractor takes more params
            data_array = self.data_extractor.get_field(field_name, plot_idx) 

            if data_array is None:
                self.logger.warning(f"No data found for field '{field_name}'. Skipping plot.")
                continue

            # 2. Process this single plot
            self.process_plot(data_array, field_name, plot_idx, plot_type)
            
        self.logger.info("PlotManager: Plot generation complete.")

    def process_plot(self, data_array: xr.DataArray, field_name: str, 
                     plot_idx: int, plot_type: str):
        """
        Processes a single plot request by selecting the right plotter
        and creating the visualization.
        """
        self.logger.debug(f"PlotManager: Creating plot for {field_name}, type: {plot_type}")

        # 1. Get the specific plotter 'artist' (e.g., MatplotlibPlotter)
        # The plotter_factory will determine the correct backend based on config
        plotter = self.plotter_factory.get_plotter(plot_type) 

        # 2. Create a new Figure object (our canvas for this plot)
        figure = Figure(plot_idx=plot_idx, config_manager=self.config_manager)

        # 3. Tell the plotter 'artist' to draw the plot on our figure
        plotter.create_plot(data_array, field_name, figure, plot_type)

        # 4. Handle saving or displaying the plot
        output_opts = self.config_manager.output_config.get_outputs_for_plot(plot_idx)
        if output_opts.get('print_to_file', False):
            # This part is simplified; plotter itself usually handles saving
            output_filepath = figure.save_plot(field_name, plot_idx) 
            if output_filepath:
                self.output_files.append(output_filepath)
                self.logger.info(f"Plot saved to: {output_filepath}")
        else:
            self.logger.info(f"Plot for {field_name} created (not saved as per config).")

    # Other methods for handling comparisons, animations, etc., are omitted for brevity
```
**Explanation:**
*   `__init__`: Initializes `PlotManager` with the `config_manager` (for instructions), `data_extractor` (for data fetching), and a `PlotterFactory` (to get the right plotting tool).
*   `plot()`: This is the main loop. It iterates through each plot instruction (e.g., `map_params`) stored in the `config_manager`.
    *   For each instruction, it first asks `self.data_extractor` to `get_field` to retrieve the relevant `data_array` (like our 2D temperature slice).
    *   Then, it calls `self.process_plot()` to handle the actual creation of that single plot.
*   `process_plot()`: This method is where the single plot is created:
    *   `plotter = self.plotter_factory.get_plotter(plot_type)`: This line is critical! It asks the `PlotterFactory` (which we'll cover in the next chapter) to give us the appropriate "Plotter" object (e.g., a `MatplotlibPlotter`) based on the `plot_type` and other configuration settings.
    *   `figure = Figure(...)`: It creates a `Figure` object, which is like the blank canvas for our plot.
    *   `plotter.create_plot(...)`: It then tells the chosen `plotter` (our "artist") to `create_plot()` on that `figure` using the `data_array` and other details.
    *   `figure.save_plot(...)`: Finally, it checks the output options from `config_manager` and, if saving is enabled, tells the `figure` to save itself to a file.

By orchestrating these steps, the `PlotManager` ensures that your processed data is correctly transformed into the desired visualization and delivered as specified.

## Summary

### Conclusion

In this chapter, you've learned that the **Plot Manager (PlotManager)** is the "director" of EViz's visualization efforts. It takes beautifully prepared data and detailed instructions from the [Configuration Manager](04_configuration_manager__configmanager__.md), then intelligently delegates the actual drawing to specialized "Plotter" objects (via a `PlotterFactory`). It orchestrates the entire process of creating an individual plot and handling its output (saving to file or displaying). The `PlotManager` is the brain that ensures your scientific data gets the perfect visual presentation.

Now that we understand how the `PlotManager` directs the show, the next logical step is to meet the actual "artists" who do the drawing! In the next chapter, we'll dive into the [Plotter (BasePlotter and backends)](09_plotter__baseplotter_and_backends__.md) – the components that use specific libraries like Matplotlib to create the stunning visualizations.

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)