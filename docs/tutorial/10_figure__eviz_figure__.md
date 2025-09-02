# Chapter 10: Figure (eViz Figure)

Welcome back, future visualization expert! In our last chapter, [Chapter 9: Plotter (BasePlotter and backends)](09_plotter__baseplotter_and_backends__.md), we met the "artists" of EViz – the `Plotters`. We learned how they use powerful libraries like Matplotlib to draw specific types of plots, like an XY map of temperature.

Now, imagine an artist has all their tools and knows *how* to paint. But where do they put their masterpiece? They need a **canvas**! In EViz, that canvas is the **Figure**, specifically the `eViz Figure`.

## Overview

### What Problem Does eViz Figure Solve?

Think of a traditional Matplotlib `Figure` as a basic blank canvas. It's functional, but for complex scientific visualizations, you often need a "smarter" canvas that helps with many tasks automatically:
*   **Organizing Multiple Plots:** If you want to show two temperature maps and a wind map side-by-side or stacked, the canvas needs to divide itself into neat sections (subplots). Manually calculating sizes and positions for these can be tedious.
*   **Geographical Awareness:** If your plot is a map of Earth, the canvas needs to know how to handle geographical coordinates, draw coastlines, and apply map projections (like showing the Earth as a flat rectangle or a curved sphere).
*   **Automatic Sizing:** You wouldn't want to manually guess the perfect width and height for every set of plots. A smart canvas should try to figure this out for you, ensuring everything fits nicely.
*   **Shared Elements:** Sometimes, you want one main title for a whole set of plots, or a single colorbar that applies to multiple related maps. The canvas should help manage these shared elements.

Matplotlib's default `Figure` provides the foundation, but `eViz Figure` enhances it with these smart, automated features specifically designed for Earth System Model data visualization.

#### Our Use Case: Creating a Multi-Panel Map with Geographic Projection

Let's say you want to visualize two temperature maps from different models side-by-side, or a temperature map and a temperature difference map. For this, you need a canvas that can:
1.  **Automatically create two (or more) subplots** to display each map.
2.  **Set up proper geographical map projections** (like Plate Carree) and add features like coastlines to each map.
3.  **Adjust its overall size** to optimally fit these plots.

The `eViz Figure` is the smart canvas that handles all these layout and geographical setup tasks, making it easy for the `Plotter` to just "paint" the data onto the prepared sub-canvases.

## Core Concepts

### Key Concepts: Your Smart Canvas Explained

The `eViz Figure` is an enhanced version of the standard `matplotlib.figure.Figure`. Here are its key features:

*   **The Enhanced Canvas:** It's fundamentally a Matplotlib `Figure`, meaning it's the top-level container for all the elements of your plot (like titles, axes, and actual data visualizations). The "eViz" part means it comes with extra built-in intelligence.
*   **Layout Management (`_subplots`, `GridSpec`):** Instead of you manually telling it where each plot goes, the `eViz Figure` can automatically determine how many rows and columns of subplots are needed based on your [Configuration Manager](04_configuration_manager__configmanager__.md) settings (especially for comparison plots). It uses Matplotlib's `GridSpec` to arrange these subplots efficiently.
*   **Map Projections (Cartopy):** This is a big one for Earth System data! If your plot type indicates a geographical map (like an XY plot), the `eViz Figure` automatically integrates `Cartopy`. It can set up various map projections (e.g., `PlateCarree`, `LambertConformal`) and add important geographical features like `coastlines()`, `borders()`, and `land` features to each map subplot.
*   **Automatic Sizing (`_calculate_optimal_figsize`):** It intelligently calculates the best width and height for the entire figure. It considers how many subplots there are, what type of plots they are (maps often need more space), and adds appropriate margins for titles and colorbars.
*   **`axes_array`:** This is a list that stores all the individual "sub-canvases" (Matplotlib `Axes` objects) that have been created on the `Figure`. The `Plotter` then draws directly onto these `Axes` objects.
*   **`_ax_opts`:** An internal dictionary where the `Figure` stores various options for its axes, like the geographical `extent` (bounding box) or the `projection` to use. These options are often read from the [Configuration Manager](04_configuration_manager__configmanager__.md).

## Getting Started

### How to Use eViz Figure (Through PlotManager)

