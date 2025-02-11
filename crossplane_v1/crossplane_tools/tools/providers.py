from typing import List
from .base import CrossplaneTool, Arg
from kubiya_sdk.tools.registry import tool_registry
import sys

"""
Provider Management Module Structure:

```mermaid
classDiagram
    class CrossplaneTool {
        <<base>>
    }
    class ProviderManager {
        +install_provider()
        +configure_provider()
        +list_providers()
        +get_provider_status()
        +uninstall_provider()
    }
    CrossplaneTool <|-- ProviderManager
    note for ProviderManager "Manages Crossplane providers\nand their configurations"
```
"""

class ProviderManager(CrossplaneTool):
    """Manage Crossplane providers."""
    
    def __init__(self):
        super().__init__(
            name="provider",
            description="Manage Crossplane providers",
            content="",
            image="bitnami/kubectl:latest"
        )
        # Register this tool and all provider-specific tools
        self.register_tools()

    def register_tools(self):
        """Register all provider tools."""
        try:
            # Register the provider manager itself
            tool_registry.register("crossplane", self)
            
            # Register all provider-specific tools
            tools = [
                self.install_provider(),
                self.configure_provider(),
                self.list_providers(),
                self.get_provider_status(),
                self.uninstall_provider(),
                self.apply_provider_resource()
            ]
            
            for tool in tools:
                tool_registry.register("crossplane", tool)
                
        except Exception as e:
            print(f"Error registering provider tools: {str(e)}")

    def install_provider(self) -> CrossplaneTool:
        """Install a Crossplane provider."""
        return CrossplaneTool(
            name="provider_install",
            description="Install a Crossplane provider with specific version and configuration",
            content="""
            if [ -z "$PROVIDER_PACKAGE" ]; then
                echo "Error: Provider package not specified"
                exit 1
            fi

            # Extract provider name and create a clean name for the resource
            PROVIDER_NAME=$(echo $PROVIDER_PACKAGE | cut -d "/" -f2 | cut -d ":" -f1)
            CLEAN_NAME=${PROVIDER_NAME##*/}

            # Apply provider with optional configuration
            cat <<EOF | kubectl apply -f -
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: $CLEAN_NAME
  ${ANNOTATIONS:+annotations: $ANNOTATIONS}
  ${LABELS:+labels: $LABELS}
spec:
  package: $PROVIDER_PACKAGE
  ${REVISION_ACTIVATION_POLICY:+revisionActivationPolicy: $REVISION_ACTIVATION_POLICY}
  ${REVISION_HISTORY_LIMIT:+revisionHistoryLimit: $REVISION_HISTORY_LIMIT}
  ${PACKAGE_PULL_SECRETS:+packagePullSecrets: $PACKAGE_PULL_SECRETS}
  ${SKIP_DEPENDENCY_RESOLUTION:+skipDependencyResolution: $SKIP_DEPENDENCY_RESOLUTION}
EOF

            echo "Waiting for provider $CLEAN_NAME to be healthy..."
            kubectl wait --for=condition=healthy provider.pkg.crossplane.io/$CLEAN_NAME --timeout=${TIMEOUT:-300s}

            if [ "$VERIFY" = "true" ]; then
                echo "\\nVerifying provider installation..."
                kubectl get provider.pkg.crossplane.io/$CLEAN_NAME -o yaml
                
                echo "\\nChecking provider pods..."
                kubectl get pods -n crossplane-system -l pkg.crossplane.io/provider=$CLEAN_NAME
            fi
            """,
            args=[
                Arg(name="provider_package", 
                    description="The provider package to install (e.g., crossplane/provider-aws:v0.24.1)",
                    required=True),
                Arg(name="revision_activation_policy",
                    description="RevisionActivationPolicy specifies how the provider controller should handle different revisions (Automatic or Manual)",
                    required=False),
                Arg(name="revision_history_limit",
                    description="Number of old revisions to retain",
                    required=False),
                Arg(name="package_pull_secrets",
                    description="List of secrets required to pull the provider package",
                    required=False),
                Arg(name="skip_dependency_resolution",
                    description="Whether to skip resolving dependencies",
                    required=False),
                Arg(name="annotations",
                    description="Additional annotations to add to the provider",
                    required=False),
                Arg(name="labels",
                    description="Additional labels to add to the provider",
                    required=False),
                Arg(name="timeout",
                    description="Timeout for waiting for provider to be healthy (default: 300s)",
                    required=False),
                Arg(name="verify",
                    description="Whether to verify the installation by checking provider status and pods",
                    required=False)
            ],
            image="bitnami/kubectl:latest"
        )

    def configure_provider(self) -> CrossplaneTool:
        """Configure a Crossplane provider with credentials and settings."""
        return CrossplaneTool(
            name="provider_configure",
            description="Configure a Crossplane provider with credentials and settings",
            content="""
            if [ -z "$PROVIDER_NAME" ]; then
                echo "Error: Provider name not specified"
                exit 1
            fi

            if [ -z "$CREDENTIALS" ] && [ -z "$CREDENTIALS_FILE" ]; then
                echo "Error: Either credentials or credentials_file must be specified"
                exit 1
            fi

            # Create temporary file for credentials if provided directly
            if [ ! -z "$CREDENTIALS" ]; then
                CREDENTIALS_FILE=$(mktemp)
                echo "$CREDENTIALS" > $CREDENTIALS_FILE
            fi

            # Create provider config
            cat <<EOF | kubectl apply -f -
apiVersion: ${PROVIDER_NAME}.crossplane.io/v1beta1
kind: ProviderConfig
metadata:
  name: ${CONFIG_NAME:-default}
  ${ANNOTATIONS:+annotations: $ANNOTATIONS}
  ${LABELS:+labels: $LABELS}
spec:
  credentials:
    source: ${CREDENTIALS_SOURCE:-Secret}
    secretRef:
      namespace: ${SECRET_NAMESPACE:-crossplane-system}
      name: ${SECRET_NAME:-provider-secret}
      key: ${SECRET_KEY:-credentials}
EOF

            # Create secret with credentials
            kubectl create secret generic ${SECRET_NAME:-provider-secret} \
                --namespace ${SECRET_NAMESPACE:-crossplane-system} \
                --from-file=${SECRET_KEY:-credentials}=$CREDENTIALS_FILE \
                --dry-run=client -o yaml | kubectl apply -f -

            if [ "$VERIFY" = "true" ]; then
                echo "\\nVerifying provider configuration..."
                kubectl get providerconfig.${PROVIDER_NAME}.crossplane.io ${CONFIG_NAME:-default} -o yaml
                
                echo "\\nChecking secret..."
                kubectl get secret ${SECRET_NAME:-provider-secret} -n ${SECRET_NAMESPACE:-crossplane-system}
            fi

            # Cleanup temporary file if created
            if [ ! -z "$CREDENTIALS" ]; then
                rm -f $CREDENTIALS_FILE
            fi
            """,
            args=[
                Arg(name="provider_name",
                    description="Name of the provider (e.g., aws, gcp, azure)",
                    required=True),
                Arg(name="credentials",
                    description="Provider credentials content",
                    required=False),
                Arg(name="credentials_file",
                    description="Path to the provider credentials file",
                    required=False),
                Arg(name="config_name",
                    description="Name of the provider configuration (default: default)",
                    required=False),
                Arg(name="credentials_source",
                    description="Source of the credentials (Secret, InjectedIdentity, etc.)",
                    required=False),
                Arg(name="secret_namespace",
                    description="Namespace for the credentials secret (default: crossplane-system)",
                    required=False),
                Arg(name="secret_name",
                    description="Name of the credentials secret (default: provider-secret)",
                    required=False),
                Arg(name="secret_key",
                    description="Key in the secret for credentials (default: credentials)",
                    required=False),
                Arg(name="annotations",
                    description="Additional annotations for the provider config",
                    required=False),
                Arg(name="labels",
                    description="Additional labels for the provider config",
                    required=False),
                Arg(name="verify",
                    description="Whether to verify the configuration",
                    required=False)
            ],
            image="bitnami/kubectl:latest"
        )

    def list_providers(self) -> CrossplaneTool:
        """List installed Crossplane providers with detailed information."""
        return CrossplaneTool(
            name="provider_list",
            description="List installed Crossplane providers with detailed information",
            content="""
            # Function to format output with emojis
            format_status() {
                if [ "$1" = "Healthy" ]; then
                    echo "✅ $1"
                elif [ "$1" = "Unhealthy" ]; then
                    echo "❌ $1"
                else
                    echo "⚠️ $1"
                fi
            }

            echo "=== Installed Providers ==="
            if [ "$WIDE_OUTPUT" = "true" ]; then
                kubectl get providers.pkg.crossplane.io -o wide
            else
                kubectl get providers.pkg.crossplane.io
            fi

            if [ "$SHOW_DETAILS" = "true" ]; then
                echo "\\n=== Provider Details ==="
                kubectl get providers.pkg.crossplane.io -o json | jq -r '.items[] | "Provider: " + .metadata.name + "\\nStatus: " + (.status.conditions[] | select(.type=="Healthy") | .status) + "\\nPackage: " + .spec.package + "\\n"' | while read -r line; do
                    echo "$line" | format_status
                done
            fi
            """,
            args=[
                Arg(name="wide_output",
                    description="Show additional columns in the output",
                    required=False),
                Arg(name="show_details",
                    description="Show detailed information about each provider",
                    required=False)
            ],
            image="bitnami/kubectl:latest"
        )

    def get_provider_status(self) -> CrossplaneTool:
        """Get detailed status and health information for a specific provider."""
        return CrossplaneTool(
            name="provider_status",
            description="Get detailed status and health information for a specific provider",
            content="""
            if [ -z "$PROVIDER_NAME" ]; then
                echo "Error: Provider name not specified"
                exit 1
            fi

            echo "=== Provider Status ==="
            if [ "$OUTPUT_FORMAT" ]; then
                kubectl get provider.pkg.crossplane.io $PROVIDER_NAME -o $OUTPUT_FORMAT
            else
                kubectl describe provider.pkg.crossplane.io $PROVIDER_NAME
            fi

            echo "\\n=== Provider Controller Pods ==="
            kubectl get pods -l pkg.crossplane.io/provider=$PROVIDER_NAME -A

            if [ "$SHOW_EVENTS" = "true" ]; then
                echo "\\n=== Provider Events ==="
                kubectl get events --field-selector involvedObject.kind=Provider,involvedObject.name=$PROVIDER_NAME --sort-by='.lastTimestamp'
            fi

            if [ "$SHOW_RESOURCES" = "true" ]; then
                echo "\\n=== Managed Resources ==="
                kubectl get managed -l crossplane.io/provider=$PROVIDER_NAME -A
            fi

            if [ "$SHOW_HEALTH" = "true" ]; then
                echo "\\n=== Health Check ==="
                kubectl get provider.pkg.crossplane.io $PROVIDER_NAME -o json | \
                jq -r '.status.conditions[] | "Type: " + .type + "\\nStatus: " + .status + "\\nMessage: " + .message + "\\nLast Transition: " + .lastTransitionTime + "\\n"'
            fi
            """,
            args=[
                Arg(name="provider_name",
                    description="Name of the provider to check",
                    required=True),
                Arg(name="output_format",
                    description="Output format (json|yaml|wide)",
                    required=False),
                Arg(name="show_events",
                    description="Show provider events",
                    required=False),
                Arg(name="show_resources",
                    description="Show managed resources",
                    required=False),
                Arg(name="show_health",
                    description="Show detailed health information",
                    required=False)
            ],
            image="bitnami/kubectl:latest"
        )

    def uninstall_provider(self) -> CrossplaneTool:
        """Uninstall a Crossplane provider and clean up its resources."""
        return CrossplaneTool(
            name="provider_uninstall",
            description="Uninstall a Crossplane provider and clean up its resources",
            content="""
            if [ -z "$PROVIDER_NAME" ]; then
                echo "Error: Provider name not specified"
                exit 1
            fi

            if [ "$BACKUP" = "true" ]; then
                echo "Creating backup of provider resources..."
                mkdir -p provider-backup
                kubectl get provider.pkg.crossplane.io $PROVIDER_NAME -o yaml > provider-backup/$PROVIDER_NAME-provider.yaml
                kubectl get crds -l crossplane.io/provider=$PROVIDER_NAME -o yaml > provider-backup/$PROVIDER_NAME-crds.yaml
                kubectl get providerconfigs.${PROVIDER_NAME#provider-}.crossplane.io --all-namespaces -o yaml > provider-backup/$PROVIDER_NAME-configs.yaml
            fi

            if [ "$DELETE_RESOURCES" = "true" ]; then
                echo "Deleting managed resources..."
                kubectl get managed -l crossplane.io/provider=$PROVIDER_NAME -A -o name | while read res; do
                    kubectl delete $res
                done
            fi

            echo "Deleting provider configurations..."
            kubectl get providerconfigs.${PROVIDER_NAME#provider-}.crossplane.io --no-headers 2>/dev/null | \
                awk '{print $1}' | xargs -r kubectl delete providerconfig

            echo "Deleting provider..."
            kubectl delete provider.pkg.crossplane.io $PROVIDER_NAME

            if [ "$DELETE_CRDS" = "true" ]; then
                echo "Cleaning up provider CRDs..."
                kubectl get crds -l crossplane.io/provider=$PROVIDER_NAME -o name | xargs -r kubectl delete
            fi

            if [ "$VERIFY" = "true" ]; then
                echo "\\nVerifying provider removal..."
                if ! kubectl get provider.pkg.crossplane.io $PROVIDER_NAME 2>/dev/null; then
                    echo "✅ Provider successfully removed"
                else
                    echo "❌ Provider still exists"
                    exit 1
                fi
            fi
            """,
            args=[
                Arg(name="provider_name",
                    description="Name of the provider to uninstall",
                    required=True),
                Arg(name="backup",
                    description="Create backup of provider resources before deletion",
                    required=False),
                Arg(name="delete_resources",
                    description="Delete all managed resources before provider removal",
                    required=False),
                Arg(name="delete_crds",
                    description="Delete provider CRDs after removal",
                    required=False),
                Arg(name="verify",
                    description="Verify provider removal",
                    required=False)
            ],
            image="bitnami/kubectl:latest"
        )

    def apply_provider_resource(self) -> CrossplaneTool:
        """Apply a provider-specific resource or CRD."""
        return CrossplaneTool(
            name="provider_apply_resource",
            description="Apply a provider-specific resource or CRD",
            content="""
            if [ -z "$RESOURCE_CONTENT" ] && [ -z "$RESOURCE_FILE" ]; then
                echo "Error: Either resource_content or resource_file must be specified"
                exit 1
            fi

            # Create temporary file for resource content if provided directly
            if [ ! -z "$RESOURCE_CONTENT" ]; then
                RESOURCE_FILE=$(mktemp)
                echo "$RESOURCE_CONTENT" > $RESOURCE_FILE
            fi

            # Get resource details
            RESOURCE_CONTENT_TMP=$(cat $RESOURCE_FILE)
            RESOURCE_KIND=$(get_resource_name "$RESOURCE_CONTENT_TMP")
            RESOURCE_NAME=$(get_resource_name "$RESOURCE_CONTENT_TMP")
            RESOURCE_NAMESPACE=$(get_resource_namespace "$RESOURCE_CONTENT_TMP")

            # Validate the resource
            if [ "$VALIDATE" = "true" ]; then
                echo "Validating resource..."
                if ! kubectl apply --dry-run=client -f $RESOURCE_FILE; then
                    echo "❌ Resource validation failed"
                    exit 1
                fi
            fi

            # Apply the resource
            if [ "$DRY_RUN" = "true" ]; then
                echo "Performing dry run..."
                kubectl apply --dry-run=server -f $RESOURCE_FILE
            else
                kubectl apply -f $RESOURCE_FILE

                if [ "$WAIT" = "true" ]; then
                    wait_for_resource "$RESOURCE_KIND" "$RESOURCE_NAME" "$RESOURCE_NAMESPACE" "${TIMEOUT:-300s}"
                fi
            fi

            # Cleanup temporary file if created
            if [ ! -z "$RESOURCE_CONTENT" ]; then
                rm -f $RESOURCE_FILE
            fi
            """,
            args=[
                Arg(name="resource_content",
                    description="The YAML content of the resource to apply",
                    required=False),
                Arg(name="resource_file",
                    description="Path to the resource YAML file",
                    required=False),
                Arg(name="validate",
                    description="Validate the resource before applying",
                    required=False),
                Arg(name="dry_run",
                    description="Perform a dry run without actually applying the resource",
                    required=False),
                Arg(name="wait",
                    description="Wait for the resource to be ready",
                    required=False),
                Arg(name="timeout",
                    description="Timeout for waiting for resource readiness (default: 300s)",
                    required=False)
            ],
            image="bitnami/kubectl:latest"
        )

