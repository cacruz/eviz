# Chapter 9: Plotter (BasePlotter and backends)

Welcome back! In our last chapter, [Chapter 8: Plot Manager (PlotManager)](08_plot_manager__plotmanager__.md), we met the "director" of our visualization efforts, the `PlotManager`. It takes our perfectly prepared data and detailed instructions, then smartly decides *what* kind of plot to make and *which tool* to use.

Now, imagine the director has made all the decisions and has the script (instructions), the actors (data), and the stage (a blank figure). Who actually *performs* the scene and paints the beautiful picture? That's the job of the **Plotter**!

### What Problem Do Plotters Solve?

Think of a plotting library like a set of art supplies:
*   **Matplotlib** is like a traditional set of oil paints and brushes – powerful, versatile, but sometimes requires a lot of setup for each stroke.
*   **HvPlot** is like a modern digital art tablet with smart features – it's great for interactive plots and automatically handles many details.
*   **Altair** is like a minimalist graphic design tool – perfect for clean, declarative, web-friendly charts.

Each of these tools has its own unique way of drawing lines, coloring areas, and adding labels. If the [Plot Manager](08_plot_manager__plotmanager__.md) had to know the exact commands for *every* plotting library and *every* plot type, it would be a huge, unmanageable mess!

**Plotters solve this by being the actual "artists" that draw the plots.** Each Plotter is an expert in using a *specific* art tool (like Matplotlib) to draw a *specific* type of picture (like an XY map).

*   `MatplotlibXYPlotter` knows exactly how to draw an XY map using Matplotlib.
*   `HvplotXYPlotter` knows how to draw an interactive XY map using HvPlot.
*   `AltairXYPlotter` knows how to draw a web-friendly XY map using Altair.

This way, the [Plot Manager](08_plot_manager__plotmanager__.md) simply tells the right Plotter, "Draw an XY map of temperature," and doesn't need to worry about the underlying technical details of Matplotlib's `contourf` function or HvPlot's `hvplot.image` method. It delegates the actual drawing to the specialist.

#### Our Use Case: Drawing an XY Map of Temperature using Matplotlib

Let's revisit our use case from the previous chapter. You have a prepared 2D slice of temperature data, and the [Plot Manager](08_plot_manager__plotmanager__.md) needs to create an XY (geographical) map of it, specifically using the Matplotlib library, and save it.

For this, the `PlotManager` will need to:
1.  **Find the `MatplotlibXYPlotter`** (the artist who specializes in Matplotlib XY maps).
2.  **Give this `MatplotlibXYPlotter` the data** and the blank canvas ([Figure](10_figure__eviz_figure__.md)).
3.  **Tell the `MatplotlibXYPlotter` to draw** the temperature map.

The `MatplotlibXYPlotter` will then use Matplotlib's functions to actually render the map and return the completed [Figure](10_figure__eviz_figure__.md).

### Key Concepts: The Specialized Artists

Plotters are the hands-on workers who turn data into visible plots.

*   **`BasePlotter` (The Generic Artist):** This is the **abstract base class** for all Plotters. Think of it as the basic job description for *any* artist in EViz. It defines common actions like "draw a plot," "save the plot," and "show the plot." Every specific Plotter must be able to do these things, even if *how* they do them differs.
*   **Specialized Plotter Types (e.g., `XYPlotter`, `XTPlotter`, `ScatterPlotter`):** These are further abstract blueprints for specific *types* of plots. For example, `XYPlotter` defines what any artist who draws XY (latitude-longitude) maps must be able to do.
*   **Backends (Matplotlib, HvPlot, Altair):** These are the actual software libraries that do the drawing. They are the "art supplies" or "tools" an artist uses.
    *   **Matplotlib:** A widely used, highly customizable plotting library for Python.
    *   **HvPlot / HoloViews:** Libraries built for interactive and dashboard-friendly plots, often used with Bokeh or Plotly.
    *   **Altair:** A declarative statistical visualization library based on Vega-Lite, excellent for interactive web-based plots.
*   **Concrete Plotters (e.g., `MatplotlibXYPlotter`, `HvplotXYPlotter`, `AltairXYPlotter`):** These are the actual "artists" that implement the abstract ideas.
    *   `MatplotlibXYPlotter` *is* an `XYPlotter` and uses the Matplotlib backend.
    *   `HvplotXYPlotter` *is* an `XYPlotter` and uses the HvPlot backend.
    *   They each have unique code in their `plot()` method to draw the specific visualization using their chosen library.
