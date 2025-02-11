"""Crossplane Tools Package

This package provides tools for managing Crossplane installations and resources.
"""

from .tools.core import register_core_tools
from .tools.providers import register_provider_tools

def register_all_tools():
    """Register all Crossplane tools with proper error handling."""
    try:
        print("Registering core tools...")
        register_core_tools()
    except Exception as e:
        print(f"Error registering core tools: {str(e)}")

    try:
        print("Registering provider tools...")
        register_provider_tools()
    except Exception as e:
        print(f"Error registering provider tools: {str(e)}")

# Register all tools when the package is imported
register_all_tools()

__version__ = "0.1.0" 