You, as a user, generally don't create an `eViz Figure` object directly. Instead, the [Plot Manager (PlotManager)](08_plot_manager__plotmanager__.md) handles this for you.

When the [Plot Manager](08_plot_manager__plotmanager__.md) is tasked with creating a plot (or a set of plots), here's how it uses the `eViz Figure`:

1.  **`PlotManager` asks for a new canvas:** The `Plot Manager` calls a special "factory" method on the `Figure` class: `Figure.create_eviz_figure()`. It passes along the [Configuration Manager](04_configuration_manager__configmanager__.md) (which holds all the instructions), the `plot_type` (e.g., 'xy' for a map), and the `field_name` (e.g., 'temperature').
2.  **`eViz Figure` is initialized and sized:** Behind the scenes, `Figure.create_eviz_figure()` takes these inputs, determines the ideal layout (how many subplots) and size for the canvas, and creates a new `eViz Figure` object.
3.  **`eViz Figure` prepares its sub-canvases:** The `Plot Manager` then tells this new `eViz Figure` to set up its internal `Axes` objects (the individual sub-canvases), possibly with geographical projections and features if it's a map. This is done by calling `figure.set_axes()`.
4.  **`Plotter` draws on the prepared canvas:** Once the `eViz Figure` has its `axes_array` ready, the `Plot Manager` hands the `Figure` to the appropriate [Plotter](09_plotter__baseplotter_and_backends__.md). The `Plotter` then retrieves the `Axes` objects from the `Figure` and uses its specific plotting library (like Matplotlib) to draw the data.
5.  **`eViz Figure` handles saving:** After the `Plotter` has drawn everything, the `Plot Manager` tells the `eViz Figure` to `save_plot()` to a file, using the output settings from the [Configuration Manager](04_configuration_manager__configmanager__.md).

This streamlined process means that when you configure EViz to make a map, the `eViz Figure` automatically provides a perfectly set-up geographical canvas for the `Plotter` to work on.

## Technical Details

### Under the Hood: eViz Figure's Workflow

Let's peek behind the scenes to see how our "smart canvas" is created and prepared for our use case (a multi-panel map).

#### 1. The Canvas Setup Plan (Non-Code Walkthrough)

When the [Plot Manager](08_plot_manager__plotmanager__.md) requests an `eViz Figure` for a map plot:

1.  **Request for a new Figure:** The `Plot Manager` calls `Figure.create_eviz_figure(config, 'xy', 'temp')`.
2.  **Get Plot Configuration:** The `create_eviz_figure` method first consults the [Configuration Manager](04_configuration_manager__configmanager__.md) to get specific settings for plotting 'temp' as an 'xy' (map) plot (e.g., is there a specific map projection or region defined?).
3.  **Determine Layout:** It then uses the `ConfigManager`'s information (like if it's a comparison plot) to decide how many rows and columns of subplots are needed (e.g., two columns for two side-by-side maps).
4.  **Initialize Figure:** A new `Figure` object is created, inheriting from Matplotlib's `Figure`.
5.  **Calculate Optimal Size:** The `Figure` then calculates an `optimal figure size` (width and height) for itself. It considers the number of subplots and whether they are maps or simple graphs, ensuring enough space for all elements.
6.  **Set Up Axes (Subplots):** The `Plot Manager` then calls the `figure.set_axes()` method.
    *   **Detect Map Plot:** The `Figure` checks the `plot_type` and sees it's a map (e.g., 'xy'). It sets an internal flag `_use_cartopy = True`.
    *   **Create Subplot Grid (`GridSpec`):** It creates a `matplotlib.gridspec.GridSpec` to define the layout of the subplots, applying calculated spacing.
    *   **Get Map Projection:** It determines the correct `Cartopy projection` (e.g., `ccrs.PlateCarree`) based on the `ConfigManager` or defaults. It also gets any specified geographical `extent`.
    *   **Create GeoAxes:** For each subplot slot (e.g., two side-by-side), it calls Matplotlib's `add_subplot()` method, but crucially, it passes the `projection` to it. This creates special `Cartopy GeoAxes` objects, which are designed for geographical plots.
    *   **Add Map Features:** To each `GeoAxes`, it automatically adds geographical features like `coastlines()`, `borders()`, and `land` features, making them ready for a map.
