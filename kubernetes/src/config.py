from kubiya_sdk.tools.models import Tool, Arg

deployment_tool = Tool(
    name="deployment",
    type="container",
    description="Manages Kubernetes deployments",
    image="bitnami/kubectl:latest",
    content="kubectl {{.action}} deployment {{.name}} {{if .image}}--image={{.image}}{{end}} {{if .replicas}}--replicas={{.replicas}}{{end}}",
    args=[
        Arg(name="action", type="str", description="Action to perform (create, update, delete, get)", required=True),
        Arg(name="name", type="str", description="Name of the deployment", required=True),
        Arg(name="image", type="str", description="Container image for create/update actions", required=False),
        Arg(name="replicas", type="int", description="Number of replicas", required=False),
    ],
    env=[
        "KUBERNETES_SERVICE_HOST",
        "KUBERNETES_SERVICE_PORT",
    ],
    files=[
        {"source": "~/.kube/config", "destination": "/root/.kube/config"}
    ]
)