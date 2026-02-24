import logging
from dataclasses import dataclass, field
from typing import Dict, List, Set, Type

from eviz.lib.data.sources import DataSource


@dataclass
class DataSourceRegistry:
    """Registry for data source types.

    This class maintains a mapping between file extensions and data source classes.
    """

    _registry: Dict[str, Type] = field(default_factory=dict, init=False)

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

    def __post_init__(self):
        """Post-initialization setup."""
        self.logger.debug("Start init")

    def register(
        self, extensions: List[str], data_source_class: Type[DataSource]
    ) -> None:
        """Register a data source class for the specified file extensions.

        Parameters
        ----------
            extensions
                List of file extensions (without the dot)
            data_source_class
                The data source class to register
        """
        for ext in extensions:
            ext = ext.lower()
            if ext.startswith("."):
                ext = ext[1:]
            self._registry[ext] = data_source_class

    def get_data_source_class(self, file_extension: str) -> Type[DataSource]:
        """Get the data source class for the specified file extension.

        Parameters
        ----------
            file_extension
                The file extension (with or without the dot)

        Returns
        -------
            The data source class for the specified file extension
        Raises
        ------
            ValueError
                If no data source class is registered for the specified file extension
        """
        ext = file_extension.lower()
        if ext.startswith("."):
            ext = ext[1:]

        if ext not in self._registry:
            raise ValueError(
                f"No data source registered for file extension: {file_extension}"
            )

        return self._registry[ext]

    def get_supported_extensions(self) -> Set[str]:
        """Get the set of supported file extensions.

        Returns
        -------
            Set of supported file extensions
        """
        return set(self._registry.keys())

    def is_supported(self, file_extension: str) -> bool:
        """Check if the specified file extension is supported.

        Parameters
        ----------
            file_extension
                The file extension (with or without the dot)

        Returns
        -------
            True if the file extension is supported, False otherwise
        """
        ext = file_extension.lower()
        if ext.startswith("."):
            ext = ext[1:]

        return ext in self._registry