*   **The Plotter Factory:** The [Plot Manager](08_plot_manager__plotmanager__.md) doesn't directly create a `MatplotlibXYPlotter`. Instead, it asks a `PlotterFactory`, "Give me an XY Plotter that uses Matplotlib," and the factory hands back the correct instance.

### How Plotters are Used (by PlotManager)

As a user, you don't directly interact with Plotters. You simply specify in your configuration (managed by [ConfigManager](04_configuration_manager__configmanager__.md)) which `plot_type` (e.g., `xy`) and `backend` (e.g., `matplotlib`) you want.

The [Plot Manager (PlotManager)](08_plot_manager__plotmanager__.md) then handles the rest:

1.  **`PlotManager` asks `PlotterFactory`:** When `PlotManager.plot()` is called (by the [Model Source](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md)), for each plot instruction, it first calls `plotter_factory.get_plotter(plot_type)`. This gets the right artist.
2.  **`PlotManager` prepares the canvas:** It then creates a `Figure` object (our blank canvas, covered in the next chapter).
3.  **`PlotManager` tells the Plotter to `plot()`:** Finally, it calls the `plot()` method of the chosen Plotter, passing it the prepared data, the configuration, and the `Figure` object.

This flow completely hides the complexity of different plotting libraries from the rest of EViz.

### Under the Hood: Plotter's Workflow

Let's trace the steps when the [Plot Manager](08_plot_manager__plotmanager__.md) needs to create an XY map using Matplotlib.

#### 1. The Artists' Plan (Non-Code Walkthrough)

1.  **`PlotManager` needs an artist:** The [Plot Manager](08_plot_manager__plotmanager__.md) has the temperature `xarray.DataArray`, the `ConfigManager` (with all plot settings, including `plot_type='xy'` and `backend='matplotlib'`), and a new `Figure` object (the canvas).
2.  **`PlotManager` consults `PlotterFactory`:** It asks the `PlotterFactory`, "I need an `xy` plotter using the `matplotlib` backend."
3.  **`PlotterFactory` creates `MatplotlibXYPlotter`:** The factory looks up its list and creates an instance of `MatplotlibXYPlotter`, then hands it back to the `PlotManager`.
4.  **`PlotManager` gives instructions to `MatplotlibXYPlotter`:** The `PlotManager` then calls `matplotlib_xy_plotter.plot(config, data_to_plot_tuple)`, passing the configuration, the `xarray.DataArray` (temperature), its coordinates (lon, lat), and the `Figure` object.
5.  **`MatplotlibXYPlotter` draws:** Inside its `plot()` method, the `MatplotlibXYPlotter`:
    *   Gets the Matplotlib `Axes` object from the `Figure` (this is where the drawing happens).
    *   Uses Matplotlib functions like `ax.contourf()` to draw the filled contours of temperature.
    *   Adds a title, labels, and a colorbar using other Matplotlib commands.
    *   The plot is now "drawn" on the `Figure` object.
6.  **`MatplotlibXYPlotter` finishes:** It returns the modified `Figure` object to the `PlotManager`.
7.  **`PlotManager` handles output:** The [Plot Manager](08_plot_manager__plotmanager__.md) then tells the `Figure` to save itself as a PNG file.

Here's a simple sequence diagram:

```{mermaid}
sequenceDiagram
    participant PlotManager as Plot Manager (Director)
    participant ConfigManager as Config Manager (Recipe Book)
    participant PlotterFactory as Plotter Factory
    participant MatplotlibXYPlotter as MatplotlibXYPlotter (Artist)
    participant Figure as Figure (Canvas)
    participant MatplotlibLib as Matplotlib Library

    PlotManager->>ConfigManager: Get plot settings (type='xy', backend='matplotlib', field='temp')
    ConfigManager-->>PlotManager: Returns settings
    PlotManager->>Figure: Create blank canvas
    PlotManager->>PlotterFactory: "Give me 'xy' plotter for 'matplotlib'!"
    PlotterFactory-->>PlotManager: Returns MatplotlibXYPlotter
    PlotManager->>MatplotlibXYPlotter: plot(config, (temp_data, lon, lat, 'temp', Figure))
    MatplotlibXYPlotter->>Figure: Get subplot Axes
    MatplotlibXYPlotter->>MatplotlibLib: Call `ax.contourf()`, `ax.set_title()`, `fig.colorbar()`
    MatplotlibLib-->>MatplotlibXYPlotter: Drawing complete on Axes
    MatplotlibXYPlotter-->>PlotManager: Figure (now with plot)
    PlotManager->>Figure: save_plot("temp_map.png")
    Figure->>MatplotlibLib: Call `fig.savefig()`
    MatplotlibLib-->>Figure: File saved
    Figure-->>PlotManager: Plot saved
```

