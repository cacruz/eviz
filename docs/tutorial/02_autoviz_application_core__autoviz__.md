# Chapter 2: Autoviz Application Core (Autoviz)

Welcome back! In [Chapter 1: Streamlit Web Interface (sViz)](01_streamlit_web_interface__sviz__.md), we learned about `sViz` – the user-friendly website that lets you click buttons and select options to get your visualizations. Think of `sViz` as the "face" of EViz, making everything look easy. But who does the heavy lifting behind that friendly face? That's where **Autoviz Application Core (Autoviz)** comes in.

## Overview

### What Problem Does Autoviz Solve?

Imagine you want to bake a cake. `sViz` is like the online ordering app where you pick your cake type and frosting. But Autoviz is the *chef* in the kitchen!

Generating scientific plots isn't just about drawing lines and colors. It involves many complex steps:
1.  **Finding the right ingredients:** Locating your scientific data files.
2.  **Understanding the recipe:** Knowing what kind of plots to make, which variables to use, and all the specific settings (colors, titles, units).
3.  **Mixing and baking:** Reading the data, performing calculations, and preparing it for plotting.
4.  **Decorating:** Actually creating the beautiful plots and saving them.

Doing all this manually for every visualization can be incredibly time-consuming, repetitive, and prone to errors.

**Autoviz solves this by being the central orchestrator.** It takes your instructions (like "make temperature maps for this dataset using these settings"), figures out all the detailed steps, and then tells the specialized components of EViz exactly what to do. It ensures that the right data is processed in the right way to create the desired plots automatically.

#### Our Use Case: Automatic Plot Generation from the Command Line

Let's say you're a scientist or data analyst, and you don't always want to use a web interface. You prefer to run a simple command to get your plots. Specifically, you want to:
1.  **Tell EViz which type of data you have** (e.g., "gridded" data, which is common for Earth System Models).
2.  **Provide a set of instructions** (configurations) for how you want the plots to look.
3.  **Automatically generate a collection of standard plots** (like maps of temperature, pressure, or wind) and save them to your computer.

Autoviz is designed to handle this workflow seamlessly, acting as the brain for the entire visualization process.

## Core Concepts

### Key Concepts: The Central Conductor

Autoviz plays a crucial role, like a conductor leading an orchestra. Here are its main responsibilities:

*   **Main Entry Point:** It's the primary way to start the visualization process without `sViz`. When `sViz` needs plots, it "talks" to Autoviz.
*   **Receiving Instructions:** Autoviz needs to know what to do. It gets its marching orders from:
    *   **Command-Line Arguments:** Simple instructions you type when running `autoviz.py`.
    *   **Configuration Files:** Detailed "recipes" (usually YAML files) that specify everything about the data, plots, and output. Autoviz uses the [Configuration Manager (ConfigManager)](04_configuration_manager__configmanager__.md) to handle these.
*   **Orchestration and Delegation:** Autoviz itself doesn't draw the plots or read the data directly. Instead, it delegates these tasks to specialized "musicians" (other EViz components). It makes sure everyone plays their part at the right time.
    *   It identifies the type of data using a "factory" that creates the correct [Model Source (GenericDataSource / GriddedDataSource / ObservationalDataSource)](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md) object.
    *   This "model" then coordinates the actual [Data Processing Pipeline (DataPipeline)](07_data_processing_pipeline__datapipeline__.md) and [Plot Manager (PlotManager)](08_plot_manager__plotmanager__.md).

## Getting Started

### How to Use Autoviz

You can interact with Autoviz directly from your computer's terminal (or command prompt). This is how `sViz` would internally tell Autoviz to get to work.

#### 1. Running Autoviz from the Command Line

To achieve our use case (generate standard plots for 'gridded' data using configurations), you'd typically run a command similar to this:

```bash
python autoviz.py -s gridded -c /path/to/my_eviz_configs
```

**What happens?**
*   `python autoviz.py`: This tells your computer to run the `autoviz.py` script, which is the heart of Autoviz.
*   `-s gridded`: This is an "argument" telling Autoviz that we are working with `gridded` data (a common format for many Earth System Models).
*   `-c /path/to/my_eviz_configs`: This tells Autoviz where to find the detailed configuration files (our "recipes") for `gridded` data. These files specify *exactly* which plots to make, what variables to use, and how to save them.

After running this command, Autoviz will get to work. You'll see messages in your terminal indicating its progress, and eventually, a set of plots and GIFs will be generated and saved into a specified output directory on your computer.

Here's a simplified look at the `main` function in `autoviz.py` that handles this:

