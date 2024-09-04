from kubiya_sdk.tools.registry import tool_registry
from .tools.kubectl import kubectl_tool
from .tools.deployment import deployment_tool
from .tools.service import service_tool
from .tools.pod import pod_tool

# Register all tools
tool_registry.register("kubernetes_tools", kubectl_tool)
tool_registry.register("kubernetes_tools", deployment_tool)
tool_registry.register("kubernetes_tools", service_tool)
tool_registry.register("kubernetes_tools", pod_tool)

# Export the tools for easy access
__all__ = ['kubectl_tool', 'deployment_tool', 'service_tool', 'pod_tool']