# Register tools when module is imported
__all__ = [
    'install_provider',
    'configure_provider',
    'list_providers',
    'get_provider_status',
    'uninstall_provider',
    'apply_provider_resource'
]

if __name__ == "__main__":
    ProviderManager()

# Create provider tools directly
install_provider_tool = CrossplaneTool(
    name="provider_install",
    description="Install a Crossplane provider with specific version and configuration",
    content="""
    if [ -z "$PROVIDER_PACKAGE" ]; then
        echo "Error: Provider package not specified"
        exit 1
    fi

    # Extract provider name and create a clean name for the resource
    PROVIDER_NAME=$(echo $PROVIDER_PACKAGE | cut -d "/" -f2 | cut -d ":" -f1)
    CLEAN_NAME=${PROVIDER_NAME##*/}

    # Apply provider with optional configuration
    cat <<EOF | kubectl apply -f -
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: $CLEAN_NAME
  ${ANNOTATIONS:+annotations: $ANNOTATIONS}
  ${LABELS:+labels: $LABELS}
spec:
  package: $PROVIDER_PACKAGE
  ${REVISION_ACTIVATION_POLICY:+revisionActivationPolicy: $REVISION_ACTIVATION_POLICY}
  ${REVISION_HISTORY_LIMIT:+revisionHistoryLimit: $REVISION_HISTORY_LIMIT}
  ${PACKAGE_PULL_SECRETS:+packagePullSecrets: $PACKAGE_PULL_SECRETS}
  ${SKIP_DEPENDENCY_RESOLUTION:+skipDependencyResolution: $SKIP_DEPENDENCY_RESOLUTION}
EOF

    echo "Waiting for provider $CLEAN_NAME to be healthy..."
    kubectl wait --for=condition=healthy provider.pkg.crossplane.io/$CLEAN_NAME --timeout=${TIMEOUT:-300s}

    if [ "$VERIFY" = "true" ]; then
        echo "\\nVerifying provider installation..."
        kubectl get provider.pkg.crossplane.io/$CLEAN_NAME -o yaml
        
        echo "\\nChecking provider pods..."
        kubectl get pods -n crossplane-system -l pkg.crossplane.io/provider=$CLEAN_NAME
    fi
    """,
    args=[
        Arg(name="provider_package", 
            description="The provider package to install (e.g., crossplane/provider-aws:v0.24.1)",
            required=True),
        Arg(name="revision_activation_policy",
            description="RevisionActivationPolicy specifies how the provider controller should handle different revisions (Automatic or Manual)",
            required=False),
        Arg(name="revision_history_limit",
            description="Number of old revisions to retain",
            required=False),
        Arg(name="package_pull_secrets",
            description="List of secrets required to pull the provider package",
            required=False),
        Arg(name="skip_dependency_resolution",
            description="Whether to skip resolving dependencies",
            required=False),
        Arg(name="annotations",
            description="Additional annotations to add to the provider",
            required=False),
        Arg(name="labels",
            description="Additional labels to add to the provider",
            required=False),
        Arg(name="timeout",
            description="Timeout for waiting for provider to be healthy (default: 300s)",
            required=False),
        Arg(name="verify",
            description="Whether to verify the installation by checking provider status and pods",
            required=False)
    ],
    image="bitnami/kubectl:latest"
)

