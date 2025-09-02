# Chapter 3: Metadump Tool (MetadataExtractor)

Welcome back! In [Chapter 2: Autoviz Application Core (Autoviz)](02_autoviz_application_core__autoviz__.md), we learned that Autoviz is the "chef" of EViz, taking your instructions and cooking up beautiful visualizations. But what if the chef needs to know *what ingredients are available* in your scientific data file before starting to cook? That's where the **Metadump Tool (MetadataExtractor)** comes in!

### What Problem Does Metadump Solve?

Imagine you've just received a big box of ingredients (a scientific data file, like a NetCDF file). You want to bake a cake (create visualizations), but you don't know what's inside the box! Is there flour, sugar, eggs? Are they fresh? What quantities?

Scientific data files are often like these mystery boxes. They contain lots of information – variables like temperature, pressure, wind speed, their units, what dimensions they have (time, latitude, longitude, vertical levels), and other important details (metadata). Before you can tell Autoviz *how* to plot temperature, you first need to know if "temperature" is even *in* the file, and what its specific name is (e.g., `temp_2m`, `T2`).

**Metadump solves this by acting like a diligent "librarian" or "inventory manager" for your data files.** It thoroughly scans your NetCDF files, reads their labels, understands their contents, and then creates an organized summary of everything inside. This summary is vital for Autoviz to know how to interpret and visualize the data without you manually digging through every file. Metadump can even suggest how to best plot certain variables!

#### Our Use Case: Understanding a New Data File

Let's say you're a scientist and you've received a new NetCDF file named `model_output.nc` from a simulation. You want to:
1.  **Quickly see what variables are available** inside the file (e.g., `PSFC` for surface pressure, `T2` for 2-meter temperature).
2.  **Understand the structure of these variables** (e.g., their dimensions like `time`, `lat`, `lon`, `level`).
3.  **Get a head start on preparing configuration files** so Autoviz can automatically generate plots without manual setup.

Metadump is designed to make this initial data exploration and setup incredibly simple.

### Key Concepts: Your Data's Librarian

Metadump's job is to make sense of your data files. Here are its core ideas:

*   **The "Librarian" (Metadump):** It's a tool that automatically inspects your scientific data files. Instead of you opening a file and manually looking through its contents, Metadump does it for you.
*   **Scanning NetCDF Files:** NetCDF is a common format for storing scientific data. Metadump is specially designed to read and understand the structure of these files.
*   **Structured Metadata (JSON):** "Metadata" is simply "data about data." Metadump extracts this information (variable names, units, dimensions, descriptions) and organizes it into a clear, easy-to-read format like JSON (JavaScript Object Notation), which is excellent for computers and people to understand.
*   **Configuration Files (YAML):** Besides just listing what's in the file, Metadump can also *suggest* how to plot things. It can generate basic configuration files (in YAML format) that tell Autoviz, "Hey, for `T2`, you can probably make an `xy` (map) plot and an `xt` (time-series) plot!" This is like the librarian giving you a suggested "reading list" based on the book's content.
*   **Crucial for Autoviz:** Autoviz needs these "ingredient lists" and "suggested recipes" from Metadump. Without them, Autoviz wouldn't know what to plot or how to set up the plots correctly.

### How to Use Metadump

You can run Metadump directly from your computer's terminal (command prompt). This is also how `sViz` or Autoviz would call Metadump internally to get information about a new dataset.

#### 1. Running Metadump from the Command Line

To achieve our use case (understand a new NetCDF file and get its metadata), you would run a command like this:

```bash
python metadump.py /path/to/model_output.nc --json my_data_metadata.json
```

**What happens?**
*   `python metadump.py`: This tells your computer to run the `metadump.py` script.
*   `/path/to/model_output.nc`: This is the path to your scientific data file that you want to inspect.
*   `--json my_data_metadata.json`: This is an "argument" telling Metadump to create a JSON file named `my_data_metadata.json` containing all the extracted metadata.

After running this command, Metadump will scan your file, and you will find a new file `my_data_metadata.json` in your current directory.

Here's a simplified look at the `main` function in `metadump.py` that handles this:

