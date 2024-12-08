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

# Helper function to check if k8s resource exists
resource_exists() {
    local namespace=$1
    local resource_type=$2
    local resource_name=$3
    kubectl get -n "$namespace" "$resource_type" "$resource_name" &> /dev/null
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

# Create ConfigMap
log "Creating ConfigMap..."
if ! resource_exists "kubiya" "configmap" "kubiya-kubewatch-config"; then
    kubectl apply -n kubiya -f - <<EOT
apiVersion: v1
kind: ConfigMap
metadata:
  name: kubiya-kubewatch-config
  labels:
    app.kubernetes.io/name: kubewatch
    app.kubernetes.io/part-of: kubiya
data:
  .kubewatch.yaml: |
$(cat "$CONFIG_PATH" | sed 's/^/    /')
EOT
    check_command "ConfigMap creation failed" "Created ConfigMap"
else
    log "✅ ConfigMap already exists"
fi

# Create ServiceAccount
log "Creating ServiceAccount..."
if ! resource_exists "kubiya" "serviceaccount" "kubiya-kubewatch"; then
    kubectl apply -n kubiya -f - <<EOT
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kubiya-kubewatch
  labels:
    app.kubernetes.io/name: kubewatch
    app.kubernetes.io/part-of: kubiya
automountServiceAccountToken: true
EOT
    check_command "ServiceAccount creation failed" "Created ServiceAccount"
else
    log "✅ ServiceAccount already exists"
fi

# Create Deployment
log "Creating Deployment..."
if ! resource_exists "kubiya" "deployment" "kubiya-kubewatch"; then
    kubectl apply -n kubiya -f - <<EOT
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubiya-kubewatch
  labels:
    app.kubernetes.io/name: kubewatch
    app.kubernetes.io/part-of: kubiya
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: kubewatch
      app.kubernetes.io/part-of: kubiya
  replicas: 1
  strategy:
    type: RollingUpdate
  template:
    metadata:
      labels:
        app.kubernetes.io/name: kubewatch
        app.kubernetes.io/part-of: kubiya
    spec:
      serviceAccountName: kubiya-kubewatch
      containers:
        - name: kubewatch
          image: ghcr.io/kubiyabot/kubewatch:main
          imagePullPolicy: IfNotPresent
          resources:
            limits:
              cpu: 100m
              memory: 128Mi
            requests:
              cpu: 50m
              memory: 64Mi
          volumeMounts:
            - name: config-volume
              mountPath: /opt/bitnami/kubewatch/conf
              readOnly: true
      volumes:
        - name: config-volume
          configMap:
            name: kubiya-kubewatch-config
EOT
    check_command "Deployment creation failed" "Created Deployment"
else
    log "✅ Deployment already exists"
fi

# Restart the deployment to pick up new config
log "Triggering kubiya-kubewatch restart..."
kubectl rollout restart deployment/kubiya-kubewatch -n kubiya
check_command "restart trigger failed" "Triggered kubiya-kubewatch restart"

log "🎉 Initialization completed successfully"
log "Note: Deployment updates are in progress and may take a few minutes to complete"
