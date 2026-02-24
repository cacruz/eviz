"""
LEGACY FILE - Redirects to eviz.lib.models.gridded

This file exists for backward compatibility only.
New code should import from: eviz.lib.models.gridded
"""

import warnings

from eviz.lib.models.gridded import GriddedDataSource

# Issue deprecation warning
warnings.warn(
    "eviz.models.gridded_source is deprecated. Use eviz.lib.models.gridded instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Compatibility alias
GriddedSource = GriddedDataSource

__all__ = ["GriddedSource"]
