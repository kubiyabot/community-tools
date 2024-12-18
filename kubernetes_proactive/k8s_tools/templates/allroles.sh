#!/bin/bash
set -euo pipefail

# Sanitize inputs
ACTION=$(echo "$action" | tr '[:upper:]' '[:lower:]')

case "$ACTION" in
  clusterrolebindings)
    kubectl $KUBECTL_AUTH_ARGS get clusterrolebindings
    ;;
  rolebindings)
    if [ -z "${namespace:-}" ]; then
      echo "Error: Namespace is required for rolebindings action" >&2
      exit 1
    fi
    kubectl $KUBECTL_AUTH_ARGS get rolebindings -n "$namespace"
    ;;
  permissions)
    kubectl $KUBECTL_AUTH_ARGS get roles,clusterroles --all-namespaces -o yaml | grep -B 5 -A 5 '*'
    ;;
  *)
    echo "Error: Invalid action. Supported actions are clusterrolebindings, rolebindings, permissions" >&2
    exit 1
    ;;
esac
