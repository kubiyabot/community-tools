from kubiya_sdk.tools.models import Arg
from kubiya_sdk.tools.registry import tool_registry
from tools.base import BaseOCTool

# Project Tools
list_projects = BaseOCTool(
    name="list_projects",
    description="List all OpenShift projects",
    content="""
    echo "=== Available Projects ==="
    oc get projects -o custom-columns=NAME:.metadata.name,DISPLAY_NAME:.metadata.annotations.openshift\\.io/display-name,STATUS:.status.phase,CREATED:.metadata.creationTimestamp
    """,
)

create_project = BaseOCTool(
    name="create_project",
    description="Create a new project in OpenShift",
    content="""
    oc new-project $project_name --description='$description'
    """,
    args=[
        Arg(name="project_name", description="Name of the project to create", required=True),
        Arg(name="description", description="Project description", required=False),
    ],
)

switch_project = BaseOCTool(
    name="switch_project",
    description="Switch to a different OpenShift project",
    content="""
    if ! oc get project "$project_name" >/dev/null 2>&1; then
        echo "Error: Project $project_name does not exist"
        exit 1
    fi
    oc project "$project_name"
    """,
    args=[
        Arg(name="project_name", description="Name of the project to switch to", required=True),
    ],
)

delete_project = BaseOCTool(
    name="delete_project",
    description="Delete an OpenShift project",
    content="""
    if ! oc get project "$project_name" >/dev/null 2>&1; then
        echo "Error: Project $project_name does not exist"
        exit 1
    fi
    oc delete project "$project_name"
    """,
    args=[
        Arg(name="project_name", description="Name of the project to delete", required=True),
    ],
)

# Deployment Tools
deploy_module = BaseOCTool(
    name="deploy_module",
    description="Deploy or update a module in OpenShift",
    content="""
    # Validate module exists
    if [ ! -f "$module_path" ]; then
        echo "Error: Module file $module_path does not exist"
        exit 1
    fi
    
    # Apply the module configuration
    echo "Deploying module from $module_path to namespace $namespace"
    oc apply -f "$module_path" -n $namespace
    
    # Wait for deployment
    if oc get deployment -n $namespace 2>/dev/null | grep -q "$module"; then
        echo "Waiting for deployment to complete..."
        oc rollout status deployment/$module -n $namespace
    fi
    """,
    args=[
        Arg(name="module", description="Name of the module to deploy", required=True),
        Arg(name="module_path", description="Path to the module's YAML configuration file", required=True),
        Arg(name="namespace", description="Target namespace", required=False, default="default"),
    ],
)

scale_deployment = BaseOCTool(
    name="scale_deployment",
    description="Scale a deployment to specified number of replicas",
    content="""
    NAMESPACE=${namespace:-default}
    
    # Verify deployment exists
    if ! oc get deployment $deployment_name -n $NAMESPACE >/dev/null 2>&1; then
        echo "Error: Deployment $deployment_name not found in namespace $NAMESPACE"
        exit 1
    fi
    
    oc scale deployment/$deployment_name --replicas=$replicas -n $NAMESPACE
    oc rollout status deployment/$deployment_name -n $NAMESPACE
    """,
    args=[
        Arg(name="deployment_name", description="Name of the deployment to scale", required=True),
        Arg(name="replicas", description="Number of desired replicas", required=True),
        Arg(name="namespace", description="Target namespace", required=False, default="default"),
    ],
)

# Storage Tool
create_storage = BaseOCTool(
    name="create_storage",
    description="Create persistent storage",
    content="""
    cat <<EOF | oc apply -n $namespace -f -
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: $pvc_name
    spec:
      accessModes:
        - $access_mode
      resources:
        requests:
          storage: $storage_size
      storageClassName: $storage_class
EOF
    """,
    args=[
        Arg(name="pvc_name", description="Name of the PVC", required=True),
        Arg(name="storage_size", description="Size of storage (e.g., 10Gi)", required=True),
        Arg(name="storage_class", description="Storage class to use", required=True),
        Arg(name="access_mode", description="Access mode (ReadWriteOnce, ReadOnlyMany, ReadWriteMany)", required=False, default="ReadWriteOnce"),
        Arg(name="namespace", description="Target namespace", required=False, default="default"),
    ],
)

