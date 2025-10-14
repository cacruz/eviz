"""
LEGACY FILE - Redirects to eviz.lib.models.base

This file exists for backward compatibility only.
New code should import from: eviz.lib.models.base
"""

import warnings

from eviz.lib.models.base import GenericDataSource

# Issue deprecation warning
warnings.warn(
    "eviz.models.base is deprecated. Use eviz.lib.models.base instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Compatibility alias
BaseSource = GenericDataSource

__all__ = ["BaseSource"]
