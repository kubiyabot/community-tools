import os
from kubiya_sdk.tools import Tool, Arg, FileSpec

def read_script(filename):
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', filename)
    with open(script_path, 'r') as file:
        return file.read()

# Common environment variables and files for all tools
COMMON_ENV = [
    "KUBERNETES_SERVICE_HOST",
    "KUBERNETES_SERVICE_PORT",
]

COMMON_FILES = [
    FileSpec(source="~/.kube/config", destination="/root/.kube/config")
]

# Define tools
kubectl_tool = Tool(
    name="kubectl",
    description="Executes kubectl commands",
    type="container",
    image="bitnami/kubectl:latest",
    content=read_script("kubectl.sh"),
    args=[
        Arg(name="command", type="str", description="The kubectl command to execute", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
    ],
    env=COMMON_ENV,
    files=COMMON_FILES,
)

deployment_tool = Tool(
    name="deployment",
    description="Manages Kubernetes deployments",
    type="container",
    image="bitnami/kubectl:latest",
    content=read_script("deployment.sh"),
    args=[
        Arg(name="action", type="str", description="Action to perform (create, update, delete, get)", required=True),
        Arg(name="name", type="str", description="Name of the deployment", required=True),
        Arg(name="image", type="str", description="Container image for create/update actions", required=False),
        Arg(name="replicas", type="int", description="Number of replicas", required=False),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
    ],
    env=COMMON_ENV,
    files=COMMON_FILES,
)

service_tool = Tool(
    name="service",
    description="Manages Kubernetes services",
    type="container",
    image="bitnami/kubectl:latest",
    content=read_script("service.sh"),
    args=[
        Arg(name="action", type="str", description="Action to perform (create, delete, get)", required=True),
        Arg(name="name", type="str", description="Name of the service", required=True),
        Arg(name="type", type="str", description="Type of service (ClusterIP, NodePort, LoadBalancer)", required=False),
        Arg(name="port", type="int", description="Port number", required=False),
        Arg(name="target_port", type="int", description="Target port number", required=False),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
    ],
    env=COMMON_ENV,
    files=COMMON_FILES,
)

pod_tool = Tool(
    name="pod",
    description="Manages Kubernetes pods",
    type="container",
    image="bitnami/kubectl:latest",
    content=read_script("pod.sh"),
    args=[
        Arg(name="action", type="str", description="Action to perform (get, delete, logs)", required=True),
        Arg(name="name", type="str", description="Name of the pod", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
        Arg(name="container", type="str", description="Container name (for logs)", required=False),
    ],
    env=COMMON_ENV,
    files=COMMON_FILES,
)

resource_usage_tool = Tool(
    name="resource_usage",
    description="Gathers resource usage insights for the cluster",
    type="container",
    image="bitnami/kubectl:latest",
    content=read_script("resource_usage.sh"),
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
    ],
    env=COMMON_ENV,
    files=COMMON_FILES,
)

cluster_health_tool = Tool(
    name="cluster_health",
    description="Checks overall cluster health",
    type="container",
    image="bitnami/kubectl:latest",
    content=read_script("cluster_health.sh"),
    args=[],
    env=COMMON_ENV,
    files=COMMON_FILES,
)

scale_deployment_tool = Tool(
    name="scale_deployment",
    description="Scales a deployment to a specified number of replicas",
    type="container",
    image="bitnami/kubectl:latest",
    content=read_script("scale_deployment.sh"),
    args=[
        Arg(name="deployment", type="str", description="Name of the deployment", required=True),
        Arg(name="replicas", type="int", description="Number of desired replicas", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=False),
    ],
    env=COMMON_ENV,
    files=COMMON_FILES,
)

# Export all tools
__all__ = [
    'kubectl_tool',
    'deployment_tool',
    'service_tool',
    'pod_tool',
    'resource_usage_tool',
    'cluster_health_tool',
    'scale_deployment_tool',
]