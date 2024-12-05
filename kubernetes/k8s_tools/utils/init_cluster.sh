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

# Ensure curl is installed
if ! command -v curl &> /dev/null; then
    log "Installing curl..."
    apt-get update && apt-get install -y curl
    check_command "curl installation failed" "curl installed successfully"
else
    log "✅ curl is already installed"
fi

# Ensure required binaries directory exists
TOOLS_DIR="/usr/local/bin"
mkdir -p "$TOOLS_DIR"

# Install kubectl if not present
if ! command -v kubectl &> /dev/null; then
    log "Installing kubectl..."
    curl -Lo "$TOOLS_DIR/kubectl" "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    chmod +x "$TOOLS_DIR/kubectl"
    check_command "kubectl installation failed" "kubectl installed successfully"
else
    log "✅ kubectl is already installed"
fi

# Install helm if not present
if ! command -v helm &> /dev/null; then
    log "Installing helm..."
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | HELM_INSTALL_DIR="$TOOLS_DIR" bash
    check_command "helm installation failed" "helm installed successfully"
else
    log "✅ helm is already installed"
fi

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

# Load kubewatch config
CONFIG_PATH="$(dirname "$0")/../config/kubewatch.yaml"
if [ ! -f "$CONFIG_PATH" ]; then
    log "❌ Error: Kubewatch config not found at $CONFIG_PATH"
    exit 1
fi

# Create values file for helm
HELM_VALUES=$(cat <<EOF
configmap:
  create: true
  name: kubiya-kubewatch-config
  data:
    .kubewatch.yaml: |
$(sed 's/^/      /' "$CONFIG_PATH")
EOF
)

# Save values to temporary file
VALUES_FILE=$(mktemp)
echo "$HELM_VALUES" > "$VALUES_FILE"

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
        --set image.tag=latest \
        -f "$VALUES_FILE"
    check_command "kubiya-kubewatch installation failed" "Initiated kubiya-kubewatch installation"
else
    # Update existing installation with new config
    log "Updating existing kubiya-kubewatch installation..."
    helm upgrade kubiya-kubewatch robusta/kubewatch \
        --namespace kubiya \
        --reuse-values \
        -f "$VALUES_FILE"
    check_command "kubiya-kubewatch upgrade failed" "Updated kubiya-kubewatch configuration"
fi

# Clean up temporary file
rm -f "$VALUES_FILE"

# Restart the deployment to pick up new config
log "Triggering kubiya-kubewatch restart..."
kubectl rollout restart deployment/kubiya-kubewatch -n kubiya
check_command "restart trigger failed" "Triggered kubiya-kubewatch restart"

log "🎉 Initialization completed successfully"
log "Note: Deployment updates are in progress and may take a few minutes to complete" 