#### 2. Diving into the Code

Let's look at how this is implemented in EViz.

**The `PlotterFactory` (`eviz/lib/autoviz/plotting/factory.py`)**

This factory is responsible for creating the right Plotter instance.

```python
# File: eviz/lib/autoviz/plotting/factory.py (simplified)
from .backends.matplotlib.xy_plot import MatplotlibXYPlotter
from .backends.hvplot.xy_plot import HvplotXYPlotter
from .backends.altair.xy_plot import AltairXYPlotter
# ... other plotter imports ...

class PlotterFactory:
    """Factory for creating appropriate plotters."""
    
    @staticmethod
    def create_plotter(plot_type, backend="matplotlib"):
        """Create a plotter for the given plot type and backend."""
        plotters_map = {
            ("xy", "matplotlib"): MatplotlibXYPlotter,
            ("xt", "matplotlib"): MatplotlibXTPlotter, # For time series
            ("xy", "hvplot"): HvplotXYPlotter,
            ("xy", "altair"): AltairXYPlotter,
            # ... many more (plot_type, backend) mappings ...
        }
        
        key = (plot_type, backend)
        if key in plotters_map:
            return plotters_map[key]() # Create and return an instance
        else:
            raise ValueError(f"No plotter available for {plot_type}, {backend}")
```
**Explanation:**
*   The `plotters_map` dictionary holds all the available `Plotter` classes, indexed by a `(plot_type, backend)` tuple.
*   When `create_plotter` is called, it constructs this `key` (e.g., `('xy', 'matplotlib')`) and retrieves the correct class from the map.
*   `return plotters_map[key]()` then creates a new object (an instance) of that class (e.g., `MatplotlibXYPlotter()`) and returns it.

**The `BasePlotter` and `XYPlotter` blueprints (`eviz/lib/autoviz/plotting/base.py`)**

These define the common interface for all Plotters.

```python
# File: eviz/lib/autoviz/plotting/base.py (simplified)
from abc import ABC, abstractmethod
import logging

class BasePlotter(ABC):
    """Abstract base class for all plotters."""
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.plot_object = None # Stores the actual plot created by the backend
    
    @abstractmethod
    def plot(self, config, data_to_plot_tuple):
        """Create a plot from the given data and configuration."""
        pass # Must be implemented by subclasses
        
    @abstractmethod
    def save(self, filename, **kwargs):
        """Save the plot to a file."""
        pass # Must be implemented by subclasses
        
    @abstractmethod
    def show(self):
        """Display the plot."""
        pass # Must be implemented by subclasses
    
    def get_plot_object(self):
        """Return the underlying plot object (e.g., Matplotlib Figure, Altair Chart)."""
        return self.plot_object

class XYPlotter(BasePlotter):
    """Base class for XY (lat-lon) plotters."""
    # It also requires the 'plot' method to be implemented, specific to XY plots.
    @abstractmethod
    def plot(self, config, data_to_plot_tuple):
        """Create an XY plot from the given data."""
        pass
```
**Explanation:**
*   `BasePlotter(ABC)` makes it an Abstract Base Class, meaning you can't create an instance of `BasePlotter` directly. It only defines what methods *must* exist.
*   `@abstractmethod` indicates methods that must be implemented by any concrete class that inherits from `BasePlotter`.
*   `XYPlotter` further refines this, making sure any Plotter that specializes in XY maps also implements the `plot` method.

**`MatplotlibXYPlotter` - The Matplotlib Artist (`eviz/lib/autoviz/plotting/backends/matplotlib/xy_plot.py`)**

This is the actual artist for our use case! It inherits from `MatplotlibBasePlotter` (which provides common Matplotlib functionalities) and implements the `plot` method for XY maps.

