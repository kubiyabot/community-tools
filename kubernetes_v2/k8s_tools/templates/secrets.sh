#!/bin/bash
set -euo pipefail

# Sanitize inputs
ACTION=$(echo "$action" | tr '[:upper:]' '[:lower:]')
NAME=$(echo "$name" | sed 's/[^a-zA-Z0-9-]//g')

case "$ACTION" in
  create)
    # Create secret YAML and apply it
    cat <<EOF | kubectl $KUBECTL_AUTH_ARGS apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: $NAME
  namespace: $NAMESPACE
type: Opaque
data:
EOF

    # Add literal data if provided
    if [ -n "${from_literal:-}" ]; then
      # Split key-value pairs and add to YAML
      IFS=',' read -ra PAIRS <<< "$from_literal"
      for PAIR in "${PAIRS[@]}"; do
        KEY="${PAIR%%=*}"
        VALUE="${PAIR#*=}"
        echo "  $KEY: $(echo -n "$VALUE" | base64)" | kubectl $KUBECTL_AUTH_ARGS apply -f -
      done
    fi

    # Add file contents if provided
    if [ -n "${from_file:-}" ]; then
      # Split multiple files if provided
      IFS=',' read -ra FILES <<< "$from_file"
      for FILE in "${FILES[@]}"; do
        KEY=$(basename "$FILE")
        echo "  $KEY: $(cat "$FILE" | base64)" | kubectl $KUBECTL_AUTH_ARGS apply -f -
      done
    fi

    # Add env file contents if provided
    if [ -n "${from_env_file:-}" ]; then
      while IFS='=' read -r KEY VALUE; do
        # Skip comments and empty lines
        [[ $KEY =~ ^#.*$ ]] || [ -z "$KEY" ] && continue
        echo "  $KEY: $(echo -n "$VALUE" | base64)" | kubectl $KUBECTL_AUTH_ARGS apply -f -
      done < "$from_env_file"
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