```python
# File: metadump.py
import logging
import sys
import argparse
from eviz.lib.metadump.metadump import MetadumpConfig, MetadataExtractor # Our Metadump tools!

def main():
    """Main entry point for the metadump tool."""
    logging.basicConfig(level=logging.INFO) # Set up basic logging

    args = parse_command_line() # 1. Get your instructions (like file path, --json)

    if len(args.filepaths) > 2:
        logger.error("Error: Only one or two file paths are allowed.")
        sys.exit(1)

    try:
        # 2. Package your instructions into a MetadumpConfig object
        config = MetadumpConfig(
            filepath_1=args.filepaths[0], # The main data file
            filepath_2=args.filepaths[1] if len(args.filepaths) == 2 else None,
            json_output=args.json, # Where to save the JSON metadata
            specs_output=args.specs, # Where to save YAML specs (if requested)
            app_output=args.app,     # Where to save YAML app config (if requested)
            ignore_vars=args.ignore, # Variables to skip
            vars=args.vars,          # Specific variables to include
            source=args.source       # Type of data source (e.g., 'gridded')
        )
        
        extractor = MetadataExtractor(config) # 3. Create our 'librarian' (MetadataExtractor)
        extractor.process() # 4. Tell the librarian to start scanning and generating files!
        
    except Exception as e:
        logger.error(f"Error processing metadata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Explanation:**
*   `parse_command_line()`: This function reads the instructions you typed (like `/path/to/model_output.nc` and `--json`).
*   `config = MetadumpConfig(...)`: Your instructions are gathered and put into a `MetadumpConfig` object, which is like a note for the librarian detailing what to do.
*   `extractor = MetadataExtractor(config)`: This creates a new "MetadataExtractor" object, which is our diligent librarian ready to work. It takes the `config` note.
*   `extractor.process()`: This is the command that tells the librarian to start its work – to open the file, scan it, extract information, and save the requested outputs.

#### 2. Understanding the Output (JSON Example)

After Metadump runs, `my_data_metadata.json` will contain a structured summary of your `model_output.nc` file. It will look something like this (simplified):

```json
{
    "global_attributes": {
        "title": "My Earth System Model Output",
        "institution": "Some University",
        "history": "Created by Model X",
        "units": "standard"
    },
    "variables": {
        "PSFC": {
            "dimensions": ["time", "lat", "lon"],
            "data_type": "float32",
            "attributes": {
                "long_name": "Surface Pressure",
                "units": "Pa"
            }
        },
        "T2": {
            "dimensions": ["time", "lat", "lon"],
            "data_type": "float32",
            "attributes": {
                "long_name": "2-meter Temperature",
                "units": "K"
            }
        },
        "time": {
            "dimensions": ["time"],
            "data_type": "datetime64[ns]",
            "attributes": {
                "long_name": "Time",
                "axis": "T"
            }
        },
        "lat": {
            "dimensions": ["lat"],
            "data_type": "float32",
            "attributes": {
                "long_name": "Latitude",
                "units": "degrees_north"
            }
        }
        // ... many more variables and their details ...
    }
}
```

This JSON file clearly shows you:
*   **`global_attributes`**: General information about the entire dataset.
*   **`variables`**: A list of all variables in the file.
    *   For each variable (like `PSFC` or `T2`), you see its `dimensions` (e.g., `time`, `lat`, `lon`), `data_type` (e.g., `float32`), and `attributes` (like `long_name` and `units`).

This is much easier to read and use than manually inspecting a complex NetCDF file!

### Under the Hood: Metadump's Workflow

Let's take a quick peek at how our "librarian" works internally when you ask it to process a file.

#### 1. The Librarian's Plan (Non-Code Walkthrough)

When you run Metadump, here's a simplified step-by-step of what happens:

1.  **Receive Instructions:** Metadump gets the file path and what kind of output you want (e.g., JSON metadata).
2.  **Open the Data File:** It uses a powerful library called `xarray` to open your NetCDF file. This is like the librarian carefully opening the book.
3.  **Scan Contents:** Metadump then goes through the opened file, looking at all the variables, their dimensions, and any associated descriptions (attributes). It also identifies key coordinates like `time`, `latitude`, `longitude`.
4.  **Organize Information:** It collects all this scattered information and puts it into a neat, structured format (like the JSON example above).
5.  **Suggest Plot Configurations (Optional):** If you didn't ask for JSON but for YAML config files, Metadump tries to guess what kind of plots make sense for each variable (e.g., a map plot for a variable with `lat` and `lon` dimensions).
6.  **Save the Output:** Finally, it writes this organized information to the specified output file(s) (e.g., `my_data_metadata.json`).

Here's a simple sequence diagram to visualize this flow:

```{mermaid}
sequenceDiagram
    participant User
    participant MetadumpCLI as metadump.py (CLI)
    participant MetadataExtractor as MetadataExtractor (Librarian)
    participant XarrayLib as Xarray Library (File Reader)

    User->>MetadumpCLI: Run `python metadump.py my_data.nc --json`
    MetadumpCLI->>MetadataExtractor: Initialize with file path and settings
    MetadataExtractor->>XarrayLib: Open `my_data.nc` (using xarray.open_dataset)
    XarrayLib-->>MetadataExtractor: Returns dataset object (data and its info)
    MetadataExtractor->>MetadataExtractor: Scans variables, dimensions, attributes
    MetadataExtractor->>MetadataExtractor: Organizes info into JSON structure
    MetadataExtractor-->>MetadumpCLI: Saves `my_data_metadata.json`
    MetadumpCLI-->>User: Process complete!
