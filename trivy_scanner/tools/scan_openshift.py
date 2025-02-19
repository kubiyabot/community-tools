import json
from kubiya_sdk.tools.models import Arg
from .base import TrivyTool, register_trivy_tool

# Define Trivy scanning tools
trivy_scan_cluster = TrivyTool(
    name="scan_cluster",
    description="Scan entire OpenShift cluster for vulnerabilities using Trivy",
    content="""
    echo "Starting cluster-wide vulnerability scan..."
    trivy k8s --format json --report all
    """,
    args=[],
)

trivy_scan_namespace = TrivyTool(
    name="scan_namespace",
    description="Scan specific OpenShift namespace for vulnerabilities",
    content="""
    if [ -z "$namespace" ]; then
        echo "Error: Namespace is required"
        exit 1
    fi

    echo "Starting vulnerability scan for namespace: $namespace"
    trivy k8s --format json --report all --include-namespaces "$namespace"
    """,
    args=[
        Arg(
            name="namespace",
            description="Namespace to scan",
            required=True
        ),
    ],
)

trivy_scan_workload = TrivyTool(
    name="scan_workload",
    description="Scan specific workload for vulnerabilities",
    content="""
    if [ -z "$workload_type" ] || [ -z "$workload_name" ] || [ -z "$namespace" ]; then
        echo "Error: workload_type, workload_name, and namespace are required"
        exit 1
    fi

    echo "Starting vulnerability scan for $workload_type/$workload_name in namespace: $namespace"
    trivy k8s --format json --report all --include-namespaces "$namespace" --include-kinds "$workload_type"
    """,
    args=[
        Arg(name="workload_type", description="Type of workload (deployment, statefulset, etc)", required=True),
        Arg(name="workload_name", description="Name of the workload", required=True),
        Arg(name="namespace", description="Namespace of the workload", required=True),
    ],
)

# List of all Trivy tools
trivy_tools = [
    trivy_scan_cluster,
    trivy_scan_namespace,
    trivy_scan_workload,
]

# Register all Trivy tools
for tool in trivy_tools:
    register_trivy_tool(tool)