configure_provider_tool = CrossplaneTool(
    name="provider_configure",
    description="Configure a Crossplane provider with credentials and settings",
    content="""
    if [ -z "$PROVIDER_NAME" ]; then
        echo "Error: Provider name not specified"
        exit 1
    fi

    if [ -z "$CREDENTIALS" ] && [ -z "$CREDENTIALS_FILE" ]; then
        echo "Error: Either credentials or credentials_file must be specified"
        exit 1
    fi

    # Create temporary file for credentials if provided directly
    if [ ! -z "$CREDENTIALS" ]; then
        CREDENTIALS_FILE=$(mktemp)
        echo "$CREDENTIALS" > $CREDENTIALS_FILE
    fi

    # Create provider config
    cat <<EOF | kubectl apply -f -
apiVersion: ${PROVIDER_NAME}.crossplane.io/v1beta1
kind: ProviderConfig
metadata:
  name: ${CONFIG_NAME:-default}
  ${ANNOTATIONS:+annotations: $ANNOTATIONS}
  ${LABELS:+labels: $LABELS}
spec:
  credentials:
    source: ${CREDENTIALS_SOURCE:-Secret}
    secretRef:
      namespace: ${SECRET_NAMESPACE:-crossplane-system}
      name: ${SECRET_NAME:-provider-secret}
      key: ${SECRET_KEY:-credentials}
EOF

    # Create secret with credentials
    kubectl create secret generic ${SECRET_NAME:-provider-secret} \
        --namespace ${SECRET_NAMESPACE:-crossplane-system} \
        --from-file=${SECRET_KEY:-credentials}=$CREDENTIALS_FILE \
        --dry-run=client -o yaml | kubectl apply -f -

    if [ "$VERIFY" = "true" ]; then
        echo "\\nVerifying provider configuration..."
        kubectl get providerconfig.${PROVIDER_NAME}.crossplane.io ${CONFIG_NAME:-default} -o yaml
        
        echo "\\nChecking secret..."
        kubectl get secret ${SECRET_NAME:-provider-secret} -n ${SECRET_NAMESPACE:-crossplane-system}
    fi

    # Cleanup temporary file if created
    if [ ! -z "$CREDENTIALS" ]; then
        rm -f $CREDENTIALS_FILE
    fi
    """,
    args=[
        Arg(name="provider_name",
            description="Name of the provider (e.g., aws, gcp, azure)",
            required=True),
        Arg(name="credentials",
            description="Provider credentials content",
            required=False),
        Arg(name="credentials_file",
            description="Path to the provider credentials file",
            required=False),
        Arg(name="config_name",
            description="Name of the provider configuration (default: default)",
            required=False),
        Arg(name="credentials_source",
            description="Source of the credentials (Secret, InjectedIdentity, etc.)",
            required=False),
        Arg(name="secret_namespace",
            description="Namespace for the credentials secret (default: crossplane-system)",
            required=False),
        Arg(name="secret_name",
            description="Name of the credentials secret (default: provider-secret)",
            required=False),
        Arg(name="secret_key",
            description="Key in the secret for credentials (default: credentials)",
            required=False),
        Arg(name="annotations",
            description="Additional annotations for the provider config",
            required=False),
        Arg(name="labels",
            description="Additional labels for the provider config",
            required=False),
        Arg(name="verify",
            description="Whether to verify the configuration",
            required=False)
    ],
    image="bitnami/kubectl:latest"
)