```

#### 2. Diving into the Code

The `MetadataExtractor` class in `eviz/lib/metadump/metadump.py` contains the core logic for our "librarian."

First, let's see how Metadump opens your NetCDF file:

```python
# File: eviz/lib/metadump/metadump.py (excerpt from MetadataExtractor class)
import xarray as xr # The powerful library for NetCDF files

@dataclass
class MetadataExtractor:
    # ... (other attributes and init) ...

    def _open_dataset(self, filepath: Optional[str]) -> Optional[xr.Dataset]:
        """Open an xarray dataset from a file."""
        if not filepath:
            return None
        try:
            return xr.open_dataset(filepath, decode_cf=True) # This is the magic!
        except Exception as e:
            logger.error(f"Failed to open dataset {filepath}: {e}")
            raise RuntimeError(f"Could not open dataset: {e}")
```

**Explanation:**
*   `import xarray as xr`: This line brings in the `xarray` library, which is a fantastic tool for working with labeled multi-dimensional arrays (like those in NetCDF files).
*   `xr.open_dataset(filepath, decode_cf=True)`: This is the key function! It tells `xarray` to open your `filepath` (e.g., `model_output.nc`) and read all its data and metadata. `decode_cf=True` helps `xarray` understand common scientific data conventions. This function returns an `xr.Dataset` object, which is like an organized container for all your data.

Next, let's look at how Metadump generates the JSON metadata:

```python
# File: eviz/lib/metadump/metadump.py (excerpt from MetadataExtractor class)
import json # For working with JSON files

@dataclass
class MetadataExtractor:
    # ... (attributes and other methods) ...

    def _generate_json_metadata(self) -> None:
        """Generate and save JSON metadata for the dataset."""
        metadata = {
            "global_attributes": self._get_json_compatible_attrs(self.dataset.attrs),
            "variables": {}
        }

        # Loop through each variable found in the dataset
        for var_name, da in self.dataset.data_vars.items():
            if self._should_include_var(var_name): # Check if this variable should be included
                metadata["variables"][var_name] = {
                    "dimensions": list(da.dims),      # Get its dimensions (e.g., ['time', 'lat', 'lon'])
                    "data_type": str(da.dtype),       # Get its data type (e.g., 'float32')
                    "attributes": self._get_json_compatible_attrs(da.attrs) # Get its descriptions
                }

        # Save the collected metadata to a JSON file
        with open(self.config.json_output or "ds_metadata.json", "w") as json_file:
            json.dump(metadata, json_file, indent=4) # 'indent=4' makes it pretty and readable
        logger.debug(f"Saved metadata to {self.config.json_output or 'ds_metadata.json'}")
```

**Explanation:**
*   `metadata = {...}`: An empty Python dictionary is created to hold all the metadata.
*   `self.dataset.attrs`: This accesses the "global attributes" of the entire NetCDF file (like `title` or `institution`).
*   `for var_name, da in self.dataset.data_vars.items():`: This loop goes through every single "data variable" (like `PSFC`, `T2`) found in your opened dataset.
    *   `da.dims`: Gives you the dimensions of that specific variable.
    *   `da.dtype`: Tells you the data type (e.g., integer, float).
    *   `da.attrs`: Gives you the attributes (descriptions) of that specific variable.
*   `json.dump(metadata, json_file, indent=4)`: After collecting all the information, this line writes the entire `metadata` dictionary into the JSON file, making it easy to read with 4 spaces for indentation.

Metadump also has methods like `_generate_specs_dict()` and `_generate_app_dict()` (not shown in detail here) that perform similar loops and logic to create the YAML configuration files for plot specifications and application settings, respectively. This is where it intelligently suggests plot types (like `xyplot`, `xtplot`, `yzplot`) based on the variable's dimensions.

### Conclusion

In this chapter, you've learned that the **Metadump Tool (MetadataExtractor)** is the "librarian" of EViz. It's essential for understanding the contents of your scientific data files (especially NetCDF). By automatically scanning these files, Metadump generates structured metadata (JSON) and suggested configuration files (YAML), which are crucial for [Autoviz Application Core (Autoviz)](02_autoviz_application_core__autoviz__.md) to correctly interpret and visualize your data without manual setup.

You now understand how Metadump acts as the initial explorer, preparing the groundwork for the visualization process. In the next chapter, we'll dive into the [Configuration Manager (ConfigManager)](04_configuration_manager__configmanager__.md), which is responsible for reading, organizing, and providing these very configuration files that Metadump helps to create.

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)