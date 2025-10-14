"""
LEGACY FILE - Redirects to eviz.lib.models.observational

This file exists for backward compatibility only.
New code should import from: eviz.lib.models.observational
"""

import warnings

from eviz.lib.models.observational import ObservationalDataSource

# Issue deprecation warning
warnings.warn(
    "eviz.models.obs_source is deprecated. Use eviz.lib.models.observational instead.",
    DeprecationWarning,
    stacklevel=2
)

# Compatibility alias
ObsSource = ObservationalDataSource

__all__ = ['ObsSource']