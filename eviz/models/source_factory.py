"""
LEGACY FILE - Partially redirects to eviz.lib.models.factory

This file maintains model-specific factories while redirecting generic ones.
Generic data sources should use: eviz.lib.models.factory.DataSourceFactory
"""

import warnings
from dataclasses import dataclass
from eviz.lib.config.config_manager import ConfigManager

# Import new architecture for base
from eviz.lib.models.factory import DataSourceFactory

# Model-specific imports remain here
from eviz.models.esm.crest import Crest
from eviz.models.esm.grib import Grib
from eviz.models.esm.geos import Geos
from eviz.models.esm.lis import Lis
from eviz.models.esm.wrf import Wrf
from eviz.models.obs.inventory.airnow import Airnow
from eviz.models.obs.inventory.ghg import Ghg
from eviz.models.obs.inventory.fluxnet import Fluxnet
from eviz.models.obs.satellite.landsat import Landsat
from eviz.models.obs.satellite.mopitt import Mopitt
from eviz.models.obs.satellite.omi import Omi

# Import legacy sources for compatibility
from eviz.models.obs_source import ObsSource
from eviz.models.gridded_source import GriddedSource
from eviz.models.source_base import GenericSource

# Issue deprecation warning for generic factories
warnings.warn(
    "Generic factories in eviz.models.source_factory are deprecated. "
    "Use eviz.lib.models.factory.DataSourceFactory for new data sources.",
    DeprecationWarning,
    stacklevel=2
)


@dataclass
class BaseSourceFactory:
    """
    Abstract base factory - should not be instantiated directly.
    """
    def create_root_instance(self, config_manager: ConfigManager):
        raise NotImplementedError("BaseSourceFactory is abstract and cannot be instantiated")


@dataclass
class GriddedSourceFactory(BaseSourceFactory):
    """
    Factory for creating GriddedSource model instances.
    """
    def create_root_instance(self, config_manager: ConfigManager):
        return GenericSource(config_manager)


@dataclass
class ObsSourceFactory(BaseSourceFactory):
    """
    Factory for creating ObsSource model instances.
    """
    def create_root_instance(self, config_manager: ConfigManager):
        return ObsSource(config_manager)


@dataclass
class GribFactory(BaseSourceFactory):
    """
    Factory for creating GriddedSource model instances for GRIB data.
    
    Used for GRIB format weather and climate data from sources like ERA5, GFS, etc.
    """
    def create_root_instance(self, config_manager: ConfigManager):
        return Grib(config_manager)


@dataclass
class GeosFactory(BaseSourceFactory):
    """
    Factory for creating Geos model instances for GEOS data processing.
    """
    def create_root_instance(self, config_manager: ConfigManager):
        return Geos(config_manager)


@dataclass
class WrfFactory(BaseSourceFactory):
    """
    Factory for creating Wrf model instances for Weather Research and Forecasting data.
    
    Handles regional model data that requires special treatment.
    """
    def create_root_instance(self, config_manager: ConfigManager):
        return Wrf(config_manager)


@dataclass
class LisFactory(BaseSourceFactory):
    """
    Factory for creating Lis model instances for Land Information System data.
    
    Handles regional model data that requires special treatment.
    """
    def create_root_instance(self, config_manager: ConfigManager):
        return Lis(config_manager)


@dataclass
class GhgFactory(BaseSourceFactory):
    """
    Factory for creating Ghg model instances
    """
    def create_root_instance(self, config_manager: ConfigManager):
        return Ghg(config_manager)


@dataclass
class AirnowFactory(BaseSourceFactory):
    """
    Factory for creating Airnow model instances for processing AirNow CSV data.
    """
    def create_root_instance(self, config_manager: ConfigManager):
        return Airnow(config_manager)


@dataclass
class OmiFactory(BaseSourceFactory):
    """
    Factory for creating Omi model instances for processing OMI HDF5 satellite data.
    """
    def create_root_instance(self, config_manager: ConfigManager):
        return Omi(config_manager)


@dataclass
class CrestFactory(BaseSourceFactory):
    """
    Factory for creating Crest model instances for processing CREST-generated data.
    """
    def create_root_instance(self, config_manager: ConfigManager):
        return Crest(config_manager)


class MopittFactory:
    def create_root_instance(self, config_manager):
        # This should be abstract and raise TypeError
        raise TypeError("Cannot instantiate abstract factory")

class LandsatFactory:
    def create_root_instance(self, config_manager):
        # This should be abstract and raise TypeError
        raise TypeError("Cannot instantiate abstract factory")

class FluxnetFactory:
    def create_root_instance(self, config_manager):
        # This should be abstract and raise TypeError
        raise TypeError("Cannot instantiate abstract factory")


