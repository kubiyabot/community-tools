"""Documentation Tools

This module provides tools for generating and viewing Crossplane provider documentation.
"""
from typing import List
from ..base import CrossplaneTool, Arg
import logging

logger = logging.getLogger(__name__)

# Provider documentation tool
provider_docs_tool = CrossplaneTool(
    name="provider_docs",
    description="Generate and view documentation for a Crossplane provider",
    content="""
    if [ -z "$PROVIDER" ]; then
        echo "Error: Provider not specified"
        exit 1
    fi

    # Get provider CRDs
    echo "Generating documentation for provider: ${PROVIDER}"
    echo "\\nAvailable Resource Types:"
    kubectl get crds -l crossplane.io/provider=${PROVIDER} -o custom-columns=NAME:.metadata.name,GROUP:.spec.group,VERSION:.spec.versions[0].name,KIND:.spec.names.kind

    if [ "$RESOURCE" ]; then
        echo "\\nResource Documentation for: ${RESOURCE}"
        kubectl explain ${RESOURCE} ${FIELD:+.${FIELD}} --api-version=${API_VERSION:-v1beta1} --recursive=${RECURSIVE:-false}
    fi

    if [ "$SHOW_EXAMPLES" = "true" ]; then
        echo "\\nExample Resources:"
        for crd in $(kubectl get crds -l crossplane.io/provider=${PROVIDER} -o name); do
            echo "\\n=== Example for $(echo $crd | cut -d/ -f2) ==="
            kubectl get $crd -o=jsonpath='{.spec.versions[0].schema.openAPIV3Schema.example}' 2>/dev/null || echo "No example available"
        done
    fi
    """,
    args=[
        Arg(name="provider", description="Name of the provider to document", required=True),
        Arg(name="resource", description="Specific resource type to document", required=False),
        Arg(name="field", description="Specific field to document", required=False),
        Arg(name="api_version", description="API version of the resource", required=False),
        Arg(name="recursive", description="Show recursive field documentation", required=False),
        Arg(name="show_examples", description="Show example resources", required=False)
    ],
    image="bitnami/kubectl:latest"
)

def create_doc_tools() -> List[CrossplaneTool]:
    """Create and register documentation tools."""
    tools = []
    
    try:
        # Create documentation tools
        doc_tools = {
            'docs': provider_docs_tool
        }

        # Add all documentation tools
        for name, tool in doc_tools.items():
            tools.append(tool)
            logger.info(f"Added documentation tool: {name}")

        # Register all created tools
        CrossplaneTool.register_tools(tools)
        logger.info(f"Successfully registered {len(tools)} documentation tools")
        
    except Exception as e:
        logger.error(f"Failed to create documentation tools: {str(e)}")
    
    return tools

# Create documentation tools when module is imported
doc_tools = create_doc_tools()

# Export tools
__all__ = [
    'provider_docs_tool',
    'create_doc_tools'
] 