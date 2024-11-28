from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

check_metrics_server = KubernetesTool(
    name="check_metrics_server",
    description="Checks if metrics-server is installed and functioning properly",
    content="""
#!/bin/bash
set -e

echo "🔍 Checking metrics-server status..."
echo "================================="

# Check if metrics API is available
if ! check_api_resource metrics.k8s.io; then
    echo "❌ Metrics API is not installed"
    echo "To install metrics-server, you can use:"
    echo "1. Helm:"
    echo "   helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/"
    echo "   helm install metrics-server metrics-server/metrics-server"
    echo ""
    echo "2. YAML manifest:"
    echo "   kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"
    exit 1
fi

# Check if metrics-server pods are running
echo "📊 Metrics Server Pods:"
kubectl get pods -n kube-system -l k8s-app=metrics-server -o wide

# Check if metrics are being collected
echo -e "\n📈 Testing metrics collection..."
if kubectl top nodes &>/dev/null; then
    echo "✅ Metrics are being collected successfully"
    kubectl top nodes | head -n 3
else
    echo "❌ Metrics collection is not working"
    echo "Checking metrics-server logs for potential issues..."
    kubectl logs -n kube-system -l k8s-app=metrics-server --tail=20
fi
""",
    args=[],
)

feature_gate_checker = KubernetesTool(
    name="check_feature_gates",
    description="Checks the status of Kubernetes feature gates",
    content="""
#!/bin/bash
set -e

echo "🔍 Checking Kubernetes Feature Gates"
echo "=================================="

# Check API server feature gates
echo "📡 API Server Feature Gates:"
kubectl get pods -n kube-system -l component=kube-apiserver -o json | \
    jq -r '.items[].spec.containers[].command[] | select(contains("--feature-gates"))' | \
    sed 's/--feature-gates=//' | tr ',' '\\n' | sed 's/^/  /'

# Check kubelet feature gates on nodes
echo -e "\n🖥️ Node Feature Gates:"
kubectl get nodes -o json | \
    jq -r '.items[] | "Node: \(.metadata.name)\n  Feature Gates: \(.metadata.annotations["kubelet.alpha.kubernetes.io/config"])"'

if [ -n "$feature" ]; then
    echo -e "\n🔍 Checking specific feature: $feature"
    if check_feature_gate "$feature"; then
        echo "✅ Feature '$feature' is enabled"
    else
        echo "❌ Feature '$feature' is not enabled"
    fi
fi
""",
    args=[
        Arg(name="feature", type="str", description="Specific feature gate to check", required=False),
    ],
)

install_metrics_server = KubernetesTool(
    name="install_metrics_server",
    description="Installs and configures metrics-server in the cluster",
    content="""
#!/bin/bash
set -e

echo "📊 Installing Metrics Server"
echo "=========================="

# Check if metrics-server is already installed
if kubectl get deployment metrics-server -n kube-system &>/dev/null; then
    echo "ℹ️ Metrics Server is already installed"
    echo "Current status:"
    kubectl get deployment metrics-server -n kube-system
    exit 0
fi

# Install metrics-server
echo "📦 Installing Metrics Server..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Wait for deployment
echo "⏳ Waiting for Metrics Server to be ready..."
kubectl rollout status deployment metrics-server -n kube-system --timeout=90s

# Verify installation
echo -e "\n📈 Verifying installation..."
sleep 10  # Give it some time to collect metrics

if kubectl top nodes &>/dev/null; then
    echo "✅ Metrics Server installed and working properly"
    echo -e "\nSample metrics:"
    kubectl top nodes | head -n 3
else
    echo "⚠️ Metrics Server installed but not collecting metrics yet"
    echo "Checking logs for potential issues:"
    kubectl logs -n kube-system -l k8s-app=metrics-server --tail=20
fi
""",
    args=[],
)

check_cluster_features = KubernetesTool(
    name="check_cluster_features",
    description="Comprehensive check of various Kubernetes cluster features and add-ons",
    content="""
#!/bin/bash
set -e

echo "🔍 Checking Cluster Features"
echo "=========================="

# Check Core Features
echo "📡 Core Features:"

# Check metrics-server
echo -n "Metrics Server: "
if check_api_resource metrics.k8s.io; then
    echo "✅ Installed"
else
    echo "❌ Not installed"
fi

# Check Ingress
echo -n "Ingress Controller: "
if kubectl get pods -A | grep -q ingress-controller; then
    echo "✅ Installed"
else
    echo "❌ Not installed"
fi

# Check CSI Drivers
echo -e "\n💾 Storage Features:"
echo "CSI Drivers installed:"
kubectl get csidrivers --no-headers 2>/dev/null | \
    awk '{print "  ✓ " $1}' || echo "  No CSI drivers found"

# Check CRDs
echo -e "\n🔧 Custom Resource Definitions:"
kubectl get crd --no-headers | \
    awk '{print "  ✓ " $1}' || echo "  No CRDs found"

# Check API Extensions
echo -e "\n🔌 API Extensions:"
kubectl get apiservices --no-headers | \
    grep -v "Local" | \
    awk '{print "  ✓ " $1 " (" $6 ")"}' || echo "  No API extensions found"

# Check Feature Gates
echo -e "\n🚪 Feature Gates:"
kubectl get nodes -o json | \
    jq -r '.items[0].metadata.annotations | 
    to_entries[] | 
    select(.key | contains("feature-gates")) | 
    .value' | \
    tr ',' '\\n' | \
    sed 's/^/  ✓ /'

# Provide recommendations
echo -e "\n💡 Recommendations:"
if ! check_api_resource metrics.k8s.io; then
    echo "  • Consider installing metrics-server for resource monitoring"
fi
if ! kubectl get pods -A | grep -q ingress-controller; then
    echo "  • Consider installing an Ingress Controller for HTTP routing"
fi
""",
    args=[],
)

# Register all tools
tools = [
    check_metrics_server,
    feature_gate_checker,
    install_metrics_server,
    check_cluster_features,
]

for tool in tools:
    tool_registry.register("kubernetes", tool)

__all__ = [
    'check_metrics_server',
    'feature_gate_checker',
    'install_metrics_server',
    'check_cluster_features',
] 