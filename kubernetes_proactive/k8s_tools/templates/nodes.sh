#!/bin/bash
set -euo pipefail

# Sanitize inputs
ACTION=$(echo "$action" | tr '[:upper:]' '[:lower:]')
NAME=${name:-""}
if [ -n "$NAME" ]; then
  NAME=$(echo "$NAME" | sed 's/[^a-zA-Z0-9-]//g')
fi

case "$ACTION" in
  get)
    if [ -n "$NAME" ]; then
      kubectl $KUBECTL_AUTH_ARGS get node "$NAME" -o yaml
    else
      kubectl $KUBECTL_AUTH_ARGS get nodes
    fi
    ;;
  describe)
    if [ -z "$NAME" ]; then
      echo "Error: Node name is required for describe action" >&2
      exit 1
    fi
    kubectl $KUBECTL_AUTH_ARGS describe node "$NAME"
    ;;
  cordon)
    if [ -z "$NAME" ]; then
      echo "Error: Node name is required for cordon action" >&2
      exit 1
    fi
    kubectl $KUBECTL_AUTH_ARGS cordon "$NAME"
    ;;
  uncordon)
    if [ -z "$NAME" ]; then
      echo "Error: Node name is required for uncordon action" >&2
      exit 1
    fi
    kubectl $KUBECTL_AUTH_ARGS uncordon "$NAME"
    ;;
  drain)
    if [ -z "$NAME" ]; then
      echo "Error: Node name is required for drain action" >&2
      exit 1
    fi
    kubectl $KUBECTL_AUTH_ARGS drain "$NAME" --ignore-daemonsets --delete-emptydir-data
    ;;
  *)
    echo "Error: Invalid action. Supported actions are get, describe, cordon, uncordon, drain" >&2
    exit 1
    ;;
esac
