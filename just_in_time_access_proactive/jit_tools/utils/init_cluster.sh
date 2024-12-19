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

# Helper function to check if resource exists
resource_exists() {
    local namespace=$1
    local resource_type=$2
    local resource_name=$3
    kubectl get -n "$namespace" "$resource_type" "$resource_name" &> /dev/null
}

log "🚀 Initializing Enforcer tools..."

# Install required tools
for cmd in curl kubectl; do
    if ! command -v $cmd &> /dev/null; then
        log "Installing $cmd..."
        case $cmd in
            curl)
                apt-get update && apt-get install -y curl
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

# Test cluster connection
log "Testing cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    log "❌ Error: Cannot connect to cluster"
    exit 1
fi
check_command "cluster connection failed" "Connected to cluster"

# Create namespace if it doesn't exist
log "Setting up kubiya namespace..."
if ! kubectl get namespace kubiya &> /dev/null; then
    kubectl create namespace kubiya
    check_command "namespace creation failed" "Created kubiya namespace"
else
    log "✅ Kubiya namespace already exists"
fi

# Deploy Enforcer components
log "Deploying Enforcer components..."

# Create and apply resources
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: opawatchdog-secrets
  namespace: kubiya
type: Opaque
data:
  POSTGRES_DB: cG9zdGdyZXM=
  POSTGRES_USER: cG9zdGdyZXM=
  POSTGRES_PASSWORD: cG9zdGdyZXM=
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enforcer
  namespace: kubiya
spec:
  replicas: 1
  selector:
    matchLabels:
      app: enforcer
  template:
    metadata:
      labels:
        app: enforcer
    spec:
      containers:
        - name: broadcast-kubiya
          image: postgres:alpine
          env:
            - name: POSTGRES_DB
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: POSTGRES_DB
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: POSTGRES_PASSWORD
          ports:
            - containerPort: 5432
        - name: opa-server-kubiya
          image: permitio/opal-server:latest
          env:
            - name: OPAL_BROADCAST_URI
              value: postgres://postgres:postgres@localhost:5432/postgres
            - name: UVICORN_NUM_WORKERS
              value: "4"
            - name: OPAL_OPA_HEALTH_CHECK_POLICY_ENABLED
              value: "true"
            - name: OPAL_POLICY_REPO_POLLING_INTERVAL
              value: "30"
            - name: OPAL_DATA_CONFIG_SOURCES
              value: '{"config":{"entries":[{"url":"http://localhost:7002/policy-data","topics":["policy_data"],"dst_path":"/static"}]}}'
            - name: OPAL_LOG_FORMAT_INCLUDE_PID
              value: "true"
          ports:
            - containerPort: 7002
        - name: opal-client-kubiya
          image: permitio/opal-client:latest
          env:
            - name: OPAL_SERVER_URL
              value: http://localhost:7002
            - name: OPAL_LOG_FORMAT_INCLUDE_PID
              value: "true"
            - name: OPAL_INLINE_OPA_LOG_FORMAT
              value: http
          ports:
            - containerPort: 7000
            - containerPort: 8181
          command: ["sh", "-c", "./wait-for.sh localhost:7002 --timeout=20 -- ./start.sh"]
        - name: enforcer
          image: ghcr.io/kubiyabot/opawatchdog
          env:
            - name: IDP_PROVIDER_NAME
              value: kubiya
            - name: OKTA_BASE_URL
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: OKTA_BASE_URL
                  optional: true
            - name: OKTA_TOKEN_ENDPOINT
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: OKTA_TOKEN_ENDPOINT
                  optional: true
            - name: OKTA_CLIENT_ID
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: OKTA_CLIENT_ID
                  optional: true
            - name: OKTA_PRIVATE_KEY
              value: /etc/okta/private.pem
          ports:
            - containerPort: 5001
          volumeMounts:
            - name: private-key-volume
              mountPath: /etc/okta
              readOnly: true
      volumes:
        - name: private-key-volume
          secret:
            secretName: opawatchdog-secrets
            items:
              - key: OKTA_PRIVATE_KEY
                path: private.pem
---
apiVersion: v1
kind: Service
metadata:
  name: enforcer
  namespace: kubiya
spec:
  ports:
    - name: enforcer
      port: 5001
      targetPort: 5001
  selector:
    app: enforcer
EOF

check_command "Failed to apply Enforcer resources" "Applied Enforcer resources successfully"

# Wait for deployment to be ready
log "Waiting for enforcer deployment to be ready..."
kubectl rollout status deployment/enforcer -n kubiya
check_command "Deployment rollout failed" "Enforcer deployment is ready"

log "✅ Enforcer deployment completed successfully!"