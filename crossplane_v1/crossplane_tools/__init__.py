# Import all tools and ensure registration
from .tools import (
    CoreOperations,
    ProviderManager,
    CompositionManager,
    ClaimManager,
    PackageManager,
    tool_registry
)

def initialize_tools():
    """Initialize and register all Crossplane tools."""
    # Initialize tool instances
    core_ops = CoreOperations()
    provider_mgr = ProviderManager()
    composition_mgr = CompositionManager()
    claim_mgr = ClaimManager()
    package_mgr = PackageManager()

    # Register core operation tools
    tool_registry.register("crossplane", core_ops)
    tool_registry.register("crossplane", core_ops.install_crossplane())
    tool_registry.register("crossplane", core_ops.uninstall_crossplane())
    tool_registry.register("crossplane", core_ops.get_status())
    tool_registry.register("crossplane", core_ops.version())
    tool_registry.register("crossplane", core_ops.debug_mode())

    # Register provider management tools
    tool_registry.register("crossplane", provider_mgr)
    tool_registry.register("crossplane", provider_mgr.install_provider())
    tool_registry.register("crossplane", provider_mgr.configure_provider())
    tool_registry.register("crossplane", provider_mgr.list_providers())
    tool_registry.register("crossplane", provider_mgr.get_provider_status())
    tool_registry.register("crossplane", provider_mgr.uninstall_provider())

    # Register composition management tools
    tool_registry.register("crossplane", composition_mgr)
    tool_registry.register("crossplane", composition_mgr.apply_composition())
    tool_registry.register("crossplane", composition_mgr.apply_xrd())
    tool_registry.register("crossplane", composition_mgr.list_compositions())

    # Register claim management tools
    tool_registry.register("crossplane", claim_mgr)
    tool_registry.register("crossplane", claim_mgr.apply_claim())
    tool_registry.register("crossplane", claim_mgr.list_claims())

    # Register package management tools
    tool_registry.register("crossplane", package_mgr)
    tool_registry.register("crossplane", package_mgr.install_package())
    tool_registry.register("crossplane", package_mgr.list_packages())
    tool_registry.register("crossplane", package_mgr.get_package_status())

# Initialize tools when the package is imported
initialize_tools() 