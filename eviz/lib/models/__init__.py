"""
Models package for EViz library.

This package contains generic data source implementations that can be used
across different visualization backends and data types.
"""

from .base import GenericDataSource
from .factory import DataSourceFactory
from .gridded import GriddedDataSource
from .observational import ObservationalDataSource

__all__ = [
    'GenericDataSource',
    'GriddedDataSource', 
    'ObservationalDataSource',
    'DataSourceFactory'
]