"""Crossplane Tools Package

This package provides tools for managing Crossplane installations and resources.
"""

from .tools.core import CoreOperations
from .tools.providers import ProviderManager

def register_all_tools():
    """Register all Crossplane tools."""
    # Initialize the managers which will register their tools
    CoreOperations()
    ProviderManager()

# Register all tools when the package is imported
register_all_tools()

__version__ = "0.1.0" 