7.  **Figure Ready:** The `eViz Figure` is now a fully prepared canvas with its `axes_array` containing ready-to-draw `GeoAxes` objects. The `Plotter` can now get these `GeoAxes` from the `Figure` and start drawing the actual data.
8.  **Saving the Plot:** When `figure.save_plot()` is called by the `Plot Manager`, the `eViz Figure` uses Matplotlib's built-in `savefig()` to save the entire figure to the specified file.

Here's a simple sequence diagram:

```{mermaid}
sequenceDiagram
    participant PlotManager as Plot Manager
    participant FigureFactory as Figure.create_eviz_figure()
    participant eVizFigure as eViz Figure (Canvas)
    participant ConfigManager as Config Manager
    participant MatplotlibCore as Matplotlib Core
    participant CartopyLib as Cartopy Library
    participant Plotter as Plotter (Artist)

    PlotManager->>FigureFactory: Create(config, 'xy', 'temp')
    FigureFactory->>ConfigManager: Get plot config & layout (e.g., 1 row, 2 cols)
    ConfigManager-->>FigureFactory: Returns layout & settings
    FigureFactory->>eVizFigure: __init__(config, 'xy', 1, 2)
    eVizFigure->>eVizFigure: _init_frame() (Calculates figsize & GridSpec)
    FigureFactory-->>PlotManager: Returns initialized eViz Figure
    
    PlotManager->>eVizFigure: set_axes() (Prepare sub-canvases)
    eVizFigure->>ConfigManager: Get map projection details (e.g., PlateCarree, extent)
    ConfigManager-->>eVizFigure: Returns projection & extent
    eVizFigure->>MatplotlibCore: add_subplot(..., projection=PlateCarree)
    MatplotlibCore->>CartopyLib: Create GeoAxes
    CartopyLib-->>MatplotlibCore: Returns GeoAxes (subplot 1)
    eVizFigure->>MatplotlibCore: add_subplot(..., projection=PlateCarree)
    MatplotlibCore->>CartopyLib: Create GeoAxes
    CartopyLib-->>MatplotlibCore: Returns GeoAxes (subplot 2)
    eVizFigure->>CartopyLib: Add coastlines, borders to GeoAxes
    CartopyLib-->>eVizFigure: Features added
    eVizFigure-->>PlotManager: Figure with prepared GeoAxes (axes_array)
    
    PlotManager->>Plotter: plot(config, data, eVizFigure)
    Plotter->>eVizFigure: Get GeoAxes from axes_array
    Plotter->>MatplotlibCore: Draw contours on GeoAxes (using Matplotlib)
    MatplotlibCore-->>Plotter: Plot rendered on GeoAxes
    Plotter-->>PlotManager: Plotting complete
    
    PlotManager->>eVizFigure: save_plot('temp_maps.png', ...)
    eVizFigure->>MatplotlibCore: savefig('temp_maps.png', ...)
    MatplotlibCore-->>eVizFigure: File saved
    eVizFigure-->>PlotManager: Plot saved
```

#### 2. Diving into the Code

Let's look at the core code for the `Figure` class in `eviz/lib/autoviz/figure.py`.

First, the static factory method `create_eviz_figure` is the entry point for creating an `eViz Figure`:

