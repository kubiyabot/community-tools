#!/bin/bash
set -e

# Helper function for logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Helper function to check command result
check_command() {
    if [ $? -ne 0 ]; then
        log "❌ Error: $1"
        exit 1
    fi
    log "✅ $2"
}

# Helper function to check if a resource exists
resource_exists() {
    kubectl get "$1" -n "$2" "$3" &> /dev/null
}

log "🚀 Initializing Kubernetes tools..."

# Check prerequisites
log "Checking prerequisites..."
if ! command -v kubectl &> /dev/null; then
    log "❌ Error: kubectl is not installed"
    exit 1
fi
check_command "kubectl check failed" "kubectl is available"

if ! command -v helm &> /dev/null; then
    log "❌ Error: helm is not installed"
    exit 1
fi
check_command "helm check failed" "helm is available"

# Test kubectl connection
log "Testing kubectl connection..."
if ! kubectl cluster-info &> /dev/null; then
    log "❌ Error: Cannot connect to Kubernetes cluster"
    log "Please check your kubeconfig and cluster access"
    exit 1
fi
check_command "cluster connection failed" "Connected to Kubernetes cluster"

# Create namespace if it doesn't exist
log "Setting up kubiya namespace..."
if ! kubectl get namespace kubiya &> /dev/null; then
    kubectl create namespace kubiya
    check_command "namespace creation failed" "Created kubiya namespace"
else
    log "✅ Kubiya namespace already exists"
fi

# Check if kubiya-kubewatch is already deployed
log "Checking kubiya-kubewatch deployment..."
if ! helm list -n kubiya | grep -q "kubiya-kubewatch"; then
    # Only install if not already present
    log "kubiya-kubewatch not found, installing..."
    
    # Add helm repo if needed
    helm repo add robusta https://robusta-charts.storage.googleapis.com || true
    helm repo update
    check_command "helm repo setup failed" "Helm repository configured"

    helm install kubiya-kubewatch robusta/kubewatch \
        --namespace kubiya \
        --create-namespace \
        --set rbac.create=true \
        --set image.repository=ghcr.io/kubiyabot/kubewatch \
        --set image.tag=latest
    check_command "kubiya-kubewatch installation failed" "Initiated kubiya-kubewatch installation"
else
    log "✅ kubiya-kubewatch is already installed"
fi

# Update kubiya-kubewatch config
log "Updating kubiya-kubewatch configuration..."
CONFIG_PATH="$(dirname "$0")/../config/kubewatch.yaml"
if [ ! -f "$CONFIG_PATH" ]; then
    log "❌ Error: Kubewatch config not found at $CONFIG_PATH"
    exit 1
fi

# Update the configmap with latest configuration
kubectl create configmap kubiya-kubewatch-config -n kubiya \
    --from-file=.kubewatch.yaml="$CONFIG_PATH" \
    -o yaml --dry-run=client | kubectl apply -f -
check_command "configmap update failed" "Updated kubiya-kubewatch configuration"

# Restart the deployment to pick up new config
log "Triggering kubiya-kubewatch restart..."
kubectl rollout restart deployment/kubiya-kubewatch -n kubiya
check_command "restart trigger failed" "Triggered kubiya-kubewatch restart"

log "🎉 Initialization completed successfully"
log "Note: Deployment updates are in progress and may take a few minutes to complete" 