"""
Data source factory for creating appropriate data source instances.

This module provides a factory pattern for instantiating the correct
data source type based on the source name and configuration.
"""

import logging
from typing import Dict, Optional, Type

from eviz.lib.config.config_manager import ConfigManager
from eviz.lib.models.base import GenericDataSource
from eviz.lib.models.categorical import CategoricalDataSource
from eviz.lib.models.gridded import GriddedDataSource
from eviz.lib.models.observational import ObservationalDataSource


class DataSourceFactory:
    """
    Factory class for creating data source instances.

    This factory handles the registration and instantiation of different
    data source types based on source names.
    """

    _registry: Dict[str, Type[GenericDataSource]] = {}
    _logger = logging.getLogger(__name__)

    @classmethod
    def register(
        cls, source_name: str, data_source_class: Type[GenericDataSource]
    ) -> None:
        """
        Register a data source class with a source name.

        Parameters
        ----------
            source_name
                Name to associate with this data source
            data_source_class
                Class to instantiate for this source name
        """
        cls._registry[source_name] = data_source_class
        cls._logger.debug(
            f"Registered data source '{source_name}' -> {data_source_class.__name__}"
        )

    @classmethod
    def create(
        cls, source_name: str, config_manager: ConfigManager
    ) -> Optional[GenericDataSource]:
        """
        Create a data source instance for the given source name.

        Parameters
        ----------
            source_name
                Name of the data source to create
            config_manager
                Configuration manager instance

        Returns
        -------
            Data source instance or None if not found
        """
        if source_name not in cls._registry:
            cls._logger.warning(f"No data source registered for '{source_name}'")
            return None

        data_source_class = cls._registry[source_name]
        cls._logger.debug(
            f"Creating {data_source_class.__name__} for source '{source_name}'"
        )

        return data_source_class(config_manager=config_manager)

    @classmethod
    def get_registered_sources(cls) -> list[str]:
        """
        Get list of all registered source names.

        Returns
        -------
            List of registered source names
        """
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, source_name: str) -> bool:
        """
        Check if a source name is registered.

        Parameters
        ----------
            source_name
                Name to check

        Returns
        -------
            True if registered, False otherwise
        """
        return source_name in cls._registry

    @staticmethod
    def create_root_instance(config_manager: ConfigManager):
        """
        Legacy interface compatibility method.

        This method provides compatibility with the old factory interface
        where factories were instantiated and then called to create instances.

        Parameters
        ----------
            config_manager
                Configuration manager instance

        Returns
        -------
            Legacy GenericSource instance for backward compatibility
        """
        # Import here to avoid circular imports
        from eviz.models.source_base import GenericSource

        # Return the legacy GenericSource which has all the plot methods
        return GenericSource(config_manager=config_manager)


# Register standard data sources
DataSourceFactory.register("gridded", GriddedDataSource)
DataSourceFactory.register("categorical", CategoricalDataSource)
DataSourceFactory.register("obs", ObservationalDataSource)
DataSourceFactory.register("satellite", ObservationalDataSource)
DataSourceFactory.register("inventory", ObservationalDataSource)

# ESM models can use gridded data source as base
DataSourceFactory.register("wrf", GriddedDataSource)
DataSourceFactory.register("lis", GriddedDataSource)
DataSourceFactory.register("geos", GriddedDataSource)
DataSourceFactory.register("nuwrf", GriddedDataSource)
from eviz.models.esm.crest import Crest

DataSourceFactory.register("crest", Crest)
