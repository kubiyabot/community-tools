# Import all tools explicitly
from .kubeshark import (
    kubeshark_troubleshoot,
    kubeshark_monitor,
    kubeshark_mesh_analyzer,
    kubeshark_http_analyzer,
    kubeshark_service_mesh_analyzer,
    kubeshark_security_analyzer,
    kubeshark_performance_analyzer,
    kubeshark_api_gateway_analyzer,
)

from .service import (
    service_management_tool,
    service_describe_tool,
)

# Export all tools
__all__ = [
    # Kubeshark tools
    'kubeshark_troubleshoot',
    'kubeshark_monitor',
    'kubeshark_mesh_analyzer',
    'kubeshark_http_analyzer',
    'kubeshark_service_mesh_analyzer',
    'kubeshark_security_analyzer',
    'kubeshark_performance_analyzer',
    'kubeshark_api_gateway_analyzer',
    
    # Service tools
    'service_management_tool',
    'service_describe_tool',
]

# Register all tools
from kubiya_sdk.tools.registry import tool_registry

KUBERNETES_TOOLS = [
    # Kubeshark tools
    kubeshark_troubleshoot,
    kubeshark_monitor,
    kubeshark_mesh_analyzer,
    kubeshark_http_analyzer,
    kubeshark_service_mesh_analyzer,
    kubeshark_security_analyzer,
    kubeshark_performance_analyzer,
    kubeshark_api_gateway_analyzer,
    
    # Service tools
    service_management_tool,
    service_describe_tool,
]

# Register all tools
for tool in KUBERNETES_TOOLS:
    tool_registry.register("kubernetes", tool)
