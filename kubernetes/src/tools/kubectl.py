from .base import BaseKubernetesTool, Arg

class KubectlTool(BaseKubernetesTool):
    def __init__(self):
        super().__init__(
            name="kubectl",
            description="Executes kubectl commands",
            script_template="kubectl.sh",
            args=[
                Arg(name="command", type="str", description="The kubectl command to execute", required=True),
                Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
            ]
        )