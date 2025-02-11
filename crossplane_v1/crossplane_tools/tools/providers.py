"""Provider Tools

This module provides tools for managing Crossplane providers.
"""
from typing import List
from .base import CrossplaneTool, Arg, Secret
import logging

logger = logging.getLogger(__name__)

# Provider installation tool
install_provider_tool = CrossplaneTool(
    name="install_provider",
    description="Install a Crossplane provider",
    content="""
    if [ -z "$PROVIDER" ]; then
        echo "Error: Provider not specified"
        exit 1
    fi

    # Install provider
    cat <<EOF | kubectl apply -f -
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: ${PROVIDER}
spec:
  package: ${PACKAGE:-xpkg.upbound.io/crossplane-contrib/provider-${PROVIDER}:v1.0.0}
  ${REVISION_ACTIVATION_POLICY:+revisionActivationPolicy: $REVISION_ACTIVATION_POLICY}
  ${REVISION_HISTORY_LIMIT:+revisionHistoryLimit: $REVISION_HISTORY_LIMIT}
  ${PACKAGE_PULL_SECRETS:+packagePullSecrets: $PACKAGE_PULL_SECRETS}
  ${SKIP_DEPENDENCY_RESOLUTION:+skipDependencyResolution: $SKIP_DEPENDENCY_RESOLUTION}
EOF

    if [ "$WAIT" = "true" ]; then
        echo "Waiting for provider to be ready..."
        kubectl wait --for=condition=healthy provider.pkg.crossplane.io/${PROVIDER} --timeout=${TIMEOUT:-300s}
    fi

    if [ "$VERIFY" = "true" ]; then
        echo "\\nVerifying provider installation..."
        kubectl get provider.pkg.crossplane.io ${PROVIDER} -o yaml
    fi
    """,
    args=[
        Arg(name="provider", description="Name of the provider to install", required=True),
        Arg(name="package", description="Provider package URL", required=False),
        Arg(name="revision_activation_policy", description="Policy for activating provider revisions", required=False),
        Arg(name="revision_history_limit", description="Number of old revisions to retain", required=False),
        Arg(name="package_pull_secrets", description="Secrets for pulling private packages", required=False),
        Arg(name="skip_dependency_resolution", description="Skip resolving package dependencies", required=False),
        Arg(name="wait", description="Wait for provider to be ready", required=False),
        Arg(name="verify", description="Verify provider installation", required=False),
        Arg(name="timeout", description="Timeout for waiting (default: 300s)", required=False)
    ],
    image="bitnami/kubectl:latest"
)

# Provider configuration tool
configure_provider_tool = CrossplaneTool(
    name="configure_provider",
    description="Configure a Crossplane provider",
    content="""
    if [ -z "$PROVIDER" ]; then
        echo "Error: Provider not specified"
        exit 1
    fi

    if [ -z "$CONFIG" ]; then
        echo "Error: Provider configuration not specified"
        exit 1
    fi

    # Configure provider
    cat <<EOF | kubectl apply -f -
apiVersion: ${PROVIDER}.crossplane.io/v1beta1
kind: ProviderConfig
metadata:
  name: ${NAME:-default}
spec:
  ${CONFIG}
EOF

    if [ "$VERIFY" = "true" ]; then
        echo "\\nVerifying provider configuration..."
        kubectl get providerconfig.${PROVIDER}.crossplane.io ${NAME:-default} -o yaml
    fi
    """,
    args=[
        Arg(name="provider", description="Provider to configure (aws, gcp, etc.)", required=True),
        Arg(name="config", description="Provider configuration in YAML format", required=True),
        Arg(name="name", description="Name of the provider configuration", required=False),
        Arg(name="verify", description="Verify provider configuration", required=False)
    ],
    image="bitnami/kubectl:latest"
)

# List providers tool
list_providers_tool = CrossplaneTool(
    name="list_providers",
    description="List installed Crossplane providers",
    content="""
    echo "Installed Providers:"
    kubectl get providers.pkg.crossplane.io -o wide

    if [ "$SHOW_CONFIGS" = "true" ]; then
        echo "\\nProvider Configurations:"
        for provider in $(kubectl get providers.pkg.crossplane.io -o jsonpath='{.items[*].metadata.name}'); do
            echo "\\nConfigurations for $provider:"
            kubectl get providerconfig.${provider}.crossplane.io -o wide 2>/dev/null || echo "No configurations found"
        done
    fi
    """,
    args=[
        Arg(name="show_configs", description="Show provider configurations", required=False)
    ],
    image="bitnami/kubectl:latest"
)

# Delete provider tool
delete_provider_tool = CrossplaneTool(
    name="delete_provider",
    description="Delete a Crossplane provider",
    content="""
    if [ -z "$PROVIDER" ]; then
        echo "Error: Provider not specified"
        exit 1
    fi

    if [ "$DELETE_CONFIGS" = "true" ]; then
        echo "Deleting provider configurations..."
        kubectl delete providerconfig.${PROVIDER}.crossplane.io --all
    fi

    echo "Deleting provider..."
    kubectl delete provider.pkg.crossplane.io ${PROVIDER}

    if [ "$WAIT" = "true" ]; then
        echo "Waiting for provider to be deleted..."
        kubectl wait --for=delete provider.pkg.crossplane.io/${PROVIDER} --timeout=${TIMEOUT:-300s}
    fi
    """,
    args=[
        Arg(name="provider", description="Name of the provider to delete", required=True),
        Arg(name="delete_configs", description="Delete provider configurations", required=False),
        Arg(name="wait", description="Wait for provider to be deleted", required=False),
        Arg(name="timeout", description="Timeout for waiting (default: 300s)", required=False)
    ],
    image="bitnami/kubectl:latest"
)

def create_provider_tools() -> List[CrossplaneTool]:
    """Create and register provider management tools."""
    tools = []
    
    try:
        # Create provider tools
        provider_tools = {
            'install': install_provider_tool,
            'configure': configure_provider_tool,
            'list': list_providers_tool,
            'delete': delete_provider_tool
        }

        # Add all provider tools
        for name, tool in provider_tools.items():
            tools.append(tool)
            logger.info(f"Added provider tool: {name}")

        # Register all created tools
        CrossplaneTool.register_tools(tools)
        logger.info(f"Successfully registered {len(tools)} provider tools")
        
    except Exception as e:
        logger.error(f"Failed to create provider tools: {str(e)}")
    
    return tools

# Create provider tools when module is imported
provider_tools = create_provider_tools()

# Export tools
__all__ = [
    'install_provider_tool',
    'configure_provider_tool',
    'list_providers_tool',
    'delete_provider_tool',
    'create_provider_tools'
] 