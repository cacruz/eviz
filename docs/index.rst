EViz Documentation
==================

**EViz** is a comprehensive Python-based visualization library designed for Earth System Modelers. It processes various model-generated output formats (NetCDF, HDF, Zarr, GRIB) and produces high-quality diagnostic plots for data analysis and validation.

.. note::
   EViz supports both command-line batch processing and interactive web-based visualization through its Streamlit interface.

Key Features
------------

* **Multi-format Support**: NetCDF, HDF5, Zarr, GRIB, CSV, and OPeNDAP URLs
* **Earth System Models**: WRF, LIS, GEOS, CREST, and generic formats  
* **Observational Data**: OMI, MOPITT, Landsat, AirNow
* **Multiple Backends**: matplotlib and hvplot plotting backends
* **Configuration-driven**: YAML-based configuration system
* **Web Interface**: Interactive Streamlit application (sviz)

Quick Links
-----------

* :doc:`Getting Started <usage/quickstart>` - Installation instructions and basic usage examples
* :doc:`Usage Guide <usage/autoviz.use>` - Detailed usage examples and supported models  
* :doc:`API Reference <api/eviz.api>` - Complete API documentation

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   usage/quickstart
   usage/autoviz.use

.. toctree::
   :maxdepth: 2
   :caption: Examples:
   
   examples/index

.. toctree::
   :maxdepth: 2
   :caption: Architecture Guide:
   
   tutorial/index

.. toctree::
   :maxdepth: 3
   :caption: API Reference:

   api/eviz.api

Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
