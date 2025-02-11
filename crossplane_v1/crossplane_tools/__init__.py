"""Crossplane Tools Package

This package provides tools for managing Crossplane installations and resources.
"""

from .tools.core import (
    install_crossplane,
    uninstall_crossplane,
    get_status,
    version,
    debug_mode
)

from .tools.providers import (
    install_provider,
    configure_provider,
    list_providers,
    get_provider_status,
    uninstall_provider,
    apply_provider_resource
)

from kubiya_sdk.tools.registry import tool_registry

def register_all_tools():
    """Register all Crossplane tools."""
    # Register core tools
    core_tools = [
        install_crossplane(),
        uninstall_crossplane(),
        get_status(),
        version(),
        debug_mode()
    ]
    
    # Register provider tools
    provider_tools = [
        install_provider(),
        configure_provider(),
        list_providers(),
        get_provider_status(),
        uninstall_provider(),
        apply_provider_resource()
    ]
    
    # Register all tools
    for tool in core_tools + provider_tools:
        tool_registry.register("crossplane", tool)

# Register all tools when the package is imported
register_all_tools()

__version__ = "0.1.0" 