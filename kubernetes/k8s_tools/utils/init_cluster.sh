#!/bin/bash
set -e

echo "🚀 Initializing Kubernetes Tools..."

# Install yq if not available
if ! command -v yq &> /dev/null; then
    echo "🔧 Installing yq..."
    YQ_VERSION="v4.35.1"
    YQ_BINARY="yq_linux_amd64"
    
    # Use curl instead of wget
    if ! curl -sSL "https://github.com/mikefarah/yq/releases/download/$YQ_VERSION/$YQ_BINARY" -o /usr/local/bin/yq; then
        echo "❌ Failed to download yq binary"
        exit 1
    fi
    chmod +x /usr/local/bin/yq || {
        echo "❌ Failed to make yq executable"
        exit 1
    }
fi

# Install kubectl if not available
if ! command -v kubectl &> /dev/null; then
    echo "🔧 Installing kubectl..."
    if ! curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"; then
        echo "❌ Failed to download kubectl"
        exit 1
    fi
    chmod +x kubectl || {
        echo "❌ Failed to make kubectl executable"
        exit 1
    }
    mv kubectl /usr/local/bin/ || {
        echo "❌ Failed to move kubectl to /usr/local/bin/"
        exit 1
    }
fi

# Generate KubeWatch configuration if webhook URL is provided
if [ -n "${KUBIYA_KUBEWATCH_WEBHOOK_URL}" ]; then
    echo "🔄 Configuring KubeWatch..."
    
    # Create config directory if it doesn't exist
    CONFIG_DIR="$(dirname "$0")/../config"
    mkdir -p "$CONFIG_DIR"
    
    # Generate base KubeWatch configuration
    cat > "$CONFIG_DIR/kubewatch.yaml" << EOF
version: "1"
filter:
  watch_for: []
  settings:
    dedup_interval: ${DEDUP_WINDOW:-15m}
    include_labels: true
    namespace_isolation: false
    group_by:
      - owner
      - app_label
    log_tail: ${MAX_LOG_LINES:-50}
handler:
  webhook:
    url: "${KUBIYA_KUBEWATCH_WEBHOOK_URL}"
    batchSize: ${BATCH_SIZE:-5}
    maxWaitTime: "${MAX_WAIT_TIME:-30s}"
    minWaitTime: "${MIN_WAIT_TIME:-5s}"
    groupEvents: true
    groupBy:
      - kind
      - namespace
      - reason
      - owner
    filtering:
      includeRoutineEvents: false
      minSeverity: "${MIN_SEVERITY:-Warning}"
      deduplication:
        enabled: true
        window: "${DEDUP_WINDOW:-15m}"
resource:
  pod: ${WATCH_POD:-true}
  node: ${WATCH_NODE:-true}
  deployment: ${WATCH_DEPLOYMENT:-true}
  service: ${WATCH_SERVICE:-false}
  ingress: ${WATCH_INGRESS:-false}
  event: ${WATCH_EVENT:-true}
enrichment:
  include_logs: ${INCLUDE_LOGS:-true}
  include_events: ${INCLUDE_EVENTS:-true}
  include_metrics: ${INCLUDE_METRICS:-true}
  max_log_lines: ${MAX_LOG_LINES:-50}
  max_events: ${MAX_EVENTS:-10}
EOF

    # Add watch configurations using yq
    if [ "${WATCH_POD:-true}" = "true" ]; then
        yq -i '.filter.watch_for += {"kind": "Pod", "reasons": ["*CrashLoopBackOff*", "*OOMKilled*", "*ImagePullBackOff*", "*RunContainerError*", "*Failed*"], "severity": "critical"}' "$CONFIG_DIR/kubewatch.yaml"
    fi

    if [ "${WATCH_NODE:-true}" = "true" ]; then
        yq -i '.filter.watch_for += {"kind": "Node", "reasons": ["*NotReady*", "*DiskPressure*", "*MemoryPressure*", "*NetworkUnavailable*"], "severity": "critical"}' "$CONFIG_DIR/kubewatch.yaml"
    fi

    echo "🔄 Applying KubeWatch configuration..."
    kubectl apply -f "$CONFIG_DIR/kubewatch.yaml"
    echo "✅ KubeWatch configuration applied successfully"
else
    echo "ℹ️ No webhook URL provided - skipping KubeWatch configuration"
fi

echo "✅ Kubernetes Tools initialized successfully!"