list_providers_tool = CrossplaneTool(
    name="provider_list",
    description="List installed Crossplane providers with detailed information",
    content="""
    # Function to format output with emojis
    format_status() {
        if [ "$1" = "Healthy" ]; then
            echo "✅ $1"
        elif [ "$1" = "Unhealthy" ]; then
            echo "❌ $1"
        else
            echo "⚠️ $1"
        fi
    }

    echo "=== Installed Providers ==="
    if [ "$WIDE_OUTPUT" = "true" ]; then
        kubectl get providers.pkg.crossplane.io -o wide
    else
        kubectl get providers.pkg.crossplane.io
    fi

    if [ "$SHOW_DETAILS" = "true" ]; then
        echo "\\n=== Provider Details ==="
        kubectl get providers.pkg.crossplane.io -o json | jq -r '.items[] | "Provider: " + .metadata.name + "\\nStatus: " + (.status.conditions[] | select(.type=="Healthy") | .status) + "\\nPackage: " + .spec.package + "\\n"' | while read -r line; do
            echo "$line" | format_status
        done
    fi
    """,
    args=[
        Arg(name="wide_output",
            description="Show additional columns in the output",
            required=False),
        Arg(name="show_details",
            description="Show detailed information about each provider",
            required=False)
    ],
    image="bitnami/kubectl:latest"
)

