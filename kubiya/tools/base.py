from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.registry import tool_registry

KUBIYA_ICON = "https://www.finsmes.com/wp-content/uploads/2022/10/Kubiya-logo-mark-color.png"
CLI_IMAGE = "ghcr.io/kubiyabot/cli:latest"

class KubiyaCliBase(Tool):
    """Base class for all Kubiya CLI tools"""
    
    def __init__(self, name, description, cli_command, args=None):
        # Ensure non-interactive mode and JSON output by default
        enhanced_command = f'''
#!/bin/sh
set -e

echo "🚀 Starting {name}..."

# Ensure KUBIYA_API_KEY is set
if [ -z "$KUBIYA_API_KEY" ]; then
    echo "❌ Error: KUBIYA_API_KEY environment variable is required"
    exit 1
fi

# Set non-interactive mode
export KUBIYA_NON_INTERACTIVE=true

# Create temporary directory for operations if needed
if echo "{cli_command}" | grep -q "TEMP_DIR"; then
    TEMP_DIR=$(mktemp -d)
    echo "📁 Created temporary workspace: $TEMP_DIR"
    
    cleanup() {{
        echo "🧹 Cleaning up temporary files..."
        rm -rf "$TEMP_DIR"
        echo "✨ Cleanup complete"
    }}
    trap cleanup EXIT
    
    # Helper function for content files
    create_content_file() {{
        local content="$1"
        local file="$TEMP_DIR/content.md"
        echo "$content" > "$file"
        echo "📝 Created temporary content file: $file"
        echo "$file"
    }}
fi

# Execute command
{cli_command}

echo "✅ Operation completed successfully"
'''

        super().__init__(
            name=name,
            description=description,
            icon_url=KUBIYA_ICON,
            type="docker",
            image=CLI_IMAGE,
            content=enhanced_command,
            args=args or [],
            secrets=["KUBIYA_API_KEY"],
        )

    @classmethod
    def register(cls, tool):
        """Register a tool with the Kubiya registry"""
        tool_registry.register("kubiya", tool)
        return tool

def create_tool(name, description, cli_command, args=None):
    """Factory function to create and register a new Kubiya CLI tool"""
    tool = KubiyaCliBase(
        name=f"kubiya_{name}",
        description=description,
        cli_command=cli_command,
        args=args or []
    )
    return KubiyaCliBase.register(tool)

__all__ = ['KubiyaCliBase', 'create_tool']