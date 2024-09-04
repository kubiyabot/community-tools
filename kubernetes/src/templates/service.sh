#!/bin/bash
set -euo pipefail

# Sanitize inputs
ACTION=$(echo "$action" | tr '[:upper:]' '[:lower:]')
NAME=$(echo "$name" | sed 's/[^a-zA-Z0-9-]//g')

case "$ACTION" in
  create)
    TYPE=${type:-ClusterIP}
    PORT=${port:-80}
    TARGET_PORT=${target_port:-$PORT}
    kubectl $KUBECTL_AUTH_ARGS --namespace "$NAMESPACE" create service "$TYPE" "$NAME" --tcp="$PORT:$TARGET_PORT" --dry-run=client -o yaml | kubectl apply -f -
    ;;
  delete)
    kubectl $KUBECTL_AUTH_ARGS --namespace "$NAMESPACE" delete service "$NAME"
    ;;
  get)
    kubectl $KUBECTL_AUTH_ARGS --namespace "$NAMESPACE" get service "$NAME" -o yaml
    ;;
  *)
    echo "Error: Invalid action. Supported actions are create, delete, get" >&2
    exit 1
    ;;
esac