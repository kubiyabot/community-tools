"""Documentation Tools

This module provides tools for managing Crossplane provider documentation.
"""
from typing import List
from ..base import CrossplaneTool, Arg
from kubiya_sdk.tools.registry import tool_registry
import sys

# Generate Provider Documentation Tool
generate_provider_docs_tool = CrossplaneTool(
    name="provider_docs_generate",
    description="Generate documentation for installed Crossplane providers",
    content="""
    # Function to generate markdown documentation
    generate_docs() {
        PROVIDER=$1
        echo "# $PROVIDER Documentation"
        echo "\\n## Available Resources"
        echo "\\nThe following resources are available in this provider:"
        
        # Get all CRDs for this provider
        kubectl get crds -l crossplane.io/provider=$PROVIDER -o custom-columns=NAME:.metadata.name,GROUP:.spec.group,VERSION:.spec.versions[0].name --no-headers | while read -r line; do
            NAME=$(echo $line | cut -d' ' -f1)
            GROUP=$(echo $line | cut -d' ' -f2)
            VERSION=$(echo $line | cut -d' ' -f3)
            
            echo "\\n### ${NAME}"
            echo "- **API Group:** ${GROUP}"
            echo "- **Version:** ${VERSION}"
            echo "\\n#### Schema"
            kubectl explain ${NAME} --recursive=true | sed 's/^/    /'
        done
    }

    if [ -z "$PROVIDER_NAME" ]; then
        echo "=== Generating Documentation for All Providers ==="
        kubectl get providers.pkg.crossplane.io -o name | cut -d'/' -f2 | while read -r provider; do
            echo "\\n=== Generating docs for $provider ==="
            generate_docs $provider > ${OUTPUT_DIR:-provider-docs}/$provider.md
        done
    else
        echo "=== Generating Documentation for $PROVIDER_NAME ==="
        generate_docs $PROVIDER_NAME > ${OUTPUT_DIR:-provider-docs}/$PROVIDER_NAME.md
    fi
    """,
    args=[
        Arg(name="provider_name", 
            description="Name of the provider to document (optional, documents all if not specified)",
            required=False),
        Arg(name="output_dir",
            description="Directory to store the generated documentation",
            required=False)
    ],
    image="bitnami/kubectl:latest"
)

# View Provider Documentation Tool
view_provider_docs_tool = CrossplaneTool(
    name="provider_docs_view",
    description="View documentation for a specific Crossplane provider",
    content="""
    if [ -z "$PROVIDER_NAME" ]; then
        echo "Error: Provider name not specified"
        exit 1
    fi

    DOC_FILE="${DOC_DIR:-provider-docs}/$PROVIDER_NAME.md"
    
    if [ ! -f "$DOC_FILE" ]; then
        echo "Documentation not found for $PROVIDER_NAME"
        echo "Please run the generate_provider_docs tool first"
        exit 1
    fi

    if [ "$FORMAT" = "html" ]; then
        # Convert markdown to HTML using pandoc
        pandoc "$DOC_FILE" -f markdown -t html -s -o "${DOC_DIR:-provider-docs}/$PROVIDER_NAME.html"
        echo "HTML documentation generated at ${DOC_DIR:-provider-docs}/$PROVIDER_NAME.html"
    else
        # Display markdown directly
        cat "$DOC_FILE"
    fi
    """,
    args=[
        Arg(name="provider_name",
            description="Name of the provider to view documentation for",
            required=True),
        Arg(name="doc_dir",
            description="Directory containing the documentation",
            required=False),
        Arg(name="format",
            description="Output format (markdown or html)",
            required=False)
    ],
    image="pandoc/core:latest"
)

# Export Provider Documentation Tool
export_provider_docs_tool = CrossplaneTool(
    name="provider_docs_export",
    description="Export Crossplane provider documentation to various formats",
    content="""
    if [ -z "$PROVIDER_NAME" ]; then
        PROVIDERS=$(ls ${DOC_DIR:-provider-docs}/*.md | xargs -n 1 basename | cut -d. -f1)
    else
        PROVIDERS=$PROVIDER_NAME
    fi

    for provider in $PROVIDERS; do
        DOC_FILE="${DOC_DIR:-provider-docs}/$provider.md"
        
        if [ ! -f "$DOC_FILE" ]; then
            echo "Documentation not found for $provider"
            continue
        fi

        case "${FORMAT:-pdf}" in
            "pdf")
                pandoc "$DOC_FILE" -f markdown -t pdf -o "${OUTPUT_DIR:-provider-docs}/$provider.pdf"
                echo "PDF exported to ${OUTPUT_DIR:-provider-docs}/$provider.pdf"
                ;;
            "html")
                pandoc "$DOC_FILE" -f markdown -t html -s -o "${OUTPUT_DIR:-provider-docs}/$provider.html"
                echo "HTML exported to ${OUTPUT_DIR:-provider-docs}/$provider.html"
                ;;
            "docx")
                pandoc "$DOC_FILE" -f markdown -t docx -o "${OUTPUT_DIR:-provider-docs}/$provider.docx"
                echo "DOCX exported to ${OUTPUT_DIR:-provider-docs}/$provider.docx"
                ;;
            *)
                echo "Unsupported format: $FORMAT"
                echo "Supported formats: pdf, html, docx"
                exit 1
                ;;
        esac
    done

    if [ "$COMPRESS" = "true" ]; then
        tar -czf "${OUTPUT_DIR:-provider-docs}/provider-docs.tar.gz" -C "${OUTPUT_DIR:-provider-docs}" .
        echo "Documentation archive created at ${OUTPUT_DIR:-provider-docs}/provider-docs.tar.gz"
    fi
    """,
    args=[
        Arg(name="provider_name",
            description="Name of the provider to export documentation for (optional, exports all if not specified)",
            required=False),
        Arg(name="doc_dir",
            description="Directory containing the documentation",
            required=False),
        Arg(name="output_dir",
            description="Directory to store the exported documentation",
            required=False),
        Arg(name="format",
            description="Export format (pdf, html, or docx)",
            required=False),
        Arg(name="compress",
            description="Compress the exported documentation into an archive",
            required=False)
    ],
    image="pandoc/core:latest"
)

# Register documentation tools directly
try:
    print("\n=== Registering Documentation Tools ===")
    doc_tools = [
        generate_provider_docs_tool,
        view_provider_docs_tool,
        export_provider_docs_tool
    ]
    
    for tool in doc_tools:
        try:
            tool_registry.register("crossplane", tool)
            print(f"✅ Registered: {tool.name}")
        except Exception as e:
            print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
            raise
except Exception as e:
    print(f"❌ Failed to register documentation tools: {str(e)}", file=sys.stderr)
    raise

# Export tools
__all__ = [
    'generate_provider_docs_tool',
    'view_provider_docs_tool',
    'export_provider_docs_tool'
] 