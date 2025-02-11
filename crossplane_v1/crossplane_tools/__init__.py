"""Crossplane Tools Package

This package provides tools for managing Crossplane installations and resources.
"""

from .tools.core import register_core_tools
from .tools.providers import register_provider_tools

# Register all tools when the package is imported
register_core_tools()
register_provider_tools()

__version__ = "0.1.0" 