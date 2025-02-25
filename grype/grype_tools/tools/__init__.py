from kubiya_sdk.tools.registry import tool_registry
from .scan import create_scan_image_tool, create_scan_directory_tool, create_scan_sbom_tool

# Create tool instances
scan_image_tool = create_scan_image_tool()
scan_directory_tool = create_scan_directory_tool()
scan_sbom_tool = create_scan_sbom_tool()

# Register tools with the registry
tool_registry.register("grype", scan_image_tool)
tool_registry.register("grype", scan_directory_tool)
tool_registry.register("grype", scan_sbom_tool)

# Export tools for direct imports
__all__ = [
    'scan_image_tool',
    'scan_directory_tool',
    'scan_sbom_tool'
]
