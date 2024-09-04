from .base import BaseKubernetesTool, Arg

class DeploymentTool(BaseKubernetesTool):
    def __init__(self):
        super().__init__(
            name="deployment",
            description="Manages Kubernetes deployments",
            script_template="deployment.sh",
            args=[
                Arg(name="action", type="str", description="Action to perform (create, update, delete, get)", required=True),
                Arg(name="name", type="str", description="Name of the deployment", required=True),
                Arg(name="image", type="str", description="Container image for create/update actions", required=False),
                Arg(name="replicas", type="int", description="Number of replicas", required=False),
                Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
            ]
        )