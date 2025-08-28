metadump module
===============

A utility tool for extracting and displaying metadata from various data file formats.

**metadump** is a command-line tool that can inspect and display metadata from NetCDF, HDF5, 
and other scientific data formats supported by EViz.

Usage
-----

Extract metadata from a file::

    python metadump.py data.nc

Show detailed variable information::

    python metadump.py --verbose data.nc

Export metadata to JSON::

    python metadump.py --format json data.nc > metadata.json

Module Documentation
--------------------

.. automodule:: metadump
   :members:
   :undoc-members:
   :show-inheritance: