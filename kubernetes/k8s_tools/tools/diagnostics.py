from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

resource_consumption_analyzer = KubernetesTool(
    name="analyze_resource_consumption",
    description="Analyzes CPU and memory consumption of pods with historical data",
    content="""
#!/bin/bash
set -e

namespace=${namespace:-"--all-namespaces"}
if [ "$namespace" != "--all-namespaces" ]; then
    namespace="-n $namespace"
fi

echo "🔍 Analyzing resource consumption..."
echo "===================================="

# Current resource usage
echo "📊 Current Top CPU Consumers:"
kubectl top pods $namespace --sort-by=cpu | head -n 10 | \
    awk 'NR>1 {print "  🔸 " $0}'

echo -e "\n📊 Current Top Memory Consumers:"
kubectl top pods $namespace --sort-by=memory | head -n 10 | \
    awk 'NR>1 {print "  🔸 " $0}'

# Get events related to resource issues in the last hour
echo -e "\n⚠️ Resource-related events (last hour):"
kubectl get events $namespace --sort-by='.lastTimestamp' \
    --field-selector type=Warning \
    --no-headers | \
    grep -E "OOMKilled|CPU throttling|memory pressure|disk pressure" | \
    tail -n 10 | \
    awk '{print "  ⚠️ " $0}'
""",
    args=[
        Arg(name="namespace", type="str", description="Namespace to analyze (optional, defaults to all namespaces)", required=False),
    ],
)

privileged_container_checker = KubernetesTool(
    name="check_privileged_containers",
    description="Identifies pods running with privileged containers and security contexts",
    content="""
#!/bin/bash
set -e

namespace=${namespace:-"--all-namespaces"}
if [ "$namespace" != "--all-namespaces" ]; then
    namespace="-n $namespace"
fi

echo "🔒 Checking for privileged containers..."
echo "====================================="

# Check for privileged containers
kubectl get pods $namespace -o json | jq -r '
  .items[] | 
  select(
    .spec.containers[].securityContext.privileged == true or
    .spec.initContainers[]?.securityContext.privileged == true
  ) |
  "⚠️  Pod: \(.metadata.name)\n   Namespace: \(.metadata.namespace)\n   Node: \(.spec.nodeName)\n   Created: \(.metadata.creationTimestamp)"
'

echo -e "\n🔍 Additional security context analysis:"
kubectl get pods $namespace -o json | jq -r '
  .items[] | 
  select(
    .spec.containers[].securityContext.runAsRoot == true or
    .spec.containers[].securityContext.allowPrivilegeEscalation == true
  ) |
  "⚠️  Pod: \(.metadata.name)\n   Namespace: \(.metadata.namespace)\n   Security Concerns: \(
    if .spec.containers[].securityContext.runAsRoot == true then "Runs as root, " else "" end
  )\(
    if .spec.containers[].securityContext.allowPrivilegeEscalation == true then "Allows privilege escalation" else "" end
  )"
'
""",
    args=[
        Arg(name="namespace", type="str", description="Namespace to check (optional, defaults to all namespaces)", required=False),
    ],
)

traffic_routing_analyzer = KubernetesTool(
    name="analyze_traffic_routing",
    description="Analyzes traffic routing configuration for pods in a namespace",
    content="""
#!/bin/bash
set -e

echo "🌐 Analyzing traffic routing in namespace: $namespace"
echo "================================================"

# Check Services and their endpoints
echo "📡 Services and Endpoints:"
kubectl get services -n $namespace -o json | jq -r '.items[] | "Service: \(.metadata.name)\n  Type: \(.spec.type)\n  Selector: \(.spec.selector | to_entries | map("\(.key)=\(.value)") | join(", "))\n"'

# Get endpoints for each service
services=$(kubectl get services -n $namespace -o jsonpath='{.items[*].metadata.name}')
for svc in $services; do
    echo "🔍 Analyzing service: $svc"
    echo "  Endpoints:"
    kubectl get endpoints $svc -n $namespace -o json | \
        jq -r '.subsets[]?.addresses[]? | "    Pod IP: \(.ip), Node: \(.nodeName)"'
    
    # Get pods matching service selector
    echo "  Targeted Pods:"
    selector=$(kubectl get service $svc -n $namespace -o json | \
        jq -r '.spec.selector | to_entries | map("\(.key)=\(.value)") | join(",")')
    if [ ! -z "$selector" ]; then
        kubectl get pods -n $namespace -l $selector -o wide | \
            awk 'NR>1 {print "    🔹 " $1 " (Status: " $3 ", IP: " $6 ")"}'
    fi
done

# Check Ingress configurations
echo -e "\n🌍 Ingress Configurations:"
kubectl get ingress -n $namespace -o json | \
    jq -r '.items[] | "Ingress: \(.metadata.name)\n  Rules:\n\(.spec.rules[] | "    Host: \(.host)\n    Paths:\n\(.http.paths[] | "      Path: \(.path)\n      Service: \(.backend.service.name)\n      Port: \(.backend.service.port.number)")")"'
""",
    args=[
        Arg(name="namespace", type="str", description="Namespace to analyze traffic routing", required=True),
    ],
)

