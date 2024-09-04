from .base import BaseKubernetesTool, Arg

class ScaleDeploymentTool(BaseKubernetesTool):
    def __init__(self):
        super().__init__(
            name="scale_deployment",
            description="Scales a deployment to a specified number of replicas",
            script_template="automations/scale_deployment.sh",
            args=[
                Arg(name="deployment", type="str", description="Name of the deployment", required=True),
                Arg(name="replicas", type="int", description="Number of desired replicas", required=True),
                Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
            ]
        )

class RollingUpdateTool(BaseKubernetesTool):
    def __init__(self):
        super().__init__(
            name="rolling_update",
            description="Performs a rolling update on a deployment",
            script_template="automations/rolling_update.sh",
            args=[
                Arg(name="deployment", type="str", description="Name of the deployment", required=True),
                Arg(name="image", type="str", description="New image to update to", required=True),
                Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
            ]
        )

class AutoHealingTool(BaseKubernetesTool):
    def __init__(self):
        super().__init__(
            name="auto_healing",
            description="Attempts to auto-heal non-running pods",
            script_template="automations/auto_healing.sh",
            args=[
                Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
            ]
        )