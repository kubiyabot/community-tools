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
    tools = {
        # Core tools
        'install_crossplane': install_crossplane(),
        'uninstall_crossplane': uninstall_crossplane(),
        'get_status': get_status(),
        'version': version(),
        'debug_mode': debug_mode(),
        
        # Provider tools
        'provider_install': install_provider(),
        'provider_configure': configure_provider(),
        'provider_list': list_providers(),
        'provider_status': get_provider_status(),
        'provider_uninstall': uninstall_provider(),
        'provider_apply_resource': apply_provider_resource()
    }
    
    print("\n=== Registering Crossplane Tools ===")
    for name, tool in tools.items():
        try:
            tool_registry.register("crossplane", tool)
            print(f"✅ Registered: {name}")
        except Exception as e:
            print(f"❌ Failed to register {name}: {str(e)}")
    
    print(f"\nTotal tools registered: {len(tools)}")

# Register all tools when the package is imported
register_all_tools()

__version__ = "0.1.0" 