get_provider_status_tool = CrossplaneTool(
    name="provider_status",
    description="Get detailed status and health information for a specific provider",
    content="""
    if [ -z "$PROVIDER_NAME" ]; then
        echo "Error: Provider name not specified"
        exit 1
    fi

    echo "=== Provider Status ==="
    if [ "$OUTPUT_FORMAT" ]; then
        kubectl get provider.pkg.crossplane.io $PROVIDER_NAME -o $OUTPUT_FORMAT
    else
        kubectl describe provider.pkg.crossplane.io $PROVIDER_NAME
    fi

    echo "\\n=== Provider Controller Pods ==="
    kubectl get pods -l pkg.crossplane.io/provider=$PROVIDER_NAME -A

    if [ "$SHOW_EVENTS" = "true" ]; then
        echo "\\n=== Provider Events ==="
        kubectl get events --field-selector involvedObject.kind=Provider,involvedObject.name=$PROVIDER_NAME --sort-by='.lastTimestamp'
    fi

    if [ "$SHOW_RESOURCES" = "true" ]; then
        echo "\\n=== Managed Resources ==="
        kubectl get managed -l crossplane.io/provider=$PROVIDER_NAME -A
    fi

    if [ "$SHOW_HEALTH" = "true" ]; then
        echo "\\n=== Health Check ==="
        kubectl get provider.pkg.crossplane.io $PROVIDER_NAME -o json | \
        jq -r '.status.conditions[] | "Type: " + .type + "\\nStatus: " + .status + "\\nMessage: " + .message + "\\nLast Transition: " + .lastTransitionTime + "\\n"'
    fi
    """,
    args=[
        Arg(name="provider_name",
            description="Name of the provider to check",
            required=True),
        Arg(name="output_format",
            description="Output format (json|yaml|wide)",
            required=False),
        Arg(name="show_events",
            description="Show provider events",
            required=False),
        Arg(name="show_resources",
            description="Show managed resources",
            required=False),
        Arg(name="show_health",
            description="Show detailed health information",
            required=False)
    ],
    image="bitnami/kubectl:latest"
)

