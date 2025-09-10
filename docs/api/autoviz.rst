autoviz module
==============

The main command-line interface for EViz visualization.

**autoviz** is the primary entry point for generating visualizations from earth system model output. 
It provides a command-line interface that can process various data formats and generate plots using 
different backends.

Usage
-----

Basic usage::

    python autoviz.py -s gridded -c config/

Compare datasets::

    python autoviz.py -s wrf --compare -c config/

Process specific file::

    python autoviz.py --file data.nc --vars temp,precip

Module Documentation
--------------------

.. automodule:: autoviz
   :members:
   :undoc-members:
   :show-inheritance: