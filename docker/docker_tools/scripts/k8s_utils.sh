#!/bin/sh

# Function to check if we're running in Kubernetes
is_running_in_k8s() {
    [ -n "$KUBERNETES_SERVICE_HOST" ] && [ -n "$KUBERNETES_SERVICE_PORT" ]
}

# Function to setup kubectl configuration
setup_kubectl() {
    if [ ! -f "/var/run/secrets/kubernetes.io/serviceaccount/token" ]; then
        log "❌" "Kubernetes service account token not found"
        return 1
    }

    # Create kubeconfig
    mkdir -p ~/.kube
    cat > ~/.kube/config <<EOF
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    server: https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}
  name: default
contexts:
- context:
    cluster: default
    user: default
  name: default
current-context: default
users:
- name: default
  user:
    token: $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
EOF

    # Test kubectl
    if ! kubectl get ns >/dev/null 2>&1; then
        log "❌" "Failed to configure kubectl"
        return 1
    fi
    
    log "✅" "kubectl configured successfully"
    return 0
}

# Function to find Dagger engine pod
find_dagger_engine() {
    local namespace="${KUBIYA_NAMESPACE:-default}"
    
    log "🔍" "Looking for Dagger engine pod in namespace: $namespace"
    
    # Look for the Dagger engine pod
    local engine_pod
    engine_pod=$(kubectl -n "$namespace" get pods -l app=dagger-engine -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$engine_pod" ]; then
        log "❌" "No Dagger engine pod found"
        return 1
    fi
    
    # Get pod status
    local pod_status
    pod_status=$(kubectl -n "$namespace" get pod "$engine_pod" -o jsonpath='{.status.phase}')
    
    if [ "$pod_status" != "Running" ]; then
        log "❌" "Dagger engine pod found but not running (status: $pod_status)"
        return 1
    }
    
    # Export the pod name
    export DAGGER_ENGINE_POD="$engine_pod"
    log "✅" "Found Dagger engine pod: $engine_pod"
    
    return 0
}

# Function to setup port forwarding to Dagger engine
setup_dagger_connection() {
    if [ -z "$DAGGER_ENGINE_POD" ]; then
        log "❌" "No Dagger engine pod specified"
        return 1
    }
    
    local namespace="${KUBIYA_NAMESPACE:-default}"
    local port="${DAGGER_ENGINE_PORT:-1234}"
    
    # Setup port forwarding in the background
    log "🔌" "Setting up port forwarding to Dagger engine"
    kubectl -n "$namespace" port-forward "$DAGGER_ENGINE_POD" "$port:1234" >/dev/null 2>&1 &
    
    # Wait for port forwarding to be ready
    local retries=10
    while ! nc -z localhost "$port" 2>/dev/null; do
        retries=$((retries - 1))
        if [ "$retries" -eq 0 ]; then
            log "❌" "Failed to establish port forwarding to Dagger engine"
            return 1
        fi
        sleep 1
    done
    
    export DAGGER_HOST="tcp://localhost:$port"
    log "✅" "Connected to Dagger engine"
    
    return 0
} 