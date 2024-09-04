from .base import BaseKubernetesTool, Arg

class ServiceTool(BaseKubernetesTool):
    def __init__(self):
        super().__init__(
            name="service",
            description="Manages Kubernetes services",
            script_template="service.sh",
            args=[
                Arg(name="action", type="str", description="Action to perform (create, delete, get)", required=True),
                Arg(name="name", type="str", description="Name of the service", required=True),
                Arg(name="type", type="str", description="Type of service (ClusterIP, NodePort, LoadBalancer)", required=False),
                Arg(name="port", type="int", description="Port number", required=False),
                Arg(name="target_port", type="int", description="Target port number", required=False),
                Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
            ]
        )