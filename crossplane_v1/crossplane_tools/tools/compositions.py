from typing import List
from .base import CrossplaneTool, Arg

class CompositionManager(CrossplaneTool):
    """Manage Crossplane compositions."""
    
    def __init__(self):
        super().__init__(
            name="crossplane_composition",
            description="Manage Crossplane compositions and XRDs",
            content="",
            args=[],
            image="bitnami/kubectl:latest"
        )

    def apply_composition(self) -> CrossplaneTool:
        """Apply a Crossplane Composition."""
        return CrossplaneTool(
            name="apply_composition",
            description="Apply a Crossplane Composition",
            content="""
            if [ -z "$COMPOSITION_FILE" ]; then
                echo "Error: Composition file not specified"
                exit 1
            fi

            # Validate the composition file
            echo "Validating composition file..."
            if ! yq e '.' "$COMPOSITION_FILE" > /dev/null; then
                echo "Error: Invalid YAML file"
                exit 1
            fi

            # Apply the composition
            echo "Applying composition..."
            kubectl apply -f "$COMPOSITION_FILE"

            # Get the composition name
            COMP_NAME=$(yq e '.metadata.name' "$COMPOSITION_FILE")
            echo "\nComposition status:"
            kubectl get composition "$COMP_NAME" -o yaml
            """,
            args=[
                Arg("composition_file",
                    description="Path to the Composition YAML file",
                    required=True)
            ],
            image="mikefarah/yq:4"  # Using yq for YAML processing
        )

    def apply_xrd(self) -> CrossplaneTool:
        """Apply a Composite Resource Definition (XRD)."""
        return CrossplaneTool(
            name="apply_xrd",
            description="Apply a Composite Resource Definition",
            content="""
            if [ -z "$XRD_FILE" ]; then
                echo "Error: XRD file not specified"
                exit 1
            fi

            # Validate the XRD file
            echo "Validating XRD file..."
            if ! yq e '.' "$XRD_FILE" > /dev/null; then
                echo "Error: Invalid YAML file"
                exit 1
            fi

            # Apply the XRD
            echo "Applying XRD..."
            kubectl apply -f "$XRD_FILE"

            # Get the XRD name
            XRD_NAME=$(yq e '.metadata.name' "$XRD_FILE")
            echo "\nXRD status:"
            kubectl get xrd "$XRD_NAME" -o yaml
            """,
            args=[
                Arg("xrd_file",
                    description="Path to the XRD YAML file",
                    required=True)
            ],
            image="mikefarah/yq:4"
        )

    def list_compositions(self) -> CrossplaneTool:
        """List all Crossplane Compositions."""
        return CrossplaneTool(
            name="list_compositions",
            description="List all Crossplane Compositions",
            content="""
            echo "=== Compositions ==="
            kubectl get compositions.apiextensions.crossplane.io -o wide

            echo "\n=== Composite Resource Definitions ==="
            kubectl get xrds.apiextensions.crossplane.io -o wide

            echo "\n=== Composition Revisions ==="
            kubectl get compositionrevisions.apiextensions.crossplane.io
            """,
            args=[],
            image="bitnami/kubectl:latest"
        )

    def get_composition_details(self) -> CrossplaneTool:
        """Get detailed information about a specific Composition."""
        return CrossplaneTool(
            name="get_composition_details",
            description="Get detailed information about a Composition",
            content="""
            if [ -z "$COMPOSITION_NAME" ]; then
                echo "Error: Composition name not specified"
                exit 1
            fi

            echo "=== Composition Details ==="
            kubectl describe composition.apiextensions.crossplane.io "$COMPOSITION_NAME"

            echo "\n=== Related XRDs ==="
            COMP_XRD=$(kubectl get composition "$COMPOSITION_NAME" -o jsonpath='{.spec.compositeTypeRef.name}')
            kubectl get xrd "$COMP_XRD" -o yaml

            echo "\n=== Composition Usage ==="
            kubectl get composite -l crossplane.io/composition="$COMPOSITION_NAME" -A
            """,
            args=[
                Arg("composition_name",
                    description="Name of the Composition to inspect",
                    required=True)
            ],
            image="bitnami/kubectl:latest"
        )

    def validate_composition(self) -> CrossplaneTool:
        """Validate a Composition file."""
        return CrossplaneTool(
            name="validate_composition",
            description="Validate a Composition file",
            content="""
            if [ -z "$COMPOSITION_FILE" ]; then
                echo "Error: Composition file not specified"
                exit 1
            fi

            echo "=== Validating Composition ==="
            
            # Check YAML syntax
            echo "Checking YAML syntax..."
            if ! yq e '.' "$COMPOSITION_FILE" > /dev/null; then
                echo "❌ Invalid YAML syntax"
                exit 1
            fi
            echo "✅ YAML syntax is valid"

            # Check required fields
            echo "\nChecking required fields..."
            yq e '.apiVersion == "apiextensions.crossplane.io/v1"' "$COMPOSITION_FILE" > /dev/null || 
                { echo "❌ Invalid or missing apiVersion"; exit 1; }
            yq e '.kind == "Composition"' "$COMPOSITION_FILE" > /dev/null || 
                { echo "❌ Invalid or missing kind"; exit 1; }
            yq e '.metadata.name' "$COMPOSITION_FILE" > /dev/null || 
                { echo "❌ Missing metadata.name"; exit 1; }
            yq e '.spec.compositeTypeRef' "$COMPOSITION_FILE" > /dev/null || 
                { echo "❌ Missing spec.compositeTypeRef"; exit 1; }
            echo "✅ All required fields are present"

            # Dry run the composition
            echo "\nPerforming dry run..."
            if kubectl apply -f "$COMPOSITION_FILE" --dry-run=client; then
                echo "✅ Dry run successful"
            else
                echo "❌ Dry run failed"
                exit 1
            fi
            """,
            args=[
                Arg("composition_file",
                    description="Path to the Composition YAML file to validate",
                    required=True)
            ],
            image="mikefarah/yq:4"
        ) 