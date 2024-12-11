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

# Install required tools
for cmd in curl yq kubectl; do
    if ! command -v $cmd &> /dev/null; then
        log "Installing $cmd..."
        case $cmd in
            curl)
                apt-get update && apt-get install -y curl
                ;;
            yq)
                YQ_VERSION="v4.35.1"
                YQ_BINARY="yq_linux_amd64"
                curl -sSL "https://github.com/mikefarah/yq/releases/download/$YQ_VERSION/$YQ_BINARY" -o "/usr/local/bin/yq"
                chmod +x "/usr/local/bin/yq"
                ;;
            kubectl)
                curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                chmod +x kubectl
                mv kubectl /usr/local/bin/
                ;;
        esac
        check_command "$cmd installation failed" "$cmd installed successfully"
    else
        log "✅ $cmd is already installed"
    fi
done

# Test kubectl connection
log "Testing kubectl connection..."
if ! kubectl cluster-info &> /dev/null; then
    log "❌ Error: Cannot connect to Kubernetes cluster"
    exit 1
fi
check_command "cluster connection failed" "Connected to Kubernetes cluster"

# Process KubeWatch configuration if webhook URL is provided
if [ -n "${KUBIYA_KUBEWATCH_WEBHOOK_URL}" ]; then
    log "🔄 Configuring KubeWatch..."
    
    # Use /tmp for all files
    JSON_FILE="${KUBEWATCH_CONFIG_PATH:-/tmp/kubewatch.json}"
    YAML_FILE="/tmp/kubewatch.yaml"
    
    # Convert JSON to YAML using yq
    log "📝 Converting configuration to YAML..."
    if [ ! -f "$JSON_FILE" ]; then
        log "❌ JSON configuration file not found at: $JSON_FILE"
        exit 1
    fi
    
    # Use yq to read JSON and output as YAML
    yq eval -P "$JSON_FILE" > "$YAML_FILE" || {
        log "❌ Failed to convert JSON to YAML"
        log "JSON content:"
        cat "$JSON_FILE"
        exit 1
    }
    
    # Create namespace if it doesn't exist
    log "Setting up kubiya namespace..."
    if ! kubectl get namespace kubiya &> /dev/null; then
        kubectl create namespace kubiya
        check_command "namespace creation failed" "Created kubiya namespace"
    else
        log "✅ Kubiya namespace already exists"
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

    # Create ClusterRole
    log "Creating ClusterRole..."
    if ! resource_exists "" "clusterrole" "kubiya-kubewatch"; then
        kubectl apply -f - <<EOT
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kubiya-kubewatch
  labels:
    app.kubernetes.io/name: kubewatch
    app.kubernetes.io/part-of: kubiya
rules:
  - apiGroups: [""]
    resources: ["pods", "nodes", "services", "deployments", "events", "configmaps"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "daemonsets", "statefulsets", "replicasets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["batch"]
    resources: ["jobs", "cronjobs"]
    verbs: ["get", "list", "watch"]
EOT
        check_command "ClusterRole creation failed" "Created ClusterRole"
    else
        log "✅ ClusterRole already exists"
    fi

    # Create ClusterRoleBinding
    log "Creating ClusterRoleBinding..."
    if ! resource_exists "" "clusterrolebinding" "kubiya-kubewatch"; then
        kubectl apply -f - <<EOT
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: kubiya-kubewatch
  labels:
    app.kubernetes.io/name: kubewatch
    app.kubernetes.io/part-of: kubiya
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kubiya-kubewatch
subjects:
- kind: ServiceAccount
  name: kubiya-kubewatch
  namespace: kubiya
EOT
        check_command "ClusterRoleBinding creation failed" "Created ClusterRoleBinding"
    else
        log "✅ ClusterRoleBinding already exists"
    fi

    # Apply ConfigMap
    log "Applying KubeWatch ConfigMap..."
    kubectl apply -f "$YAML_FILE" || {
        log "❌ Failed to apply KubeWatch configuration"
        log "Configuration content:"
        cat "$YAML_FILE"
        exit 1
    }
    check_command "ConfigMap creation failed" "Created ConfigMap"

    # Create/Update Deployment
    log "Creating/Updating KubeWatch Deployment..."
    kubectl apply -n kubiya -f - <<EOT
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubiya-kubewatch
  namespace: kubiya
  labels:
    app.kubernetes.io/name: kubewatch
    app.kubernetes.io/part-of: kubiya
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: kubewatch
  template:
    metadata:
      labels:
        app.kubernetes.io/name: kubewatch
    spec:
      serviceAccountName: kubiya-kubewatch
      containers:
      - name: kubewatch
        image: ghcr.io/kubiyabot/kubewatch:main
        imagePullPolicy: Always
        args: ["run", "--config", "/config/.kubewatch.yaml"]
        volumeMounts:
        - name: config
          mountPath: /config
      env:
      - name: KUBIYA_KUBEWATCH_WEBHOOK_URL
        value: ${KUBIYA_KUBEWATCH_WEBHOOK_URL}
      volumes:
      - name: config
        configMap:
          name: kubewatch-config
EOT
    check_command "Deployment creation/update failed" "Created/Updated Deployment"

    # Wait for deployment to be ready
    log "Waiting for KubeWatch deployment to be ready..."
    kubectl rollout status deployment/kubiya-kubewatch -n kubiya
    check_command "Deployment rollout failed" "KubeWatch deployment is ready"

    log "✅ KubeWatch configuration applied successfully - events will be sent to the configured webhook"
else
    log "ℹ️ No webhook URL provided - skipping KubeWatch configuration"
fi

log "✅ Kubernetes Tools initialized successfully!"
