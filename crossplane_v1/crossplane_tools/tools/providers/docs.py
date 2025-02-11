from typing import List, Dict
from ..base import CrossplaneTool, Arg

class ProviderDocs(CrossplaneTool):
    """Handle provider documentation and CRD references."""
    
    def __init__(self):
        super().__init__(
            name="provider_docs",
            description="Access and manage provider documentation and CRD references",
            content="",
            args=[],
            image="bitnami/kubectl:latest",
            mermaid="""
```mermaid
classDiagram
    class CrossplaneTool {
        <<base>>
    }
    class ProviderDocs {
        +list_provider_crds()
        +get_crd_schema()
        +get_provider_docs()
        +validate_resource()
        +generate_resource_template()
    }
    CrossplaneTool <|-- ProviderDocs
    note for ProviderDocs "Manages provider documentation\nand CRD references"
```
"""
        )

    def list_provider_crds(self) -> CrossplaneTool:
        """List all CRDs for a specific provider."""
        return CrossplaneTool(
            name="list_provider_crds",
            description="List all CRDs for a specific provider",
            content="""
            if [ -z "$PROVIDER" ]; then
                echo "Error: Provider not specified"
                exit 1
            fi

            echo "=== Provider CRDs ==="
            kubectl get crds -o custom-columns=NAME:.metadata.name,GROUP:.spec.group,VERSION:.spec.versions[0].name,KIND:.spec.names.kind | grep "$PROVIDER"

            echo "\n=== Provider Categories ==="
            kubectl get crds -o jsonpath="{range .items[?(@.spec.group=='$PROVIDER')]}{.spec.names.categories}{'\n'}{end}" | sort -u
            """,
            args=[
                Arg("provider",
                    description="Provider name (e.g., aws.upbound.io)",
                    required=True)
            ],
            image="bitnami/kubectl:latest"
        )

    def get_crd_schema(self) -> CrossplaneTool:
        """Get detailed schema for a specific CRD."""
        return CrossplaneTool(
            name="get_crd_schema",
            description="Get detailed schema for a specific CRD",
            content="""
            if [ -z "$CRD_NAME" ]; then
                echo "Error: CRD name not specified"
                exit 1
            fi

            echo "=== CRD Schema ==="
            kubectl get crd $CRD_NAME -o jsonpath='{.spec.versions[0].schema.openAPIV3Schema}' | yq e -P -
            
            echo "\n=== Required Fields ==="
            kubectl get crd $CRD_NAME -o jsonpath='{.spec.versions[0].schema.openAPIV3Schema.required}' | yq e -P -
            """,
            args=[
                Arg("crd_name",
                    description="Name of the CRD",
                    required=True)
            ],
            image="mikefarah/yq:4"
        )

    def get_provider_docs(self) -> CrossplaneTool:
        """Get documentation for a provider."""
        return CrossplaneTool(
            name="get_provider_docs",
            description="Get documentation for a provider",
            content="""
            if [ -z "$PROVIDER" ]; then
                echo "Error: Provider not specified"
                exit 1
            fi

            # Get provider package info
            PROVIDER_PKG=$(kubectl get provider $PROVIDER -o jsonpath='{.spec.package}')
            
            echo "=== Provider Information ==="
            echo "Package: $PROVIDER_PKG"
            echo "Documentation: https://marketplace.upbound.io/providers/$PROVIDER"
            
            echo "\n=== Available Resources ==="
            kubectl get crds -o custom-columns=RESOURCE:.spec.names.kind,GROUP:.spec.group,VERSION:.spec.versions[0].name | grep "$PROVIDER"
            
            echo "\n=== Provider Status ==="
            kubectl describe provider $PROVIDER
            """,
            args=[
                Arg("provider",
                    description="Provider name",
                    required=True)
            ],
            image="bitnami/kubectl:latest"
        )

    def validate_resource(self) -> CrossplaneTool:
        """Validate a resource against its CRD schema."""
        return CrossplaneTool(
            name="validate_resource",
            description="Validate a resource against its CRD schema",
            content="""
            if [ -z "$RESOURCE_FILE" ]; then
                echo "Error: Resource file not specified"
                exit 1
            fi

            echo "=== Validating Resource ==="
            
            # Extract resource kind and version
            KIND=$(yq e '.kind' "$RESOURCE_FILE")
            VERSION=$(yq e '.apiVersion' "$RESOURCE_FILE")
            
            echo "Resource Kind: $KIND"
            echo "API Version: $VERSION"
            
            # Validate using kubectl
            if kubectl apply --dry-run=server -f "$RESOURCE_FILE"; then
                echo "✅ Resource validation successful"
            else
                echo "❌ Resource validation failed"
                exit 1
            fi
            """,
            args=[
                Arg("resource_file",
                    description="Path to resource YAML file",
                    required=True)
            ],
            image="mikefarah/yq:4"
        )

    def generate_resource_template(self) -> CrossplaneTool:
        """Generate a resource template from CRD schema."""
        return CrossplaneTool(
            name="generate_resource_template",
            description="Generate a resource template from CRD schema",
            content="""
            if [ -z "$CRD_NAME" ] || [ -z "$RESOURCE_NAME" ]; then
                echo "Error: CRD name and resource name are required"
                exit 1
            fi

            # Get CRD schema
            SCHEMA=$(kubectl get crd $CRD_NAME -o jsonpath='{.spec.versions[0].schema.openAPIV3Schema}')
            GROUP=$(kubectl get crd $CRD_NAME -o jsonpath='{.spec.group}')
            VERSION=$(kubectl get crd $CRD_NAME -o jsonpath='{.spec.versions[0].name}')
            KIND=$(kubectl get crd $CRD_NAME -o jsonpath='{.spec.names.kind}')

            # Generate template
            cat <<EOF
apiVersion: $GROUP/$VERSION
kind: $KIND
metadata:
  name: $RESOURCE_NAME
spec:
  forProvider:
    # Add provider-specific fields here
    # See schema for available fields
  providerConfigRef:
    name: default
EOF

            echo "\n=== Available Fields ==="
            echo "$SCHEMA" | yq e '.properties.spec.properties.forProvider' -
            """,
            args=[
                Arg("crd_name",
                    description="Name of the CRD",
                    required=True),
                Arg("resource_name",
                    description="Name for the new resource",
                    required=True)
            ],
            image="mikefarah/yq:4"
        ) 