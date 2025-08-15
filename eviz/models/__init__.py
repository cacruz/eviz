"""Model-specific implementations for EViz data processing.

This package contains the LEGACY model architecture. New code should use eviz.lib.models.

MIGRATION NOTICE:
================
This package is being migrated to eviz.lib.models for better separation of concerns.

New imports (preferred):
    from eviz.lib.models import GriddedDataSource, DataSourceFactory
    
Legacy imports (compatibility - will redirect):
    from eviz.models import GriddedSource, SourceFactory  # -> eviz.lib.models
"""

# Legacy compatibility imports - redirect to new architecture
from eviz.lib.models.base import GenericDataSource as BaseSource
from eviz.lib.models.gridded import GriddedDataSource as GriddedSource  
from eviz.lib.models.observational import ObservationalDataSource as ObsSource
from eviz.lib.models.factory import DataSourceFactory as SourceFactory

# Legacy factory aliases
from eviz.lib.models.factory import DataSourceFactory as BaseSourceFactory
from eviz.lib.models.factory import DataSourceFactory as GriddedSourceFactory
from eviz.lib.models.factory import DataSourceFactory as ObsSourceFactory

# Model-specific factories still in this package
from .source_factory import (
    GribFactory,
    GeosFactory,
    WrfFactory,
    LisFactory,
    AirnowFactory,
    OmiFactory,
    CrestFactory,
    GhgFactory
)

__all__ = [
    'BaseSource',           # -> eviz.lib.models.base.GenericDataSource
    'GriddedSource',        # -> eviz.lib.models.gridded.GriddedDataSource
    'ObsSource',            # -> eviz.lib.models.observational.ObservationalDataSource
    'SourceFactory',        # -> eviz.lib.models.factory.DataSourceFactory
    'BaseSourceFactory',    # -> eviz.lib.models.factory.DataSourceFactory
    'GriddedSourceFactory', # -> eviz.lib.models.factory.DataSourceFactory
    'ObsSourceFactory',     # -> eviz.lib.models.factory.DataSourceFactory
    # Model-specific factories remain here
    'GribFactory',
    'GeosFactory', 
    'WrfFactory',
    'LisFactory',
    'AirnowFactory',
    'OmiFactory',
    'CrestFactory',
    'GhgFactory'
]