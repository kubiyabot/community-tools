#!/bin/bash
set -e

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

echo "🔄 Applying KubeWatch configuration..."
kubectl apply -f "$CONFIG_PATH"

echo "✅ KubeWatch configuration applied successfully"
echo "🔗 Webhook URL configured: $KUBIYA_KUBEWATCH_WEBHOOK_URL"
