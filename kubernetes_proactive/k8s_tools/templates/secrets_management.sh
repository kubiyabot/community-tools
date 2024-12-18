#!/bin/bash
set -euo pipefail

# Sanitize inputs
ACTION=$(echo "$action" | tr '[:upper:]' '[:lower:]')
NAME=${name:-""}
if [ -n "$NAME" ]; then
  NAME=$(echo "$NAME" | sed 's/[^a-zA-Z0-9-]//g')
fi

case "$ACTION" in
  list)
    # List all secrets across namespaces
    kubectl $KUBECTL_AUTH_ARGS get secrets --all-namespaces
    ;;
    
  decode)
    # Decode a specific secret
    if [ -z "$NAME" ] || [ -z "${NAMESPACE:-}" ]; then
      echo "Error: Both secret name and namespace are required for decode action" >&2
      exit 1
    fi
    kubectl $KUBECTL_AUTH_ARGS get secret "$NAME" -n "$NAMESPACE" -o jsonpath="{.data}" | \
      while IFS= read -r line; do
        echo "$line" | base64 -d
      done
    ;;
    
  unused)
    # Find pods that don't mount secrets
    echo "Finding pods without mounted secrets..."
    kubectl $KUBECTL_AUTH_ARGS get pods --all-namespaces -o json | \
      jq -r '.items[] | select(.spec.volumes[].secret == null) | "\(.metadata.namespace):\(.metadata.name)"'
    ;;
    
  *)
    echo "Error: Invalid action. Supported actions are list, decode, unused" >&2
    exit 1
    ;;
esac
