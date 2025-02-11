"""Crossplane Tools Package

This package provides tools for managing Crossplane installations and resources.
"""

from .tools.core import register_core_tools
from .tools.providers import register_provider_tools
from kubiya_sdk.tools.registry import tool_registry

def register_all_tools():
    """Register all Crossplane tools with proper error handling."""
    print("\n=== Starting Crossplane Tools Registration ===")
    
    try:
        print("\nRegistering core tools...")
        register_core_tools()
    except Exception as e:
        print(f"Error registering core tools: {str(e)}")

    try:
        print("\nRegistering provider tools...")
        register_provider_tools()
    except Exception as e:
        print(f"Error registering provider tools: {str(e)}")

    # Print registered tools summary
    print("\n=== Registered Tools Summary ===")
    registered_tools = tool_registry.get_tools("crossplane")
    if registered_tools:
        print("\nRegistered tools:")
        for tool in registered_tools:
            print(f"- {tool.name}: {tool.description}")
    else:
        print("No tools registered!")
    
    print("\n=== Crossplane Tools Registration Complete ===\n")

# Register all tools when the package is imported
register_all_tools()

__version__ = "0.1.0" 