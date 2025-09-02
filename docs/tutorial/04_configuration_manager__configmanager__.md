# Chapter 4: Configuration Manager (ConfigManager)

Welcome back, future visualization expert! In [Chapter 3: Metadump Tool (MetadataExtractor)](03_metadump_tool__metadataextractor__.md), we learned how to be a "librarian" for our data files, discovering what ingredients (variables, dimensions) are available. Before that, in [Chapter 2: Autoviz Application Core (Autoviz)](02_autoviz_application_core__autoviz__.md), we saw `Autoviz` acting as the "chef," orchestrating the entire visualization process.

But how does the chef know *exactly* what recipe to follow? Where are all the detailed instructions stored – like which variables to plot, what units to use, what colors, and where to save the pictures? This is where the **Configuration Manager (ConfigManager)** steps in!

## Overview

### What Problem Does ConfigManager Solve?

Imagine you're trying to bake a very complex cake. You have all your ingredients, and a skilled chef. But for the cake to turn out perfectly, the chef needs a detailed recipe:
*   What type of cake?
*   How much flour, sugar, eggs?
*   At what temperature to bake?
*   What kind of frosting and decorations?

In EViz, creating scientific visualizations is similar. There are many settings that control how plots look and behave:
*   Which data files to load?
*   Which specific variables (`PSFC`, `T2`) to visualize?
*   What kind of plot (map, time series, profile)?
*   Should units be converted (e.g., Kelvin to Celsius)?
*   What colors to use for the map?
*   Where should the generated images and GIFs be saved?

If these settings were scattered everywhere or hard-coded, it would be messy, error-prone, and difficult to change.

**ConfigManager solves this by acting like the "master recipe book" or "control center" for EViz.** It collects *all* these settings from special configuration files (usually YAML files) and command-line inputs, organizes them neatly, and makes sure every part of EViz has easy access to the exact instructions it needs. It ensures consistency and flexibility in your visualizations.

#### Our Use Case: Applying a Standard Visualization Recipe

Let's say you're a scientist, and you have a standard way you like to visualize your model's surface pressure, temperature, and wind. You've prepared a couple of YAML files that specify all these details. You want `Autoviz` to automatically generate these plots according to your predefined "recipe."

`ConfigManager` is the core component that loads and manages these recipes, making them available to `Autoviz` and other parts of the visualization system.

## Core Concepts

### Key Concepts: Your Visualization's Brain

ConfigManager is like the central brain or control panel for your visualization project.