```python
# File: eviz/lib/autoviz/plotting/backends/matplotlib/xy_plot.py (simplified)
import matplotlib as mpl
import cartopy.crs as ccrs # For geographical maps
import numpy as np
from .base import MatplotlibBasePlotter # Inherits common Matplotlib setup

class MatplotlibXYPlotter(MatplotlibBasePlotter):
    """Matplotlib implementation of XY plotting."""
    def __init__(self):
        super().__init__()
        self.fig = None # Will hold the Matplotlib Figure
        self.ax = None  # Will hold the Matplotlib Axes
            
    def plot(self, config, data_to_plot_tuple):
        """
        Create an XY plot using Matplotlib.
        data_to_plot_tuple contains (data2d, x, y, field_name, plot_idx, figure_obj).
        """
        data2d, x, y, field_name, _, figure_obj = data_to_plot_tuple
        
        if data2d is None: return figure_obj # Nothing to plot

        self.fig = figure_obj # Our canvas
        # Get the correct Axes object from the Figure based on current plot index
        self.ax = self.fig.get_axes()[config.axindex] 
        
        # Apply plot options and text (simplified details)
        self.ax_opts = self.fig.update_ax_opts(field_name, self.ax, 'xy', level=config.level)
        self.plot_text(config, field_name=field_name, pid='xy') # Add title/labels

        # This is the core Matplotlib drawing command!
        cfilled = self.filled_contours(config, field_name, self.ax, x, y, data2d, 
                                       transform=ccrs.PlateCarree())
        
        # Add colorbar (simplified handling)
        if cfilled is not None:
            self.set_colorbar(config, cfilled, self.fig, self.ax, 0, field_name, data2d)
        
        self.plot_object = self.fig # Store the Matplotlib Figure object
        return self.fig

    def save(self, filename, **kwargs):
        """Save the plot to a file."""
        if self.plot_object:
            self.plot_object.savefig(filename, **kwargs)
        else:
            self.logger.warning("No plot object to save.")

    def show(self):
        """Display the plot."""
        if self.plot_object:
            mpl.pyplot.show()
        else:
            self.logger.warning("No plot object to show.")
```
**Explanation:**
*   `class MatplotlibXYPlotter(MatplotlibBasePlotter)`: It inherits common Matplotlib utilities from `MatplotlibBasePlotter`.
*   `plot(self, config, data_to_plot_tuple)`: This method implements the abstract `plot` method.
    *   It unpacks `data_to_plot_tuple` to get `data2d` (our temperature data), `x`, `y` (coordinates), `field_name` (e.g., 'temp'), and the `figure_obj` (our canvas).
    *   `self.ax = self.fig.get_axes()[config.axindex]` gets the specific subplot `Axes` object on the `Figure` where this plot should be drawn.
    *   `self.filled_contours(...)`: This is a helper method (from `MatplotlibBasePlotter`) that actually calls Matplotlib's `ax.contourf()` to draw the colored map.
    *   `self.set_colorbar(...)`: Another helper to add the color scale.
    *   `self.plot_object = self.fig`: The resulting Matplotlib Figure is stored, making it available for saving or showing.

**`AltairXYPlotter` - The Altair Artist (`eviz/lib/autoviz/plotting/backends/altair/xy_plot.py`)**

For comparison, here's a simplified view of how an Altair plotter would work:

```python
# File: eviz/lib/autoviz/plotting/backends/altair/xy_plot.py (simplified)
import altair as alt
import pandas as pd
from eviz.lib.autoviz.plotting.base import XYPlotter

class AltairXYPlotter(XYPlotter):
    """Altair implementation of XY plotting."""
    def __init__(self):
        super().__init__()
        alt.data_transformers.disable_max_rows() # Important for large datasets
    
    def plot(self, config, data_to_plot_tuple):
        """
        Create an interactive XY plot using Altair.
        data_to_plot_tuple contains (data2d, x, y, field_name, plot_idx, figure_obj).
        """
        data2d, x, y, field_name, _, _ = data_to_plot_tuple # Figure object often not used directly by Altair
        
        if data2d is None: return None

        # Altair often works best with pandas DataFrames
        # This converts the xarray DataArray into a pandas DataFrame
        df = self._convert_to_dataframe(data2d, x, y)
        
        title = field_name
        cmap = config.ax_opts.get('use_cmap', 'viridis')
        # Altair uses Vega color schemes, so conversion might be needed
        vega_scheme = 'viridis' # Simplified
        
        # This is the core Altair drawing command!
        chart = alt.Chart(df).mark_square().encode(
            x=alt.X('x:Q', title=x.name), # 'Q' means quantitative data
            y=alt.Y('y:Q', title=y.name),
            color=alt.Color('value:Q', scale=alt.Scale(scheme=vega_scheme), title=field_name),
            tooltip=[alt.Tooltip('x:Q'), alt.Tooltip('y:Q'), alt.Tooltip('value:Q')]
        ).properties(
            width=800, height=500, title=title
        ).interactive() # Makes the plot interactive (zoom, pan)
        
        self.plot_object = chart # Store the Altair chart object
        return chart

    def _convert_to_dataframe(self, data2d, x, y):
        """Helper to convert xarray DataArray to pandas DataFrame."""
        # Simplified for brevity. In reality, it handles various cases.
        df = data2d.to_dataframe(name='value').reset_index()
        df = df.rename(columns={x.name: 'x', y.name: 'y'}) # Standardize column names
        return df

    def save(self, filename, **kwargs):
        """Save the plot to a file."""
        if self.plot_object:
            self.plot_object.save(filename, **kwargs)
    # ... show method omitted ...
```
**Explanation:**
*   `plot()` method unpacks the `data_to_plot_tuple`. Note how Altair often works with `pandas.DataFrame`s, so `_convert_to_dataframe` is used.
*   `alt.Chart(df).mark_square().encode(...)`: This is the declarative way Altair builds a plot, specifying what goes on the x-axis, y-axis, and what determines the color. `.interactive()` adds interactivity.
*   The `plot_object` here stores an `altair.Chart` object.