certificate_analyzer = KubernetesTool(
    name="analyze_certificates",
    description="Analyzes and validates CA certificates in the cluster",
    content="""
#!/bin/bash
set -e

echo "🔐 Analyzing Cluster Certificates"
echo "==============================="

# Check API server certificate
echo "📜 API Server Certificate:"
kubectl get --raw /api/v1/namespaces | \
    openssl x509 -noout -dates -in /var/run/secrets/kubernetes.io/serviceaccount/ca.crt 2>/dev/null | \
    awk '{print "  " $0}'

# Check secrets of type kubernetes.io/tls
echo -e "\n📜 TLS Secrets in cluster:"
kubectl get secrets --all-namespaces -o json | \
jq -r '.items[] | 
  select(.type=="kubernetes.io/tls") | 
  "Namespace: \(.metadata.namespace)\nName: \(.metadata.name)\nCreated: \(.metadata.creationTimestamp)"' | \
sed 's/^/  /'

# Check certificate expiration for ingress controllers
echo -e "\n📜 Ingress Controller Certificates:"
kubectl get pods --all-namespaces -l app.kubernetes.io/name=ingress-nginx -o json | \
jq -r '.items[].metadata | "Namespace: \(.namespace)\nPod: \(.name)"' | \
sed 's/^/  /'

# Check kubelet client certificates
echo -e "\n📜 Kubelet Client Certificates:"
kubectl get nodes -o json | \
jq -r '.items[] | "Node: \(.metadata.name)\nCertificate Expiry: \(.status.conditions[] | select(.type=="Ready") | .lastHeartbeatTime)"' | \
sed 's/^/  /'
""",
    args=[],
)

crashloop_analyzer = KubernetesTool(
    name="analyze_crashloop",
    description="Analyzes pods in CrashLoopBackOff state",
    content="""
#!/bin/bash
set -e

namespace=${namespace:-"default"}

echo "🔍 Analyzing CrashLoopBackOff pods in namespace: $namespace"
echo "======================================================="

# Find pods in CrashLoopBackOff state
crashloop_pods=$(kubectl get pods -n $namespace -o json | \
    jq -r '.items[] | select(.status.containerStatuses[]?.state.waiting.reason=="CrashLoopBackOff") | .metadata.name')

if [ -z "$crashloop_pods" ]; then
    echo "✅ No pods in CrashLoopBackOff state found in namespace $namespace"
    exit 0
fi

for pod in $crashloop_pods; do
    echo "📝 Analysis for pod: $pod"
    echo "------------------------"
    
    # Get pod details
    echo "🔹 Pod Status:"
    kubectl describe pod $pod -n $namespace | \
        grep -A 5 "Status:" | sed 's/^/  /'
    
    # Get recent events
    echo -e "\n🔹 Recent Events:"
    kubectl get events -n $namespace --field-selector involvedObject.name=$pod --sort-by='.lastTimestamp' | \
        tail -n 5 | sed 's/^/  /'
    
    # Get logs from previous instance
    echo -e "\n🔹 Last logs before crash:"
    kubectl logs $pod -n $namespace --previous --tail=20 2>/dev/null | \
        sed 's/^/  /' || echo "  No previous logs available"
    
    # Get resource usage
    echo -e "\n🔹 Resource Usage:"
    kubectl top pod $pod -n $namespace 2>/dev/null | \
        sed 's/^/  /' || echo "  Resource metrics not available"
    
    # Get container status details
    echo -e "\n🔹 Container Status Details:"
    kubectl get pod $pod -n $namespace -o json | \
        jq -r '.status.containerStatuses[] | "  Container: \(.name)\n  Restart Count: \(.restartCount)\n  Last State: \(.lastState)\n  Current State: \(.state)"' | \
        sed 's/^/  /'
done
""",
    args=[
        Arg(name="namespace", type="str", description="Namespace to analyze (defaults to 'default')", required=False),
    ],
)

node_event_analyzer = KubernetesTool(
    name="analyze_node_events",
    description="Lists nodes with their associated events",
    content="""
#!/bin/bash
set -e

echo "🖥️ Analyzing Node Events"
echo "======================="

# Get all nodes
nodes=$(kubectl get nodes -o jsonpath='{.items[*].metadata.name}')

for node in $nodes; do
    echo "📡 Node: $node"
    echo "----------------"
    
    # Get node status
    echo "Status:"
    kubectl describe node $node | grep "Conditions:" -A 5 | sed 's/^/  /'
    
    # Get node events
    echo -e "\nEvents:"
    kubectl get events --field-selector involvedObject.name=$node,involvedObject.kind=Node \
        --sort-by='.lastTimestamp' | \
        awk 'NR>1 {print "  " $0}'
    
    echo -e "\nResource Usage:"
    kubectl top node $node 2>/dev/null | awk 'NR>1 {print "  " $0}' || echo "  Resource metrics not available"
    echo
done
""",
    args=[],
)

debug_container_tool = KubernetesTool(
    name="enable_debug_container",
    description="Enables a debug container for a specified pod",
    content="""
#!/bin/bash
set -e

echo "🔧 Enabling debug container for pod: $pod_name in namespace: $namespace"
echo "=================================================================="

# Check if pod exists
if ! kubectl get pod $pod_name -n $namespace >/dev/null 2>&1; then
    echo "❌ Pod $pod_name not found in namespace $namespace"
    exit 1
fi

# Enable debug container
echo "📦 Adding debug container..."
kubectl debug -n $namespace $pod_name \
    --image=busybox \
    --target=$pod_name \
    -it -- sh

echo "✅ Debug container enabled successfully"
""",
    args=[
        Arg(name="pod_name", type="str", description="Name of the pod to debug", required=True),
        Arg(name="namespace", type="str", description="Namespace of the pod", required=True),
    ],
)

# Register all tools
tools = [
    resource_consumption_analyzer,
    privileged_container_checker,
    traffic_routing_analyzer,
    certificate_analyzer,
    crashloop_analyzer,
    node_event_analyzer,
    debug_container_tool,
]

for tool in tools:
    tool_registry.register("kubernetes", tool)

__all__ = [
    'resource_consumption_analyzer',
    'privileged_container_checker',
    'traffic_routing_analyzer',
    'certificate_analyzer',
    'crashloop_analyzer',
    'node_event_analyzer',
    'debug_container_tool',
] 