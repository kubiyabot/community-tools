from .base import BaseKubernetesTool, Arg

class PodTool(BaseKubernetesTool):
    def __init__(self):
        super().__init__(
            name="pod",
            description="Manages Kubernetes pods",
            script_template="pod.sh",
            args=[
                Arg(name="action", type="str", description="Action to perform (get, delete, logs)", required=True),
                Arg(name="name", type="str", description="Name of the pod", required=True),
                Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
                Arg(name="container", type="str", description="Container name (for logs)", required=False),
            ]
        )