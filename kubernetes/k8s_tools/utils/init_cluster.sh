#!/bin/bash
set -e

# Install yq if not available
if ! command -v yq &> /dev/null; then
    echo "🔧 Installing yq..."
    YQ_VERSION="v4.35.1"
    YQ_BINARY="yq_linux_amd64"
    wget -q https://github.com/mikefarah/yq/releases/download/$YQ_VERSION/$YQ_BINARY -O /usr/local/bin/yq
    chmod +x /usr/local/bin/yq
fi

# Check if KUBIYA_KUBEWATCH_WEBHOOK_URL is set
if [ -z "${KUBIYA_KUBEWATCH_WEBHOOK_URL}" ]; then
    echo "ℹ️ No webhook URL configured - skipping KubeWatch deployment"
    exit 0
fi

# Apply KubeWatch configuration
CONFIG_PATH="$(dirname "$0")/../config/kubewatch.yaml"
if [ ! -f "$CONFIG_PATH" ]; then
    echo "❌ Error: KubeWatch configuration file not found at $CONFIG_PATH"
    exit 1
fi

# Update webhook URL in configuration
yq -i ".handler.webhook.url = \"${KUBIYA_KUBEWATCH_WEBHOOK_URL}\"" "$CONFIG_PATH"

echo "🔄 Applying KubeWatch configuration..."
kubectl apply -f "$CONFIG_PATH"

echo "✅ KubeWatch configuration applied successfully"
echo "🔗 Webhook URL configured: $KUBIYA_KUBEWATCH_WEBHOOK_URL"
