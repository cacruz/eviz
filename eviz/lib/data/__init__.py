"""
Data handling module for eviz.

This module provides tools for loading, processing, and manipulating
data from various sources.
"""

from eviz.lib.data.factory import DataSourceFactory
from eviz.lib.data.pipeline import DataPipeline
from eviz.lib.data.sources import DataSource

__all__ = ["DataSource", "DataSourceFactory", "DataPipeline"]
