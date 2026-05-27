=============================================================
EVIZ: An Easy to Use Earth Modeling System Visualization Tool
=============================================================

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.20417921.svg
   :target: https://doi.org/10.5281/zenodo.20417921
   :alt: DOI

`EViz` is a comprehensive Python-based visualization library designed specifically for
Earth System Modelers. It processes a wide variety of model-generated output formats
and produces high-quality diagnostic plots for data analysis and validation. EViz serves
as an essential validation tool for earth system model data, offering both command-line and
interactive visualization capabilities.

Features
--------
* Multi-format Support: Process NetCDF, HDF, Zarr, and other common Earth System Model data formats
* Flexible Visualization: Generate maps, time series, vertical profiles, box plots, and correlation analyses
* Customizable: Configure plot appearance through YAML files with extensive customization options
* Comparison Tools: Compare multiple datasets side-by-side for in-depth analysis
* Statistical Analysis: Calculate and display metrics like RMSE and R² values directly on plots
* Interactive Mode: Use the interactive web interface for exploratory data analysis
* Batch Processing: Generate multiple plots efficiently through command-line batch processing

Installation
------------
EViz can be installed using conda:

.. code-block:: bash

    conda env create -f environment.yaml
    conda activate viz
    pip install -e .

Documentation
-------------
For comprehensive documentation, tutorials, and examples, please visit our documentation site:
https://cacruz.github.io/eviz

Contributing
------------
We welcome contributions! Please see our `Contributing Guide <https://github.com/cacruz/eviz/blob/main/CONTRIBUTING.rst>`_  for details on how to submit pull requests, report issues, or request features.

Support
-------
For questions, comments, bug reports, or feature requests, please use the `issues section <https://github.com/cacruz/eviz/issues>`_ on GitHub.

Citation
--------
If you use EViz in your research, please cite it using the DOI:

.. code-block:: text

    Cruz, C. A., Raghunandan, D., & Valenti, V. EViz: Earth System Model Visualization
    Toolkit. https://doi.org/10.5281/zenodo.20417921

Code of Conduct
---------------
This project follows the `Contributor Covenant Code of Conduct <https://github.com/cacruz/eviz/blob/main/CODE_OF_CONDUCT.md>`_.
By participating, you are expected to uphold this code.

License
-------
EViz is distributed under the Apache 2.0 license. Please read the LICENSE document located in the root folder.

Acknowledgments
---------------
EViz is developed and maintained by the `Advanced Software Technology Group (ASTG) <https://astg.pages.smce.nasa.gov/website/>`_ at NASA.