# Route Tool
create_route = BaseOCTool(
    name="create_route",
    description="Create or update an OpenShift route",
    content="""
    oc create route edge $route_name --service=$service_name --hostname=$hostname -n $namespace --insecure-policy=Redirect --dry-run=client -o yaml | oc apply -f -
    """,
    args=[
        Arg(name="route_name", description="Name of the route", required=True),
        Arg(name="service_name", description="Name of the service to expose", required=True),
        Arg(name="hostname", description="Hostname for the route", required=True),
        Arg(name="namespace", description="Target namespace", required=False, default="default"),
    ],
)

# Context Tool
get_context = BaseOCTool(
    name="get_context",
    description="Display current context information",
    content="""
    echo "=== Current User ==="
    oc whoami
    
    echo -e "\n=== Current Project ==="
    oc project
    
    echo -e "\n=== Current Server ==="
    oc whoami --show-server
    """,
)

# Resource Listing Tools
get_resources = BaseOCTool(
    name="get_resources",
    description="List specific OpenShift resources",
    content="""
    oc get $resource_type -n $namespace -o wide
    """,
    args=[
        Arg(name="resource_type", description="Resource type (pods, deployments, services, etc)", required=True),
        Arg(name="namespace", description="Target namespace", required=False, default="default"),
    ],
)

describe_resource = BaseOCTool(
    name="describe_resource",
    description="Get detailed information about a specific resource",
    content="""
    if ! oc get $resource_type/$resource_name -n $namespace >/dev/null 2>&1; then
        echo "Error: Resource $resource_name of type $resource_type not found in namespace $namespace"
        exit 1
    fi
    oc describe $resource_type/$resource_name -n $namespace
    """,
    args=[
        Arg(name="resource_type", description="Resource type (pod, deployment, service, etc)", required=True),
        Arg(name="resource_name", description="Name of the resource", required=True),
        Arg(name="namespace", description="Target namespace", required=False, default="default"),
    ],
)

# Logging Tool
get_logs = BaseOCTool(
    name="get_logs",
    description="Get logs from a specific pod",
    content="""
    if ! oc get pod $pod_name -n $namespace >/dev/null 2>&1; then
        echo "Error: Pod $pod_name not found in namespace $namespace"
        exit 1
    fi
    
    oc logs $pod_name -n $namespace --tail=${tail_lines} ${follow:+--follow}
    """,
    args=[
        Arg(name="pod_name", description="Name of the pod", required=True),
        Arg(name="tail_lines", description="Number of lines to show from the end", required=False, default="100"),
        Arg(name="follow", description="Follow the logs in real-time", required=False, default="false"),
        Arg(name="namespace", description="Target namespace", required=False, default="default"),
    ],
)

# Quota Management
create_quota = BaseOCTool(
    name="create_quota",
    description="Create a resource quota in a namespace",
    content="""
    cat <<EOF | oc apply -n $namespace -f -
    apiVersion: v1
    kind: ResourceQuota
    metadata:
      name: $quota_name
    spec:
      hard:
        cpu: "$cpu_limit"
        memory: "$memory_limit"
        pods: "$pod_limit"
EOF
    """,
    args=[
        Arg(name="quota_name", description="Name of the quota", required=True),
        Arg(name="cpu_limit", description="CPU limit (e.g., '2' or '2000m')", required=True),
        Arg(name="memory_limit", description="Memory limit (e.g., '2Gi')", required=True),
        Arg(name="pod_limit", description="Maximum number of pods", required=True),
        Arg(name="namespace", description="Target namespace", required=False, default="default"),
    ],
)

# Monitoring Tools
get_cluster_status = BaseOCTool(
    name="get_cluster_status",
    description="Get OpenShift cluster status",
    content="""
    echo "=== Cluster Operators Status ==="
    oc get clusteroperators
    """,
)

get_node_status = BaseOCTool(
    name="get_node_status",
    description="Get status of cluster nodes",
    content="""
    echo "=== Node Status ==="
    oc get nodes -o wide
    """,
)

get_cluster_version = BaseOCTool(
    name="get_cluster_version",
    description="Get OpenShift cluster version information",
    content="""
    echo "=== Cluster Version ==="
    oc get clusterversion
    """,
)

# List of all OpenShift tools
oc_tools = [
    list_projects,
    create_project,
    switch_project,
    delete_project,
    deploy_module,
    scale_deployment,
    create_storage,
    create_route,
    get_context,
    get_resources,
    describe_resource,
    get_logs,
    create_quota,
    get_cluster_status,
    get_node_status,
    get_cluster_version,
]

# Register all OpenShift tools
for tool in oc_tools:
    tool_registry.register("openshift", tool)
