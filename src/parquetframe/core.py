"""
Backward compatibility shim for parquetframe.core module.

This module maintains compatibility with existing code that imports from
parquetframe.core while the Phase 2 multi-engine framework is developed.

The new multi-engine components are available in the 'core' subpackage.
"""

# Maintain backward compatibility by re-exporting from core_legacy
from .core_legacy import *  # noqa: F401, F403

# New Phase 2 components are available through parquetframe.core_v2
# or by importing directly from parquetframe.core.* submodules
