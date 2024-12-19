#!/bin/bash
set -euo pipefail

echo "Cluster Node Status:"
kubectl $KUBECTL_AUTH_ARGS get nodes

echo -e "\nCluster Component Status:"
kubectl $KUBECTL_AUTH_ARGS get componentstatuses

echo -e "\nPods Not Running:"
kubectl $KUBECTL_AUTH_ARGS get pods --all-namespaces --field-selector status.phase!=Running

echo -e "\nEvents (last 1 hour):"
kubectl $KUBECTL_AUTH_ARGS get events --all-namespaces --sort-by=.metadata.creationTimestamp --since=1h