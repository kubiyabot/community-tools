#!/bin/bash
set -euo pipefail

# Sanitize inputs
ACTION=$(echo "$action" | tr '[:upper:]' '[:lower:]')
NAME=$(echo "$name" | sed 's/[^a-zA-Z0-9-]//g')

case "$ACTION" in
  create|update)
    if [ -z "${image:-}" ]; then
      echo "Error: 'image' is required for create/update actions" >&2
      exit 1
    fi
    IMAGE=$(echo "$image" | sed 's/[^a-zA-Z0-9.:-_/]//g')
    REPLICAS=${replicas:-1}
    kubectl $KUBECTL_AUTH_ARGS --namespace "$NAMESPACE" create deployment "$NAME" --image="$IMAGE" --replicas="$REPLICAS" --dry-run=client -o yaml | kubectl apply -f -
    ;;
  delete)
    kubectl $KUBECTL_AUTH_ARGS --namespace "$NAMESPACE" delete deployment "$NAME"
    ;;
  get)
    kubectl $KUBECTL_AUTH_ARGS --namespace "$NAMESPACE" get deployment "$NAME" -o yaml
    ;;
  *)
    echo "Error: Invalid action. Supported actions are create, update, delete, get" >&2
    exit 1
    ;;
esac