*   **The "Brain" / "Control Center":** This is the core idea. `ConfigManager` is not a worker (it doesn't draw plots or load data directly). Instead, it holds all the *instructions* for the workers.
*   **YAML Configuration Files:** These are like your detailed "recipe cards." YAML (Yet Another Markup Language) is a human-friendly way to write configuration data. EViz uses YAML files to define:
    *   `app.yaml`: General application settings, like which data files to use, output directories, and global plot options.
    *   `_specs.yaml`: Specific details for each variable, like what plot types are suitable, default units, and specific plotting parameters.
    `ConfigManager` reads these files.
*   **Command-Line Inputs:** Sometimes you want to quickly change a setting without editing a YAML file (e.g., specifying an input file or output directory when running `autoviz.py`). `ConfigManager` also incorporates these inputs, often overriding settings from YAML files.
*   **Centralized Source of Truth:** Every other component in EViz (like the data loader, the plotter, the output saver) consults `ConfigManager` when it needs to know how to do something. This ensures that everyone is working with the same, consistent set of rules.
*   **Organized Settings:** Instead of one giant list of settings, `ConfigManager` organizes them into logical groups (like input settings, output settings, system settings).

## Getting Started

### How Autoviz Uses ConfigManager

You, as a user, don't typically interact directly with `ConfigManager`. Instead, you interact with `Autoviz` (as we learned in Chapter 2), and `Autoviz` then relies heavily on `ConfigManager`.

When you run `Autoviz` with your configuration files (e.g., `python autoviz.py -s gridded -c /path/to/my_configs`), here's the high-level flow:

1.  **`Autoviz` Initialization:** The `Autoviz` application starts and its first major task is to set up its "brain."
2.  **`ConfigManager` Creation:** `Autoviz` creates an instance of `ConfigManager`, telling it where to find your YAML configuration files and passing any command-line arguments.
3.  **Loading the Recipe:** `ConfigManager` then reads all the YAML files and combines them with any command-line inputs. It organizes all these settings into its internal structure.
4.  **Providing Instructions:** As `Autoviz` proceeds to load data, process it, and generate plots, it constantly asks `ConfigManager` for instructions.
    *   "Hey `ConfigManager`, what's the `output_dir`?"
    *   "Hey `ConfigManager`, for the `PSFC` variable, what `plot_type` should I use?"
    *   "Hey `ConfigManager`, should I `make_gif`?"

The `ConfigManager` will respond with the correct setting, allowing `Autoviz` and its delegated components to execute the visualization precisely as you've defined in your configuration.

## Technical Details

### Under the Hood: ConfigManager's Workflow

Let's dive a little deeper into how `ConfigManager` works internally.

#### 1. The Brain's Plan (Non-Code Walkthrough)

When `Autoviz` asks `ConfigManager` to set things up, here's a simplified step-by-step:

1.  **`Autoviz` Calls `ConfigManager`:** `Autoviz` (our conductor) initiates the `ConfigManager` (our brain), providing it with the paths to the YAML config files.
2.  **`ConfigManager` Creates `Config`:** The `ConfigManager` first creates a foundational `Config` object, which is responsible for the initial parsing.
3.  **`Config` Uses `YAMLParser`:** The `Config` object then uses a `YAMLParser` (like a meticulous librarian) to read each `app.yaml` and `_specs.yaml` file you've provided.
4.  **`YAMLParser` Merges Settings:** The `YAMLParser` reads all the different settings from the YAML files, merges them, and organizes them into an `AppData` object (for general app settings) and `spec_data` (for variable-specific settings). It also organizes map parameters and metadata.
5.  **`Config` Populates Sub-Configurations:** The `Config` object takes this parsed data and distributes it to specialized sub-configuration objects:
    *   `InputConfig`: Handles settings related to input data files and comparison modes.
    *   `OutputConfig`: Manages all output-related settings (e.g., `output_dir`, `print_format`, `make_gif`).
    *   `SystemConfig`: Deals with system-wide options (e.g., using multiprocessing).
    *   `HistoryConfig`: For tracking changes (less critical for basic understanding).
6.  **`ConfigManager` Provides Unified Access:** The main `ConfigManager` object then acts as a single point of access. When other parts of EViz need a setting, they ask `ConfigManager`. `ConfigManager` intelligently checks its internal `Config` object and its sub-configurations to find the requested setting and return it.

Here's a simple sequence diagram to visualize this flow:

```{mermaid}
sequenceDiagram
    participant AutovizCore as Autoviz (Conductor)
    participant ConfigManager as ConfigManager (Brain)
    participant Config as Config (Orchestrator)
    participant YAMLParser as YAMLParser (Librarian)
    participant InputOutputSystemConfig as Input/Output/System Configs (Specialists)

    AutovizCore->>ConfigManager: Initialize (with config file paths)
    ConfigManager->>Config: Create Config object
    Config->>YAMLParser: Parse YAML files (`app.yaml`, `_specs.yaml`)
    YAMLParser-->>Config: Return parsed `app_data`, `spec_data` etc.
    Config->>InputOutputSystemConfig: Initialize Input/Output/System Configs with `app_data`
    InputOutputSystemConfig-->>Config: Sub-configs ready
    Config-->>ConfigManager: Config object fully set up
    AutovizCore->>ConfigManager: Ask for setting (e.g., `output_dir`)
    ConfigManager->>Config: Forward request
    Config->>InputOutputSystemConfig: Look up in relevant sub-config
    InputOutputSystemConfig-->>Config: Return `output_dir`
    Config-->>ConfigManager: Return `output_dir`
    ConfigManager-->>AutovizCore: Provide `output_dir`
```

#### 2. Diving into the Code

Let's look at some simplified code snippets to understand how this is implemented.

First, the main `Config` class (`eviz/lib/config/config.py`) that brings everything together:

```python
# File: eviz/lib/config/config.py (simplified)
from dataclasses import dataclass, field
from typing import List, Dict, Any
from eviz.lib.config.yaml_parser import YAMLParser
from eviz.lib.config.app_data import AppData # Holds parsed app settings
from eviz.lib.config.input_config import InputConfig # For input-related settings
from eviz.lib.config.output_config import OutputConfig # For output-related settings
# ... (other imports for SystemConfig, HistoryConfig, etc.) ...

@dataclass
class Config:
    source_names: List[str]
    config_files: List[str]
    app_data: AppData = field(default_factory=AppData) # Where general settings will go
    spec_data: Dict[str, Any] = field(default_factory=dict) # Where variable specs will go
    # ... other fields ...

    def __post_init__(self):
        # 1. Use the YAMLParser to read and merge all YAML files
        self.yaml_parser = YAMLParser(config_files=self.config_files, source_names=self.source_names)
        self.yaml_parser.parse() # This reads the files and populates internal data

        # 2. Convert parsed data into structured objects
        self.app_data = AppData(**self.yaml_parser.app_data)
        self.spec_data = self.yaml_parser.spec_data
        # ... other data from parser ...

        # 3. Initialize specialized sub-configuration objects
        self.input_config = InputConfig(self.source_names, self.config_files)
        self.output_config = OutputConfig()
        # ... initialize system_config, history_config ...

        # 4. Pass the parsed application data to all sub-configurations
        self._assign_app_data_to_subconfigs()
        self.input_config.initialize()
        self.output_config.initialize()
        # ... initialize other sub-configs ...

    def _assign_app_data_to_subconfigs(self):
        """Assign app_data to all sub-configurations."""
        self.input_config.app_data = self.app_data
        self.output_config.app_data = self.app_data
        # ... assign to other sub-configs ...
```
**Explanation:**
*   The `Config` class takes `config_files` (your YAML paths) and `source_names` (e.g., `gridded`).
*   In `__post_init__` (which runs right after a `Config` object is created), it first uses `YAMLParser` to read all your YAML files.
*   Then, it takes the raw data parsed by `YAMLParser` and uses it to create structured objects like `AppData`.
*   Finally, it creates instances of `InputConfig`, `OutputConfig`, etc., and passes them the relevant parts of the `app_data`. Each sub-config then initializes itself using its specific section of the `app_data`.

Next, let's see a snippet from `YAMLParser` (`eviz/lib/config/yaml_parser.py`) for reading files:

```python
# File: eviz/lib/config/yaml_parser.py (simplified)
from dataclasses import dataclass, field
from typing import List, Dict, Any
import os
import eviz.lib.utils as u # Utility for loading YAML

@dataclass
class YAMLParser:
    config_files: List[str]
    source_names: List[str]
    app_data: Dict[str, Any] = field(default_factory=dict)
    spec_data: Dict[str, Any] = field(default_factory=dict)
    # ... other fields ...

    def parse(self):
        """Parse YAML files and populate app_data and spec_data."""
        # This method orchestrates the reading and merging
        self._concatenate_yaml()
        # ... other initialization ...

    def _concatenate_yaml(self) -> List[Dict[str, Any]]:
        """Read and merge multiple YAML files and their associated specs."""
        result = {} # This will store the merged 'app_data'
        for index, file_path in enumerate(self.config_files):
            # Load the main YAML file (e.g., app.yaml)
            yaml_content = u.load_yaml_simple(file_path)
            
            # Merge different sections into 'result'
            if 'inputs' in yaml_content:
                result.setdefault('inputs', []).extend(yaml_content['inputs'])
            if 'outputs' in yaml_content:
                result.setdefault('outputs', {}).update(yaml_content['outputs'])
            # ... merge other top-level sections ...

            # Check for an associated '_specs.yaml' file
            specs_file = os.path.join(os.path.dirname(file_path),
                                      f"{os.path.splitext(os.path.basename(file_path))[0]}_specs.yaml")
            if os.path.exists(specs_file):
                specs_content = u.load_yaml_simple(specs_file)
                self.spec_data.update(specs_content) # Merge specs data
            # ... handle case if specs file doesn't exist ...

        self.app_data = result # Store the merged app data
        return [] # Simplified for example
```
**Explanation:**
*   `YAMLParser`'s `_concatenate_yaml` method loops through each `config_file` path.
*   It uses a utility (`u.load_yaml_simple`) to read the YAML content into a Python dictionary.
*   It then intelligently merges different sections (`inputs`, `outputs`, etc.) into a `result` dictionary.
*   Crucially, it also looks for an associated `_specs.yaml` file (e.g., if `my_app.yaml` is provided, it looks for `my_app_specs.yaml`) and merges that into `self.spec_data`.
*   Finally, the merged `app_data` (general settings) and `spec_data` (variable-specific settings) are ready for `Config` to use.

Now, let's look at `ConfigManager` itself (`eviz/lib/config/config_manager.py`). This class is the public-facing "brain" that provides a simplified way to access all these underlying settings:

```python
# File: eviz/lib/config/config_manager.py (simplified)
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from eviz.lib.config.config import Config # The base config object
from eviz.lib.config.input_config import InputConfig
from eviz.lib.config.output_config import OutputConfig
# ... other config imports ...

@dataclass
class ConfigManager:
    # ConfigManager holds instances of the underlying config objects
    input_config: InputConfig
    output_config: OutputConfig
    # ... system_config, history_config ...
    config: Config # The central Config object

    # ... other internal fields ...

    def __post_init__(self):
        """Initialize the ConfigManager after construction."""
        # For instance, tell InputConfig about ConfigManager for callback purposes
        self.input_config.config_manager = self
        # Setup comparison logic, etc.
        self.setup_comparison()

    @property
    def output_dir(self):
        """Access to the output directory setting."""
        # This shows how ConfigManager delegates to OutputConfig
        return self.output_config.output_dir

    @property
    def make_gif(self):
        """Access to the make_gif setting."""
        return self.output_config.make_gif

    def __getattr__(self, name):
        """
        Dynamically access attributes from the underlying config objects.
        This allows you to ask ConfigManager for a setting, and it figures out
        which sub-config (or the main Config) actually holds that setting.
        """
        if name in self.__dict__:
            return self.__dict__[name]

        # Check in the central 'config' object first
        if hasattr(self.config, name):
            return getattr(self.config, name)

        # Then check in other specialized config objects
        for sub_config in [self.input_config, self.output_config, self.system_config]:
            if hasattr(sub_config, name):
                return getattr(sub_config, name)

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
```
**Explanation:**
*   `ConfigManager` is initialized with instances of `InputConfig`, `OutputConfig`, and the central `Config` object. It acts as a wrapper around them.
*   It has `@property` decorators (like `output_dir` and `make_gif`) that provide direct, easy access to frequently used settings. These properties simply "delegate" the request to the correct sub-configuration (e.g., `self.output_config.output_dir`).
*   The magical `__getattr__` method is key! If you try to access `config_manager.some_setting` and `some_setting` isn't directly defined in `ConfigManager` or `Config`, `__getattr__` will automatically search `InputConfig`, `OutputConfig`, etc., until it finds `some_setting` or raises an error. This makes `ConfigManager` incredibly flexible and user-friendly for other EViz components, as they don't need to know *exactly* which sub-configuration holds a specific setting.

## Summary

### Conclusion

In this chapter, you've learned that the **Configuration Manager (ConfigManager)** is the "brain" or "master recipe book" of EViz. It's responsible for gathering all your visualization settings from YAML files and command-line inputs, organizing them, and providing a unified, easy-to-access source of truth for all other EViz components.

By centralizing configuration, `ConfigManager` ensures that your plots are generated consistently and that modifying settings is straightforward and flexible. You now understand how `Autoviz` (the chef) uses `ConfigManager` to get all its instructions.

Next, we'll dive into the different types of data `EViz` can handle and how it identifies them, by exploring the [Model Source (GenericDataSource / GriddedDataSource / ObservationalDataSource)](05_model_source__genericdatasource___griddeddatasource___observationaldatasource__.md).

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)