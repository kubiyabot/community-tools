from typing import List
from .base import CrossplaneTool, Arg

class ProviderManager(CrossplaneTool):
    """Manage Crossplane providers."""
    
    def __init__(self):
        super().__init__(
            name="crossplane_provider",
            description="Manage Crossplane providers and their configurations",
            content="",
            args=[],
            image="bitnami/kubectl:latest"
        )

    def install_provider(self) -> CrossplaneTool:
        """Install a Crossplane provider."""
        return CrossplaneTool(
            name="install_provider",
            description="Install a Crossplane provider",
            content="""
            if [ -z "$PROVIDER_PACKAGE" ]; then
                echo "Error: Provider package not specified"
                exit 1
            fi

            # Install the provider
            cat <<EOF | kubectl apply -f -
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: ${PROVIDER_PACKAGE##*/}
spec:
  package: $PROVIDER_PACKAGE
EOF

            # Wait for provider to be healthy
            PROVIDER_NAME=$(echo $PROVIDER_PACKAGE | cut -d "/" -f2 | cut -d ":" -f1)
            kubectl wait --for=condition=healthy provider.pkg.crossplane.io/$PROVIDER_NAME --timeout=300s
            """,
            args=[
                Arg("provider_package", 
                    description="The provider package to install (e.g., crossplane/provider-aws:v0.24.1)",
                    required=True)
            ],
            image="bitnami/kubectl:latest"
        )

    def configure_provider(self) -> CrossplaneTool:
        """Configure a Crossplane provider with credentials."""
        return CrossplaneTool(
            name="configure_provider",
            description="Configure a Crossplane provider with credentials",
            content="""
            if [ -z "$PROVIDER_CONFIG" ]; then
                echo "Error: Provider config file not specified"
                exit 1
            fi

            # Apply the provider configuration
            kubectl apply -f $PROVIDER_CONFIG

            # Verify the configuration
            PROVIDER_CONFIG_NAME=$(yq e '.metadata.name' $PROVIDER_CONFIG)
            kubectl get providerconfig $PROVIDER_CONFIG_NAME -o yaml
            """,
            args=[
                Arg("provider_config",
                    description="Path to the provider configuration file",
                    required=True)
            ],
            image="mikefarah/yq:4"  # Using yq for YAML processing
        )

    def list_providers(self) -> CrossplaneTool:
        """List installed Crossplane providers."""
        return CrossplaneTool(
            name="list_providers",
            description="List installed Crossplane providers",
            content="""
            echo "=== Installed Providers ==="
            kubectl get providers.pkg.crossplane.io -o wide

            echo "\n=== Provider Revisions ==="
            kubectl get providerrevisions.pkg.crossplane.io

            echo "\n=== Provider Configs ==="
            kubectl get providerconfigs --all-namespaces
            """,
            args=[],
            image="bitnami/kubectl:latest"
        )

    def get_provider_status(self) -> CrossplaneTool:
        """Get detailed status of a specific provider."""
        return CrossplaneTool(
            name="get_provider_status",
            description="Get detailed status of a specific provider",
            content="""
            if [ -z "$PROVIDER_NAME" ]; then
                echo "Error: Provider name not specified"
                exit 1
            fi

            echo "=== Provider Status ==="
            kubectl describe provider.pkg.crossplane.io $PROVIDER_NAME

            echo "\n=== Provider Controller Pods ==="
            kubectl get pods -l pkg.crossplane.io/provider=$PROVIDER_NAME -A

            echo "\n=== Provider Events ==="
            kubectl get events --field-selector involvedObject.kind=Provider,involvedObject.name=$PROVIDER_NAME --sort-by='.lastTimestamp'
            """,
            args=[
                Arg("provider_name",
                    description="Name of the provider to check",
                    required=True)
            ],
            image="bitnami/kubectl:latest"
        )

    def uninstall_provider(self) -> CrossplaneTool:
        """Uninstall a Crossplane provider."""
        return CrossplaneTool(
            name="uninstall_provider",
            description="Uninstall a Crossplane provider",
            content="""
            if [ -z "$PROVIDER_NAME" ]; then
                echo "Error: Provider name not specified"
                exit 1
            fi

            # Delete provider configurations first
            echo "Deleting provider configurations..."
            kubectl get providerconfigs.${PROVIDER_NAME#provider-}.crossplane.io --no-headers 2>/dev/null | awk '{print $1}' | xargs -r kubectl delete providerconfig

            # Delete the provider
            echo "Deleting provider..."
            kubectl delete provider.pkg.crossplane.io $PROVIDER_NAME

            # Clean up provider CRDs
            echo "Cleaning up provider CRDs..."
            kubectl get crds -o name | grep "${PROVIDER_NAME#provider-}.crossplane.io" | xargs -r kubectl delete
            """,
            args=[
                Arg("provider_name",
                    description="Name of the provider to uninstall",
                    required=True)
            ],
            image="bitnami/kubectl:latest"
        ) 