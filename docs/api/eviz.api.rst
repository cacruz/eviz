EViz API Reference
==================

EViz is a comprehensive Python-based visualization library originally designed for Earth System Models developed at NASA.
It addresses the common challenge faced by users, developers, and maintainers of earth system models who need to 
visualize output from modeling systems that produce data in various formats and can be quite voluminous.

Unlike existing visualization packages that are often model-specific or OS-dependent, EViz provides a model-agnostic, 
OS-independent approach to Earth system model output visualization, handling the complexity of different file formats 
transparently.

Infrastructure
**************

The entire EViz infrastructure is built upon two packages: ``lib`` and ``models``.

``lib`` is a high-level OO Python package which aims to provide a framework for **EViz**.

The aim of ``lib`` is to define and provide classes that are used to construct visualizable figure objects to be either
plotted or interactively visualized. In the case of ``autoviz.py``, the manipulated objects are ``Matplotlib`` figures and axes.

One unifying aspect of the package is that all visualizable objects are ultimately transformed into ``Xarray`` objects
which provide a unified representation of data and metadata. A key design feature is the use of YAML-based 
configuration files to specify the map output. This approach avoids having the user write any code. Instead,
the YAML files provide directives to drive the map generation. 

The ``models`` package contains the user defined modules for all the supported Earth system science models. These
modules contain code implementations to visualize a particular output definition.

The current implementation has been developed in Python 3 and tested on Mac and Linux operating systems. The required
environment can be found in the environment.yaml file.

Supported Data Formats
**********************

EViz supports multiple data formats commonly used in Earth system modeling:

- **NetCDF** - Primary format, most common for Earth system model output
- **GRIB** - Meteorological data format
- **HDF5** - Hierarchical data format
- **Zarr** - Cloud-optimized format
- **CSV** - Text-based tabular data

EViz also supports remote data access via OPeNDAP URLs. The system automatically detects data format based on file 
extension, defaulting to NetCDF4 when no extension is provided.

Core API Documentation
**********************

.. toctree::
   :maxdepth: 2

   eviz

Main Entry Points
*****************

.. toctree::
   :maxdepth: 2

   autoviz
   metadump

Quick API Reference
*******************

The EViz library provides a comprehensive set of modules for Earth system data visualization. 
Here are the key components organized by functionality:

**Core Classes:**
  - :doc:`eviz.lib.autoviz.base` - Main Autoviz application class
  - :doc:`eviz.lib.config.config_manager` - Configuration management
  - :doc:`eviz.lib.data.pipeline.pipeline` - Data processing pipeline
  - :doc:`eviz.lib.autoviz.plotting.plot_manager` - Plot management

**Configuration System:**
  - :doc:`eviz.lib.config.config` - Main configuration class
  - :doc:`eviz.lib.config.input_config` - Input configuration
  - :doc:`eviz.lib.config.output_config` - Output configuration
  - :doc:`eviz.lib.config.system_config` - System configuration

**Data Processing:**
  - :doc:`eviz.lib.data.pipeline.reader` - Data readers
  - :doc:`eviz.lib.data.pipeline.processor` - Data processors
  - :doc:`eviz.lib.data.pipeline.transformer` - Data transformers
  - :doc:`eviz.lib.data.pipeline.integrator` - Data integrators

**Plotting Backends:**
  - :doc:`eviz.lib.autoviz.plotting.backends.matplotlib` - Matplotlib backend
  - :doc:`eviz.lib.autoviz.plotting.backends.hvplot` - HvPlot backend