```python
# File: eviz/lib/autoviz/figure.py (simplified static factory method)
import logging
import matplotlib.pyplot as plt # For basic matplotlib functions

# ... other imports (ConfigManager, etc.) ...

class Figure(mfigure.Figure): # Inherits from Matplotlib's base Figure
    # ... (other Figure methods will be here) ...

    @classmethod
    def create_eviz_figure(cls, config_manager, plot_type, field_name=None, 
                            nrows=None, ncols=None, **kwargs) -> "Figure":
        """
        Factory method to create an eViz Figure instance.
        It determines the layout and size before creating the Figure.
        """
        if field_name is None:
            field_name = config_manager.current_field_name
        
        # 1. Determine subplot layout (e.g., how many rows and columns are needed)
        layout = cls._determine_subplot_layout(
            config_manager, field_name, plot_type, nrows, ncols
        )
        
        # 2. Create the Figure instance (this calls the __init__ method below)
        fig = cls(config_manager, plot_type, nrows=layout[0], ncols=layout[1], **kwargs)
        
        # 3. Initialize axis-specific options from configuration
        fig._initialize_ax_opts(cls._get_plot_config(config_manager, field_name, plot_type))
        
        return fig
```
**Explanation:**
*   `@classmethod`: This means `create_eviz_figure` is a method of the class `Figure` itself, not an individual `Figure` object. It's like a blueprint for making `Figure` objects.
*   `cls._determine_subplot_layout(...)`: This helper method (which we'll simplify later) figures out the optimal `(nrows, ncols)` for the subplots based on the `config_manager`'s settings.
*   `fig = cls(...)`: This line actually creates a new `Figure` object, calling the `__init__` method (shown next) and passing the determined layout.
*   `fig._initialize_ax_opts(...)`: This helper sets up internal options for the axes (like map extent or projection) by reading from the [Configuration Manager](04_configuration_manager__configmanager__.md).

Now let's look at the `Figure`'s `__init__` method, which sets up the basic canvas properties:

```python
# File: eviz/lib/autoviz/figure.py (simplified __init__ method)
import logging
import matplotlib.figure as mfigure # The base Matplotlib Figure class
import matplotlib.gridspec as gridspec # For managing subplot layouts
import cartopy.crs as ccrs # For geographical map projections

from eviz.lib.config.config_manager import ConfigManager # To get configuration settings

class Figure(mfigure.Figure):
    """
    Enhanced Matplotlib Figure acting as the smart "canvas" for eViz.
    It handles plot layout, map projections, and overall appearance.
    """
    def __init__(self, config_manager: ConfigManager, plot_type: str, 
                 nrows: int = 1, ncols: int = 1, **kwargs):
        
        self.config_manager = config_manager
        self.plot_type = plot_type
        self._logger = logging.getLogger(__name__)
        self._subplots = (nrows, ncols) # (rows, columns) for our subplot grid
        self._use_cartopy = False      # Flag: True if this Figure needs Cartopy for maps
        self.axes_array = []           # List to store all created Matplotlib Axes (sub-canvases)
        self._ax_opts = {}             # Internal dictionary for axis-specific options (extent, projection)
        self.gs = None                 # Matplotlib GridSpec object for advanced layout

        super().__init__(**kwargs) # Call the __init__ of the base Matplotlib Figure
        self._init_frame()         # Perform initial setup: calculate size and grid spacing
```
**Explanation:**
*   `class Figure(mfigure.Figure)`: This tells Python that our `Figure` class is an extension of Matplotlib's standard `Figure`.
*   `self.config_manager`, `self.plot_type`: These store crucial information passed during creation.
*   `self._subplots`, `self.axes_array`, `self._ax_opts`, `self.gs`: These are internal attributes to manage the subplot layout, store references to the actual `Axes` objects, and hold plotting options.
*   `super().__init__(**kwargs)`: This calls the `__init__` method of the parent `matplotlib.figure.Figure` class, setting up the basic Matplotlib canvas.
*   `self._init_frame()`: This is a key helper method that calculates the optimal `figsize` (figure size) and sets up the `GridSpec` for subplot arrangement.

Next, the `_init_frame` method handles dynamic sizing and grid setup:

```python
# File: eviz/lib/autoviz/figure.py (simplified _init_frame method)
    def _init_frame(self):
        """
        Calculates the optimal figure size and subplot spacing.
        This adapts the canvas size to the number and type of plots.
        """
        # Determine the number of subplots, especially for comparison modes
        self._set_compare_diff_subplots() 
        
        # Calculate the best (width, height) for the overall figure
        figsize = self._calculate_optimal_figsize()
        self.set_size_inches(figsize) # Apply the calculated size to the Matplotlib Figure
        
        # Calculate optimal spacing between subplots and create the GridSpec
        spacing_params = self._calculate_subplot_spacing()
        self.gs = gridspec.GridSpec(*self._subplots, **spacing_params)
```
**Explanation:**
*   `self._set_compare_diff_subplots()`: This helper uses `self.config_manager` to update `self._subplots` (e.g., from `(1,1)` to `(2,1)` for a two-way comparison).
*   `self._calculate_optimal_figsize()`: This helper calculates the best `(width, height)` in inches for the figure, considering `self._subplots` and other factors.
*   `self.set_size_inches(figsize)`: This applies the calculated size to the underlying Matplotlib `Figure`.
*   `self.gs = gridspec.GridSpec(...)`: This creates a `GridSpec` object, which is like a blueprint for how the subplots will be arranged on the `Figure`, including spacing.

Once the `Figure` is initialized and its grid is set, the `Plot Manager` calls `set_axes()` to create the actual subplots (the `Axes` objects):

```python
# File: eviz/lib/autoviz/figure.py (simplified set_axes method)
import cartopy.crs as ccrs # For Cartopy map projections
import cartopy.feature as cfeature # For geographical features like coastlines

class Figure(mfigure.Figure):
    # ... (init and other methods) ...

    def set_axes(self) -> "Figure":
        """
        Creates the actual Matplotlib Axes (subplots) on the Figure.
        It intelligently decides whether to use geographical projections (Cartopy).
        """
        # Determine if Cartopy (map projection) is needed based on the plot type
        if 'tx' in self.plot_type or 'sc' in self.plot_type or 'xy' in self.plot_type:
            self._use_cartopy = True

        if self._use_cartopy:
            return self._create_subplots_crs() # Call method for Cartopy-specific subplots
        else:
            # For non-map plots, just add regular Matplotlib subplots
            for i in range(self._subplots[0]):
                for j in range(self._subplots[1]):
                    ax = self.add_subplot(self.gs[i, j]) # Add a standard Matplotlib Axes
                    self.axes_array.append(ax) # Store the Axes object
            return self
```
**Explanation:**
*   `if ... self._use_cartopy = True`: If the `plot_type` is one that requires geographical maps, a flag is set.
*   `self._create_subplots_crs()`: If `_use_cartopy` is `True`, this specialized method is called to create `Cartopy GeoAxes`.
*   `self.add_subplot(self.gs[i, j])`: If not a map, this creates a regular Matplotlib `Axes` object in the grid position specified by `self.gs[i, j]`.
*   `self.axes_array.append(ax)`: Each created `Axes` object is stored in this list, so the `Plotter` can easily access them later.

The `_create_subplots_crs` method is where the `Cartopy` magic happens:

```python
# File: eviz/lib/autoviz/figure.py (simplified _create_subplots_crs method)
import cartopy.crs as ccrs
import cartopy.feature as cfeature

class Figure(mfigure.Figure):
    # ... (init and other methods) ...

    def _create_subplots_crs(self) -> "Figure":
        """
        Creates subplots that are Cartopy GeoAxes, applying appropriate
        map projections and adding geographical features.
        """
        map_projection = self._get_projection() # Determine the map projection (e.g., PlateCarree)
        
        for i in range(self._subplots[0]):
            for j in range(self._subplots[1]):
                # This is the key line: creates a GeoAxes with a specific projection!
                ax = self.add_subplot(self.gs[i, j], projection=map_projection)
                self.axes_array.append(ax)

        # Add common geographical features to all newly created map axes
        for ax in self.axes_array:
            ax.coastlines() # Draw coastlines
            ax.add_feature(cfeature.BORDERS, linestyle=':') # Add country borders
            ax.add_feature(cfeature.LAND, edgecolor='black') # Fill land areas
        
        return self
```
**Explanation:**
*   `map_projection = self._get_projection()`: This helper method (shown next) determines which `Cartopy` projection object to use (e.g., `ccrs.PlateCarree`).
*   `ax = self.add_subplot(self.gs[i, j], projection=map_projection)`: This is crucial! By passing `projection=map_projection` to `add_subplot`, Matplotlib creates a `Cartopy GeoAxes` object instead of a regular `Axes`. This `GeoAxes` then understands geographical coordinates.
*   `ax.coastlines()`, `ax.add_feature(...)`: These lines use `Cartopy` to easily add geographical context to each map subplot.

The `_get_projection` method helps choose the right `Cartopy` projection:

```python
# File: eviz/lib/autoviz/figure.py (simplified _get_projection method)
import cartopy.crs as ccrs # The core Cartopy projection module
import numpy as np
from typing import Optional

class Figure(mfigure.Figure):
    # ... (init and other methods) ...

    def _get_projection(self, projection_name: Optional[str] = None) -> ccrs.Projection:
        """
        Retrieves a Cartopy projection object based on a name from configuration.
        Also determines the map extent and central coordinates.
        """
        extent = [-180, 180, -90, 90] # Default global geographical extent
        
        # Check if a custom extent is defined in _ax_opts (from ConfigManager)
        if 'extent' in self._ax_opts and isinstance(self._ax_opts['extent'], (list, tuple)):
            extent = list(self._ax_opts['extent'])
        
        # Calculate central longitude and latitude for certain projections
        central_lon = np.mean(extent[:2])
        central_lat = np.mean(extent[2:])
        
        # Choose the Cartopy projection based on the name or default to PlateCarree
        if projection_name is None or projection_name.lower() == 'platecarree':
            self._projection = ccrs.PlateCarree()
        elif projection_name.lower() == 'lambert':
            self._projection = ccrs.LambertConformal(
                central_longitude=central_lon, central_latitude=central_lat
            )
        # ... other projection types like 'robinson', 'orthographic' would be here ...
        
        self._ax_opts['extent'] = extent # Store the final extent
        return self._projection
```
**Explanation:**
*   `extent = [-180, 180, -90, 90]`: This is the default global map boundary. It can be overridden by settings in `_ax_opts` (which come from your [Configuration Manager](04_configuration_manager__configmanager__.md)).
*   `central_lon`, `central_lat`: These are calculated, as some projections need a central point.
*   `ccrs.PlateCarree()`, `ccrs.LambertConformal(...)`: These create specific `Cartopy Projection` objects. `PlateCarree` is a common, simple rectangular projection. `LambertConformal` is often used for regional weather maps.

Finally, after the `Plotter` has drawn the data onto the `Figure`'s `Axes`, the `eViz Figure` handles saving:

```python
# File: eviz/lib/autoviz/figure.py (simplified save_plot method)
import os
import matplotlib.pyplot as plt # Needed to close the figure

class Figure(mfigure.Figure):
    # ... (init and other methods) ...

    def save_plot(self, field_name: str, plot_idx: int) -> Optional[str]:
        """
        Saves the entire Figure to a file, using output options from ConfigManager.
        This is typically called by the Plot Manager.
        """
        # Check if saving to file is enabled in the configuration
        if not self.config_manager.output_config.print_to_file:
            self.logger.debug("Configured not to save plot to file.")
            return None

        output_dir = self.config_manager.output_config.output_dir
        file_ext = self.config_manager.output_config.print_format
        
        # Construct a unique filename for the output plot
        fname_prefix = f"{field_name}_{self.plot_type}_{plot_idx}"
        output_filepath = os.path.join(output_dir, f"{fname_prefix}.{file_ext}")

        self.logger.info(f"Saving plot to: {output_filepath}")
        try:
            # Use Matplotlib's built-in savefig method to save the entire figure
            self.savefig(output_filepath, dpi=300, bbox_inches='tight')
            plt.close(self) # Close the Matplotlib figure to free up system memory
            return output_filepath
        except Exception as e:
            self.logger.error(f"Error saving figure to {output_filepath}: {e}")
            return None
```
**Explanation:**
*   `self.config_manager.output_config.print_to_file`: Checks the [Configuration Manager](04_configuration_manager__configmanager__.md) to see if plots should be saved.
*   `output_dir`, `file_ext`: Retrieves the output directory and file format (e.g., 'png') from the `ConfigManager`.
*   `self.savefig(...)`: This is Matplotlib's powerful built-in method to save the `Figure` to a file. `dpi=300` sets the resolution, and `bbox_inches='tight'` ensures no extra white space around the plot.
*   `plt.close(self)`: After saving, it's good practice to close the figure to release memory, especially when generating many plots automatically.

## Summary

### Conclusion

In this chapter, you've learned that the **Figure (eViz Figure)** is the "smart canvas" of EViz. It's an enhanced Matplotlib `Figure` that automatically handles the complex tasks of organizing subplots, setting up geographical map projections (using Cartopy), adding map features, and intelligently sizing itself. The [Plot Manager](08_plot_manager__plotmanager__.md) creates and prepares this smart canvas, allowing the [Plotter](09_plotter__baseplotter_and_backends__.md) to simply "paint" the data onto its ready-made sub-canvases. This powerful abstraction ensures that your scientific visualizations are always well-structured, geographically accurate, and visually appealing.

This concludes our journey through the core components of EViz! You now have a solid understanding of how EViz turns raw data into beautiful, insightful visualizations.

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)