uninstall_provider_tool = CrossplaneTool(
    name="provider_uninstall",
    description="Uninstall a Crossplane provider and clean up its resources",
    content="""
    if [ -z "$PROVIDER_NAME" ]; then
        echo "Error: Provider name not specified"
        exit 1
    fi

    if [ "$BACKUP" = "true" ]; then
        echo "Creating backup of provider resources..."
        mkdir -p provider-backup
        kubectl get provider.pkg.crossplane.io $PROVIDER_NAME -o yaml > provider-backup/$PROVIDER_NAME-provider.yaml
        kubectl get crds -l crossplane.io/provider=$PROVIDER_NAME -o yaml > provider-backup/$PROVIDER_NAME-crds.yaml
        kubectl get providerconfigs.${PROVIDER_NAME#provider-}.crossplane.io --all-namespaces -o yaml > provider-backup/$PROVIDER_NAME-configs.yaml
    fi

    if [ "$DELETE_RESOURCES" = "true" ]; then
        echo "Deleting managed resources..."
        kubectl get managed -l crossplane.io/provider=$PROVIDER_NAME -A -o name | while read res; do
            kubectl delete $res
        done
    fi

    echo "Deleting provider configurations..."
    kubectl get providerconfigs.${PROVIDER_NAME#provider-}.crossplane.io --no-headers 2>/dev/null | \
        awk '{print $1}' | xargs -r kubectl delete providerconfig

    echo "Deleting provider..."
    kubectl delete provider.pkg.crossplane.io $PROVIDER_NAME

    if [ "$DELETE_CRDS" = "true" ]; then
        echo "Cleaning up provider CRDs..."
        kubectl get crds -l crossplane.io/provider=$PROVIDER_NAME -o name | xargs -r kubectl delete
    fi

    if [ "$VERIFY" = "true" ]; then
        echo "\\nVerifying provider removal..."
        if ! kubectl get provider.pkg.crossplane.io $PROVIDER_NAME 2>/dev/null; then
            echo "✅ Provider successfully removed"
        else
            echo "❌ Provider still exists"
            exit 1
        fi
    fi
    """,
    args=[
        Arg(name="provider_name",
            description="Name of the provider to uninstall",
            required=True),
        Arg(name="backup",
            description="Create backup of provider resources before deletion",
            required=False),
        Arg(name="delete_resources",
            description="Delete all managed resources before provider removal",
            required=False),
        Arg(name="delete_crds",
            description="Delete provider CRDs after removal",
            required=False),
        Arg(name="verify",
            description="Verify provider removal",
            required=False)
    ],
    image="bitnami/kubectl:latest"
)

