#!/bin/bash
set -euo pipefail

# Sanitize inputs
ACTION=$(echo "$action" | tr '[:upper:]' '[:lower:]')
NAME=$(echo "$name" | sed 's/[^a-zA-Z0-9-]//g')

case "$ACTION" in
  get)
    kubectl $KUBECTL_AUTH_ARGS --namespace "$NAMESPACE" get pod "$NAME" -o yaml
    ;;
  delete)
    kubectl $KUBECTL_AUTH_ARGS --namespace "$NAMESPACE" delete pod "$NAME"
    ;;
  logs)
    if [ -n "${container:-}" ]; then
      CONTAINER=$(echo "$container" | sed 's/[^a-zA-Z0-9-]//g')
      kubectl $KUBECTL_AUTH_ARGS --namespace "$NAMESPACE" logs "$NAME" -c "$CONTAINER"
    else
      kubectl $KUBECTL_AUTH_ARGS --namespace "$NAMESPACE" logs "$NAME"
    fi
    ;;
  *)
    echo "Error: Invalid action. Supported actions are get, delete, logs" >&2
    exit 1
    ;;
esac