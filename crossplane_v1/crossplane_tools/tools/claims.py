from typing import List
from .base import CrossplaneTool, Arg

"""
Claims Management Module Structure:

```mermaid
classDiagram
    class CrossplaneTool {
        <<base>>
    }
    class ClaimManager {
        +apply_claim()
        +list_claims()
        +get_claim_status()
        +delete_claim()
    }
    CrossplaneTool <|-- ClaimManager
    note for ClaimManager "Manages Crossplane composite\nresource claims across namespaces"
```
"""

class ClaimManager(CrossplaneTool):
    """Manage Crossplane composite resource claims."""
    
    def __init__(self):
        super().__init__(
            name="crossplane_claim",
            description="Manage Crossplane composite resource claims",
            content="",
            args=[],
            image="bitnami/kubectl:latest",
            mermaid="""
```mermaid
classDiagram
    class CrossplaneTool {
        <<base>>
    }
    class ClaimManager {
        +apply_claim()
        +list_claims()
        +get_claim_status()
        +delete_claim()
    }
    CrossplaneTool <|-- ClaimManager
    note for ClaimManager "Manages Crossplane composite\nresource claims across namespaces"
```
"""
        )

    def apply_claim(self) -> CrossplaneTool:
        """Apply a composite resource claim."""
        return CrossplaneTool(
            name="apply_claim",
            description="Apply a composite resource claim",
            content="""
            if [ -z "$CLAIM_FILE" ]; then
                echo "Error: Claim file not specified"
                exit 1
            fi

            # Validate the claim file
            echo "Validating claim file..."
            if ! yq e '.' "$CLAIM_FILE" > /dev/null; then
                echo "Error: Invalid YAML file"
                exit 1
            fi

            # Get namespace from file or use default
            NAMESPACE=$(yq e '.metadata.namespace' "$CLAIM_FILE")
            if [ "$NAMESPACE" = "null" ]; then
                NAMESPACE="default"
                echo "No namespace specified, using 'default'"
            fi

            # Apply the claim
            echo "Applying claim..."
            kubectl apply -f "$CLAIM_FILE" -n "$NAMESPACE"

            # Get the claim name and kind
            CLAIM_NAME=$(yq e '.metadata.name' "$CLAIM_FILE")
            CLAIM_KIND=$(yq e '.kind' "$CLAIM_FILE")

            echo "\nWaiting for claim to be ready..."
            kubectl wait --for=condition=ready "$CLAIM_KIND" "$CLAIM_NAME" -n "$NAMESPACE" --timeout=300s
            """,
            args=[
                Arg("claim_file",
                    description="Path to the claim YAML file",
                    required=True)
            ],
            image="mikefarah/yq:4"
        )

    def list_claims(self) -> CrossplaneTool:
        """List all composite resource claims."""
        return CrossplaneTool(
            name="list_claims",
            description="List all composite resource claims",
            content="""
            echo "=== Composite Resource Claims ==="
            # Get all namespaces
            NAMESPACES=$(kubectl get ns -o jsonpath='{.items[*].metadata.name}')
            
            # Get all claim types (CRDs that are claims)
            CLAIM_TYPES=$(kubectl get crds -o jsonpath='{range .items[?(@.spec.names.categories[*]=="claim")]}{.metadata.name}{"\n"}{end}')
            
            # For each namespace and claim type, get claims
            for NS in $NAMESPACES; do
                echo "\nNamespace: $NS"
                echo "-------------------"
                for CLAIM_TYPE in $CLAIM_TYPES; do
                    echo "\n$CLAIM_TYPE:"
                    kubectl get "$CLAIM_TYPE" -n "$NS" 2>/dev/null || true
                done
            done

            echo "\n=== Composite Resources ==="
            kubectl get composite -A
            """,
            args=[],
            image="bitnami/kubectl:latest"
        )

    def get_claim_status(self) -> CrossplaneTool:
        """Get detailed status of a specific claim."""
        return CrossplaneTool(
            name="get_claim_status",
            description="Get detailed status of a specific claim",
            content="""
            if [ -z "$CLAIM_NAME" ] || [ -z "$CLAIM_TYPE" ]; then
                echo "Error: Claim name and type not specified"
                exit 1
            fi

            if [ -n "$NAMESPACE" ]; then
                NS_FLAG="-n $NAMESPACE"
            else
                NS_FLAG="-n default"
                echo "No namespace specified, using 'default'"
            fi

            echo "=== Claim Status ==="
            kubectl get "$CLAIM_TYPE" "$CLAIM_NAME" $NS_FLAG -o yaml

            echo "\n=== Composite Resource ==="
            CR_NAME=$(kubectl get "$CLAIM_TYPE" "$CLAIM_NAME" $NS_FLAG -o jsonpath='{.status.compositeRef.name}' 2>/dev/null)
            if [ -n "$CR_NAME" ]; then
                kubectl get composite "$CR_NAME" -o yaml
            else
                echo "No composite resource found"
            fi

            echo "\n=== Events ==="
            kubectl get events $NS_FLAG --field-selector involvedObject.name="$CLAIM_NAME" --sort-by='.lastTimestamp'
            """,
            args=[
                Arg("claim_name",
                    description="Name of the claim to check",
                    required=True),
                Arg("claim_type",
                    description="Type of the claim (e.g., database.example.org)",
                    required=True),
                Arg("namespace",
                    description="Namespace of the claim",
                    required=False)
            ],
            image="bitnami/kubectl:latest"
        )

    def delete_claim(self) -> CrossplaneTool:
        """Delete a composite resource claim."""
        return CrossplaneTool(
            name="delete_claim",
            description="Delete a composite resource claim",
            content="""
            if [ -z "$CLAIM_NAME" ] || [ -z "$CLAIM_TYPE" ]; then
                echo "Error: Claim name and type not specified"
                exit 1
            fi

            if [ -n "$NAMESPACE" ]; then
                NS_FLAG="-n $NAMESPACE"
            else
                NS_FLAG="-n default"
                echo "No namespace specified, using 'default'"
            fi

            echo "Getting composite resource name before deletion..."
            CR_NAME=$(kubectl get "$CLAIM_TYPE" "$CLAIM_NAME" $NS_FLAG -o jsonpath='{.status.compositeRef.name}' 2>/dev/null)

            echo "Deleting claim..."
            kubectl delete "$CLAIM_TYPE" "$CLAIM_NAME" $NS_FLAG

            if [ -n "$CR_NAME" ]; then
                echo "Waiting for composite resource deletion..."
                kubectl wait --for=delete composite "$CR_NAME" --timeout=300s 2>/dev/null || true
            fi
            """,
            args=[
                Arg("claim_name",
                    description="Name of the claim to delete",
                    required=True),
                Arg("claim_type",
                    description="Type of the claim (e.g., database.example.org)",
                    required=True),
                Arg("namespace",
                    description="Namespace of the claim",
                    required=False)
            ],
            image="bitnami/kubectl:latest"
        ) 