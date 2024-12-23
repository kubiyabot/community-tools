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

# Install required tools if needed
for cmd in curl kubectl; do
    if ! command -v $cmd &> /dev/null; then
        log "Installing $cmd..."
        case $cmd in
            curl)
                rm -rf /var/lib/apt/lists/*
                apt-get clean
                apt-get update -y
                DEBIAN_FRONTEND=noninteractive apt-get install -y curl
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

# Clean up existing deployment
log "Cleaning up existing deployment..."
if kubectl get deployment enforcer -n kubiya &> /dev/null; then
    kubectl delete deployment enforcer -n kubiya
    check_command "Failed to remove existing deployment" "Existing deployment removed"
fi
if kubectl get secret opawatchdog-secrets -n kubiya &> /dev/null; then
    kubectl delete secret opawatchdog-secrets -n kubiya
fi

# Build base secret data
SECRET_DATA=$(cat <<EOF
  POSTGRES_DB: cG9zdGdyZXM=
  POSTGRES_USER: cG9zdGdyZXM=
  POSTGRES_PASSWORD: cG9zdGdyZXM=
  OPAL_POLICY_REPO_URL: $OPAL_POLICY_REPO_URL_B64
  OPAL_POLICY_REPO_MAIN_BRANCH: $OPAL_POLICY_REPO_MAIN_BRANCH_B64
EOF
)

# Add DataDog API key if provided
if [ ! -z "$DATA_DOG_API_KEY_BASE64" ]; then
    SECRET_DATA+=$(cat <<EOF

  DD_API_KEY: $DATA_DOG_API_KEY_BASE64
EOF
)
    log "✅ Added DD_API_KEY to configuration"
fi

# Add DataDog site if provided
if [ ! -z "$DATA_DOG_SITE_BASE64" ]; then
    SECRET_DATA+=$(cat <<EOF

  DD_SITE: $DATA_DOG_SITE_BASE64
EOF
)
    log "✅ Added DD_SITE to configuration"
fi

# Initialize enforcer environment variables
if [ "$IDP_PROVIDER" = "okta" ]; then
    SECRET_DATA+=$(cat <<EOF

  OKTA_BASE_URL: $OKTA_BASE_URL_B64
  OKTA_TOKEN_ENDPOINT: $OKTA_TOKEN_ENDPOINT_B64
  OKTA_CLIENT_ID: $OKTA_CLIENT_ID_B64
  private.pem: $PRIVATE_KEY_B64
EOF
)
    log "✅ Added Okta configuration"
    
    ENFORCER_ENV="          env:
            - name: OKTA_BASE_URL
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: OKTA_BASE_URL
            - name: OKTA_TOKEN_ENDPOINT
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: OKTA_TOKEN_ENDPOINT
            - name: OKTA_CLIENT_ID
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: OKTA_CLIENT_ID
            - name: OKTA_PRIVATE_KEY
              value: /etc/okta/private.pem
            - name: IDP_PROVIDER_NAME
              value: okta"
              
    if [ ! -z "$DATA_DOG_API_KEY_BASE64" ]; then
        ENFORCER_ENV+="
            - name: DD_API_KEY
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: DD_API_KEY"
    fi
    
    if [ ! -z "$DATA_DOG_SITE_BASE64" ]; then
        ENFORCER_ENV+="
            - name: DD_SITE
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: DD_SITE"
    fi
    
    ENFORCER_VOLUME_MOUNTS="          volumeMounts:
            - name: private-key-volume
              mountPath: /etc/okta/private.pem
              subPath: private.pem"
              
    ENFORCER_VOLUMES="      volumes:
        - name: private-key-volume
          secret:
            secretName: opawatchdog-secrets"
else
    ENFORCER_ENV="          env:
            - name: IDP_PROVIDER_NAME
              value: kubiya"
              
    if [ ! -z "$DATA_DOG_API_KEY_BASE64" ]; then
        ENFORCER_ENV+="
            - name: DD_API_KEY
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: DD_API_KEY"
    fi
    
    if [ ! -z "$DATA_DOG_SITE_BASE64" ]; then
        ENFORCER_ENV+="
            - name: DD_SITE
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: DD_SITE"
    fi
    
    ENFORCER_VOLUME_MOUNTS=""
    ENFORCER_VOLUMES=""
fi

# Build OPA server environment variables
OPA_ENV="            - name: OPAL_BROADCAST_URI
              value: postgres://postgres:postgres@localhost:5432/postgres
            - name: UVICORN_NUM_WORKERS
              value: \"4\"
            - name: OPAL_OPA_HEALTH_CHECK_POLICY_ENABLED
              value: \"true\"
            - name: OPAL_POLICY_REPO_URL
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: OPAL_POLICY_REPO_URL
            - name: OPAL_POLICY_REPO_MAIN_BRANCH
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: OPAL_POLICY_REPO_MAIN_BRANCH"

# Add Git deploy key to OPA server if provided
if [ ! -z "$GIT_DEPLOY_KEY_BS64" ]; then
    SECRET_DATA+=$(cat <<EOF

  GIT_DEPLOY_KEY: $GIT_DEPLOY_KEY_BS64
EOF
)
    OPA_ENV+="
            - name: OPAL_POLICY_REPO_SSH_KEY
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: GIT_DEPLOY_KEY"
    log "✅ Added Git deploy key to OPA configuration"
fi

# Add remaining OPA configuration
OPA_ENV+="
            - name: OPAL_POLICY_REPO_POLLING_INTERVAL
              value: \"30\"
            - name: OPAL_DATA_CONFIG_SOURCES
              value: '{\"config\":{\"entries\":[{\"url\":\"http://localhost:7002/policy-data\",\"topics\":[\"policy_data\"],\"dst_path\":\"/static\"}]}}'
            - name: OPAL_LOG_FORMAT_INCLUDE_PID
              value: \"true\""

# Deploy configuration
log "Deploying Enforcer components..."

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: opawatchdog-secrets
  namespace: kubiya
type: Opaque
data:
$SECRET_DATA
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
$OPA_ENV
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
$ENFORCER_ENV
          ports:
            - containerPort: 5001
$ENFORCER_VOLUME_MOUNTS
$ENFORCER_VOLUMES
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

# Update tool-manager deployment with auth server URL
log "Updating tool-manager with auth server URL..."
kubectl patch deployment tool-manager -n kubiya --type=json -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/env/-",
    "value": {
      "name": "KUBIYA_AUTH_SERVER_URL",
      "value": "http://enforcer.kubiya:5001"
    }
  }
]'
check_command "Failed to patch tool-manager deployment" "Tool manager updated successfully"

log "✅ Enforcer deployment completed successfully!"