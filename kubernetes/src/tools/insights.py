from .base import BaseKubernetesTool, Arg

class ResourceUsageTool(BaseKubernetesTool):
    def __init__(self):
        super().__init__(
            name="resource_usage",
            description="Gathers resource usage insights for the cluster",
            script_template="insights/resource_usage.sh",
            args=[
                Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
            ]
        )

class PodStatusTool(BaseKubernetesTool):
    def __init__(self):
        super().__init__(
            name="pod_status",
            description="Gathers pod status insights for the cluster",
            script_template="insights/pod_status.sh",
            args=[
                Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
            ]
        )

class ClusterHealthTool(BaseKubernetesTool):
    def __init__(self):
        super().__init__(
            name="cluster_health",
            description="Checks overall cluster health",
            script_template="insights/cluster_health.sh",
            args=[]
        )