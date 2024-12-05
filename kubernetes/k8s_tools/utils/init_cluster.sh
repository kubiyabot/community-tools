#!/bin/bash
set -e

echo "Initializing Kubernetes tools..."

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo "Error: helm is not installed"
    exit 1
fi

# Create namespace if it doesn't exist
if ! kubectl get namespace kubiya &> /dev/null; then
    echo "Creating kubiya namespace..."
    kubectl create namespace kubiya
fi

# Create kubewatch config
echo "Creating kubewatch configuration..."
kubectl delete configmap kubewatch-config -n kubiya --ignore-not-found

kubectl create configmap kubewatch-config -n kubiya --from-file=.kubewatch.yaml="$(dirname "$0")/../config/kubewatch.yaml"

# Deploy kubewatch
echo "Deploying kubewatch..."
helm repo add robusta https://robusta-charts.storage.googleapis.com
helm repo update

helm upgrade --install kubewatch robusta/kubewatch \
    --namespace kubiya \
    --set config.handler.webhook.enabled=true \
    --set config.handler.webhook.url=https://webhooksource-kubiya.hooks.kubiya.ai:8443/webhook \
    --set rbac.create=true \
    --set image.repository=ghcr.io/kubiyabot/kubewatch \
    --set image.tag=latest

# Wait for deployment
echo "Waiting for kubewatch deployment..."
kubectl rollout status deployment/kubewatch -n kubiya --timeout=300s

echo "Initialization completed successfully" 