apply_provider_resource_tool = CrossplaneTool(
    name="provider_apply_resource",
    description="Apply a provider-specific resource or CRD",
    content="""
    if [ -z "$RESOURCE_CONTENT" ] && [ -z "$RESOURCE_FILE" ]; then
        echo "Error: Either resource_content or resource_file must be specified"
        exit 1
    fi

    # Create temporary file for resource content if provided directly
    if [ ! -z "$RESOURCE_CONTENT" ]; then
        RESOURCE_FILE=$(mktemp)
        echo "$RESOURCE_CONTENT" > $RESOURCE_FILE
    fi

    # Get resource details
    RESOURCE_CONTENT_TMP=$(cat $RESOURCE_FILE)
    RESOURCE_KIND=$(get_resource_name "$RESOURCE_CONTENT_TMP")
    RESOURCE_NAME=$(get_resource_name "$RESOURCE_CONTENT_TMP")
    RESOURCE_NAMESPACE=$(get_resource_namespace "$RESOURCE_CONTENT_TMP")

    # Validate the resource
    if [ "$VALIDATE" = "true" ]; then
        echo "Validating resource..."
        if ! kubectl apply --dry-run=client -f $RESOURCE_FILE; then
            echo "❌ Resource validation failed"
            exit 1
        fi
    fi

    # Apply the resource
    if [ "$DRY_RUN" = "true" ]; then
        echo "Performing dry run..."
        kubectl apply --dry-run=server -f $RESOURCE_FILE
    else
        kubectl apply -f $RESOURCE_FILE

        if [ "$WAIT" = "true" ]; then
            wait_for_resource "$RESOURCE_KIND" "$RESOURCE_NAME" "$RESOURCE_NAMESPACE" "${TIMEOUT:-300s}"
        fi
    fi

    # Cleanup temporary file if created
    if [ ! -z "$RESOURCE_CONTENT" ]; then
        rm -f $RESOURCE_FILE
    fi
    """,
    args=[
        Arg(name="resource_content",
            description="The YAML content of the resource to apply",
            required=False),
        Arg(name="resource_file",
            description="Path to the resource YAML file",
            required=False),
        Arg(name="validate",
            description="Validate the resource before applying",
            required=False),
        Arg(name="dry_run",
            description="Perform a dry run without actually applying the resource",
            required=False),
        Arg(name="wait",
            description="Wait for the resource to be ready",
            required=False),
        Arg(name="timeout",
            description="Timeout for waiting for resource readiness (default: 300s)",
            required=False)
    ],
    image="bitnami/kubectl:latest"
)

# Register tools directly
try:
    print("\n=== Registering Provider Tools ===")
    provider_tools = [
        install_provider_tool,
        configure_provider_tool,
        list_providers_tool,
        get_provider_status_tool,
        uninstall_provider_tool,
        apply_provider_resource_tool
    ]
    
    for tool in provider_tools:
        try:
            tool_registry.register("crossplane", tool)
            print(f"✅ Registered: {tool.name}")
        except Exception as e:
            print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
            raise
except Exception as e:
    print(f"❌ Failed to register provider tools: {str(e)}", file=sys.stderr)
    raise

# Export tools
__all__ = [
    'install_provider_tool',
    'configure_provider_tool',
    'list_providers_tool',
    'get_provider_status_tool',
    'uninstall_provider_tool',
    'apply_provider_resource_tool'
] 