**`HvplotXYPlotter` - The HvPlot Artist (`eviz/lib/autoviz/plotting/backends/hvplot/xy_plot.py`)**

And a similar view for HvPlot:

```python
# File: eviz/lib/autoviz/plotting/backends/hvplot/xy_plot.py (simplified)
import hvplot.xarray # noqa, this registers .hvplot accessor on xarray objects
import holoviews as hv
from eviz.lib.autoviz.plotting.base import XYPlotter

class HvplotXYPlotter(XYPlotter):
    """HvPlot implementation of XY plotting."""
    def __init__(self):
        super().__init__()
        # Initialize HoloViews extension for interactive plots (e.g., Bokeh)
        try: hv.extension('bokeh')
        except Exception: pass # Handle if extension fails
    
    def plot(self, config, data_to_plot_tuple):
        """
        Create an interactive XY plot using HvPlot.
        data_to_plot_tuple contains (data2d, x, y, field_name, plot_idx, figure_obj).
        """
        data2d, x, y, field_name, _, _ = data_to_plot_tuple
        
        if data2d is None: return None

        x_dim = x.name if hasattr(x, 'name') else 'lon' # Get dimension names
        y_dim = y.name if hasattr(y, 'name') else 'lat'

        cmap = config.ax_opts.get('use_cmap', 'viridis')
        title = field_name
        
        # This is the core HvPlot command, leveraging xarray's .hvplot accessor!
        plot = data2d.hvplot.image(
            x=x_dim,
            y=y_dim,
            cmap=cmap,
            title=title,
            width=800,
            height=500,
            colorbar=True,
            clabel=field_name, # Colorbar label
            tools=['pan', 'wheel_zoom', 'hover'] # Interactive tools
        )
        
        self.plot_object = plot # Store the HoloViews object
        return plot

    def save(self, filename, **kwargs):
        """Save the plot to a file (might require specific renderers)."""
        # Saving HvPlot can be more complex, often needing specific export tools
        self.logger.warning("HvPlot saving currently not fully implemented in this simplified example.")
    # ... show method omitted ...
```
**Explanation:**
*   `hvplot.xarray` is imported to enable the `.hvplot` accessor on `xarray.DataArray` objects.
*   `data2d.hvplot.image(...)`: This is the direct, concise way HvPlot creates interactive images from `xarray` data. It automatically handles many details like axes labels and interactive tools.
*   The `plot_object` here stores a `holoviews.core.spaces.HoloMap` or `holoviews.Image` object.

These different Plotters demonstrate how EViz abstracts away the details of various plotting libraries, providing a consistent interface (`plot`, `save`, `show`) for the [Plot Manager](08_plot_manager__plotmanager__.md) to work with.

### Conclusion

In this chapter, you've learned that **Plotters (BasePlotter and backends)** are the actual "artists" who draw the visualizations in EViz. `BasePlotter` provides a common blueprint for what any artist should do, while specialized concrete Plotters (like `MatplotlibXYPlotter`, `HvplotXYPlotter`, `AltairXYPlotter`) know how to use specific libraries (Matplotlib, HvPlot, Altair) to draw specific types of plots (like XY maps). The [Plot Manager (PlotManager)](08_plot_manager__plotmanager__.md) selects the right Plotter, hands it the data and a canvas, and lets the Plotter perform the detailed drawing. This makes EViz flexible and able to leverage various powerful plotting tools.

Now that we understand who draws the plots, the next logical step is to understand the "canvas" itself – the object that holds the plot and manages its layout and saving. In the next chapter, we'll dive into the [Figure (eViz Figure)](10_figure__eviz_figure__.md).

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)