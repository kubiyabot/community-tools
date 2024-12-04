#!/bin/bash
set -euo pipefail

# Sanitize inputs
ACTION=$(echo "$action" | tr '[:upper:]' '[:lower:]')
NAME=$(echo "$name" | sed 's/[^a-zA-Z0-9-]//g')

case "$ACTION" in
  create)
    # Create secret from literal values if provided
    if [ -n "${from_literal:-}" ]; then
      kubectl $KUBECTL_AUTH_ARGS create secret generic "$NAME" \
        --namespace "$NAMESPACE" \
        --from-literal="$from_literal"
    fi

    # Create secret from files if provided
    if [ -n "${from_file:-}" ]; then
      kubectl $KUBECTL_AUTH_ARGS create secret generic "$NAME" \
        --namespace "$NAMESPACE" \
        --from-file="$from_file"
    fi

    # Create secret from env file if provided
    if [ -n "${from_env_file:-}" ]; then
      kubectl $KUBECTL_AUTH_ARGS create secret generic "$NAME" \
        --namespace "$NAMESPACE" \
        --from-env-file="$from_env_file"
    fi
    ;;

  delete)
    kubectl $KUBECTL_AUTH_ARGS --namespace "$NAMESPACE" delete secret "$NAME"
    ;;

  get)
    kubectl $KUBECTL_AUTH_ARGS --namespace "$NAMESPACE" get secret "$NAME" -o yaml
    ;;

  *)
    echo "Error: Invalid action. Supported actions are create, delete, get" >&2
    exit 1
    ;;
esac