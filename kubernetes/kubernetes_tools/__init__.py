from kubiya_sdk.tools import Tool, Source
from .kubectl import KUBECTL_TOOL
from .deployment import DEPLOYMENT_TOOL
from .service import SERVICE_TOOL
from .pod import POD_TOOL
from .config import KUBERNETES_TOOLS_SOURCE

# Create Tool instances
kubectl_tool = Tool(**KUBECTL_TOOL, source=KUBERNETES_TOOLS_SOURCE)
deployment_tool = Tool(**DEPLOYMENT_TOOL, source=KUBERNETES_TOOLS_SOURCE)
service_tool = Tool(**SERVICE_TOOL, source=KUBERNETES_TOOLS_SOURCE)
pod_tool = Tool(**POD_TOOL, source=KUBERNETES_TOOLS_SOURCE)

# Export the tools
__all__ = ['kubectl_tool', 'deployment_tool', 'service_tool', 'pod_tool']