```python
# File: autoviz.py
import argparse
# ... (other imports and helper functions omitted) ...
from eviz.lib.autoviz.base import Autoviz # Our Autoviz class!

def parse_command_line() -> argparse.Namespace:
    """Parses command line arguments like -s and -c."""
    parser = argparse.ArgumentParser(description='Arguments being passed')
    parser.add_argument('-s', '--sources', nargs='+', required=True,
                         help='Source type (gridded, wrf, etc.)')
    parser.add_argument('--config', '-c', nargs='+', required=False,
                        help='Directory containing YAML configuration files')
    # ... (other arguments omitted for simplicity) ...
    args = parser.parse_args()
    return args

def main():
    """Main driver for the autoviz plotting tool."""
    args = parse_command_line() # 1. Get instructions from the command line

    # Simplified logic: focus on plot generation, not metadata
    # ... (metadata extraction logic omitted) ...

    # Prepare source name for Autoviz
    input_sources = [s.strip() for s in args.sources[0].split(',')]

    for source in input_sources:
        print(f"Processing source: {source}")
        # 2. Create an Autoviz instance
        autoviz = Autoviz([source], args=args)
        # 3. Tell Autoviz to run the visualization process!
        autoviz.run()

if __name__ == "__main__":
    main()
```

**Explanation:**
*   `parse_command_line()`: This function looks at what you typed after `python autoviz.py` and neatly organizes those instructions (like `-s gridded`) into an `args` object.
*   `autoviz = Autoviz([source], args=args)`: This line creates a new "Autoviz conductor" object. We pass it the `source` (like 'gridded') and all the `args` (your instructions).
*   `autoviz.run()`: This is the command that tells the conductor to start the concert – to begin the entire visualization process.

## Technical Details

### Under the Hood: Autoviz's Workflow

Let's peek behind the curtain to see how Autoviz orchestrates everything.

#### 1. The Conductor's Plan (Non-Code Walkthrough)

When you (or `sViz`) tell Autoviz to `run()`, here's a simplified step-by-step of what happens:

1.  **Receive Instructions:** Autoviz first gathers all the instructions from the command line and loads the detailed configurations using the [Configuration Manager (ConfigManager)](04_configuration_manager__configmanager__.md). This is like the conductor reading the full musical score.
2.  **Identify Data Type:** Based on your `source` (e.g., 'gridded'), Autoviz determines what kind of data it's dealing with.
3.  **Find the Right Expert:** It then uses a special "factory" (a tool for creating objects) to create a specific [Model Source (GenericDataSource / GriddedDataSource / ObservationalDataSource)](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md) object. This object is specialized to handle *your specific type* of data. For `gridded` data, it creates a `GriddedDataSource` object.
4.  **Delegate to the Model:** Autoviz hands over control to this specialized "model" object. From this point, the `Model Source` takes charge of:
    *   Loading and processing the data (using the [Data Processing Pipeline (DataPipeline)](07_data_processing_pipeline__datapipeline__.md)).
    *   Setting up the plotting (using the [Plot Manager (PlotManager)](08_plot_manager__plotmanager__.md)).
    *   Generating and saving the actual plots.
5.  **Report Back:** Once the plots are generated and saved, the `Model Source` finishes its task, and Autoviz reports that the visualization process is complete.

Here's a simple sequence diagram to visualize this flow:

```{mermaid}
sequenceDiagram
    participant UserOrSViz as User / sViz
    participant AutovizCLI as autoviz.py (CLI)
    participant AutovizCore as Autoviz Class (The Conductor)
    participant ConfigManager as Configuration Manager
    participant DataSourceFactory as Data Source Factory
    participant ModelSource as Model Source (e.g., Gridded Data)

    UserOrSViz->>AutovizCLI: Run command (`python autoviz.py -s gridded ...`)
    AutovizCLI->>AutovizCore: Initialize Autoviz (pass source & args)
    AutovizCore->>ConfigManager: Load configuration settings
    ConfigManager-->>AutovizCore: Returns all config details
    AutovizCore->>DataSourceFactory: Ask for factory for "gridded" source
    DataSourceFactory-->>AutovizCore: Returns GriddedSourceFactory
    AutovizCore->>ModelSource: Create actual GriddedDataSource object (the specific expert)
    ModelSource->>ModelSource: **[Takes over]** Process data, generate plots (using DataPipeline, PlotManager, etc.)
    ModelSource-->>AutovizCore: Plots/GIFs saved to disk
    AutovizCore-->>AutovizCLI: Visualization process finished
    AutovizCLI-->>UserOrSViz: Command completed
```

#### 2. Diving into the Code

The `Autoviz` class in `eviz/lib/autoviz/base.py` is where our conductor lives.

First, let's see how Autoviz gets ready:

