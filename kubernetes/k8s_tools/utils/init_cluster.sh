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

# Create kubewatch config
log "Creating kubewatch configuration..."
CONFIG_PATH="$(dirname "$0")/../config/kubewatch.yaml"
if [ ! -f "$CONFIG_PATH" ]; then
    log "❌ Error: Kubewatch config not found at $CONFIG_PATH"
    exit 1
fi

kubectl delete configmap kubewatch-config -n kubiya --ignore-not-found
check_command "failed to delete old configmap" "Cleaned up old configmap"

kubectl create configmap kubewatch-config -n kubiya --from-file=.kubewatch.yaml="$CONFIG_PATH"
check_command "configmap creation failed" "Created kubewatch configmap"

# Deploy kubewatch
log "Setting up helm repository..."
helm repo add robusta https://robusta-charts.storage.googleapis.com
helm repo update
check_command "helm repo setup failed" "Helm repository configured"

log "Deploying kubewatch..."
helm upgrade --install kubewatch robusta/kubewatch \
    --namespace kubiya \
    --set config.handler.webhook.enabled=true \
    --set config.handler.webhook.url=https://webhooksource-kubiya.hooks.kubiya.ai:8443/webhook \
    --set rbac.create=true \
    --set image.repository=ghcr.io/kubiyabot/kubewatch \
    --set image.tag=latest
check_command "kubewatch deployment failed" "Deployed kubewatch"

# Wait for deployment
log "Waiting for kubewatch deployment..."
kubectl rollout status deployment/kubewatch -n kubiya --timeout=300s
check_command "deployment verification failed" "Kubewatch deployment is ready"

log "🎉 Initialization completed successfully" 