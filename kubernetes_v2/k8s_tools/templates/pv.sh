#!/bin/bash
set -euo pipefail

# Sanitize inputs
ACTION=$(echo "$action" | tr '[:upper:]' '[:lower:]')
NAME=$(echo "$name" | sed 's/[^a-zA-Z0-9-]//g')

case "$ACTION" in
  create)
    SIZE=${size:-1Gi}
    STORAGE_CLASS=${storage_class:-standard}
    ACCESS_MODE=${access_mode:-ReadWriteOnce}
    
    cat <<EOF | kubectl $KUBECTL_AUTH_ARGS apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: $NAME
spec:
  capacity:
    storage: $SIZE
  accessModes:
    - $ACCESS_MODE
  storageClassName: $STORAGE_CLASS
  hostPath:
    path: /data/$NAME
EOF
    ;;
  delete)
    kubectl $KUBECTL_AUTH_ARGS delete pv "$NAME"
    ;;
  get)
    kubectl $KUBECTL_AUTH_ARGS get pv "$NAME" -o yaml
    ;;
  *)
    echo "Error: Invalid action. Supported actions are create, delete, get" >&2
    exit 1
    ;;
esac