```python
# File: eviz/lib/autoviz/base.py
import logging
from argparse import Namespace
from dataclasses import dataclass, field

from eviz.lib.config.config_manager import ConfigManager # For config!
# Other factories for specific data types
from eviz.models.source_factory import GriddedSourceFactory # For gridded data!

# ... (helper functions like get_config_path_from_env and create_config omitted) ...

def get_factory_from_user_input(inputs) -> list:
    """
    Return factory classes associated with user input sources.
    This maps a source name (like 'gridded') to its factory.
    """
    mappings = {
        "gridded": GriddedSourceFactory(),    # Our gridded data expert
        # ... (other mappings for 'wrf', 'omi', etc. omitted) ...
    }
    factories = []
    for i in inputs:
        if i not in mappings:
            print(f"\nERROR: '{i}' is not a valid source name.\n")
            import sys; sys.exit(1)
        factories.append(mappings[i])
    return factories

@dataclass
class Autoviz:
    """Main class for automatic visualization."""
    source_names: list
    args: Namespace = None
    _config_manager: ConfigManager = None
    factory_sources: list = field(init=False) # List of factories for our sources

    def __post_init__(self):
        """Initializes Autoviz, setting up config and data factories."""
        self.logger.debug("Autoviz initialization")
        if not self.args: # If no args provided (e.g., in notebooks)
            self.args = Namespace(sources=self.source_names, compare=False, ...)
        
        # 1. Get the right "factory" for our data type (e.g., GriddedSourceFactory)
        self.factory_sources = get_factory_from_user_input(self.source_names)
        
        # 2. Load all configurations using the ConfigManager
        self._config_manager = create_config(self.args) 
```

**Explanation:**
*   `get_factory_from_user_input()`: This function is like a directory of experts. If you ask for "gridded" data, it gives you a `GriddedSourceFactory`. This "factory" knows how to create the specific `GriddedDataSource` object later.
*   `@dataclass class Autoviz:`: This defines our main `Autoviz` class.
*   `__post_init__()`: This special method runs right after an `Autoviz` object is created.
    *   `self.factory_sources = get_factory_from_user_input(...)`: Here, Autoviz asks for the correct factory based on the `source_names` you provided (e.g., 'gridded').
    *   `self._config_manager = create_config(self.args)`: It then initializes the [Configuration Manager (ConfigManager)](04_configuration_manager__configmanager__.md), loading all the detailed settings from your configuration files.

Finally, the `run()` method in the `Autoviz` class kicks off the main process:

```python
# File: eviz/lib/autoviz/base.py (continued)
# ... (imports and Autoviz class definition) ...

@dataclass
class Autoviz:
    # ... (attributes and __post_init__ as above) ...

    def run(self):
        """Execute the visualization process."""
        self.logger.info("Execute the visualization process")
        
        # This component uses the ConfigManager to prepare the entire workflow
        self.config_adapter.process_configuration() 

        # Now, for each data type (source), create the actual "Model" object
        for factory in self.factory_sources:
            # 1. Use the factory to create the specific Model Source (e.g., GriddedDataSource)
            model = factory.create_root_instance(self._config_manager)

            # 2. Tell the Model Source to do its work (process data and generate plots)
            model() # This special call starts the data processing and plotting!
```

**Explanation:**
*   `self.config_adapter.process_configuration()`: This important step uses the loaded configurations to set up the entire visualization "pipeline." It prepares the instructions for data handling and plotting.
*   `for factory in self.factory_sources:`: Since you might want to process multiple data sources, Autoviz loops through each one.
*   `model = factory.create_root_instance(self._config_manager)`: This is where the `factory` (e.g., `GriddedSourceFactory`) actually *creates* the specialized [Model Source (GenericDataSource / GriddedDataSource / ObservationalDataSource)](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md) object (e.g., `GriddedDataSource`). This `model` object is the "expert" for your specific data.
*   `model()`: This seemingly simple line is the magic! It's a special way to call the `run` method of the `model` object itself. This is where the `GriddedDataSource` takes control, uses the [Data Processing Pipeline (DataPipeline)](07_data_processing_pipeline__datapipeline__.md) to get data, passes it to the [Plot Manager (PlotManager)](08_plot_manager__plotmanager__.md) to create plots, and saves them.

## Summary

### Conclusion

In this chapter, you've learned that **Autoviz Application Core (Autoviz)** is the central brain of EViz. It's the "conductor" that takes your high-level instructions (from the command line or `sViz`), loads detailed configurations, identifies the data type, and then delegates the actual data processing and plot generation to specialized components like the [Model Source](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md) objects. It ensures that EViz can automatically and efficiently turn raw data into insightful visualizations.

You now understand that `sViz` is the friendly portal, and Autoviz is the powerful engine working behind it. In the next chapter, we'll explore another useful tool that Autoviz sometimes uses: the [Metadump Tool (MetadataExtractor)](03_metadump_tool__metadataextractor__.md), which helps us understand what's inside our data files.

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)