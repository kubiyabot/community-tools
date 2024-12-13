from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.registry import tool_registry

KUBIYA_ICON = "https://www.finsmes.com/wp-content/uploads/2022/10/Kubiya-logo-mark-color.png"
CLI_VERSION = "v0.0.6"
CLI_URL = f"https://github.com/kubiyabot/cli/releases/download/{CLI_VERSION}/kubiya-linux-amd64"
CLI_PATH = "/usr/local/bin/kubiya"

class KubiyaCliBase(Tool):
    """Base class for all Kubiya CLI tools"""
    
    def __init__(self, name, description, cli_command, args=None, mermaid=None):
        enhanced_command = f'''
#!/bin/sh
set -e

# Debug info
echo "Starting setup..."
uname -a
ls -la /usr/local/bin || true

# Install required packages if not already installed
if ! command -v curl >/dev/null 2>&1; then
    apk add --no-cache curl
fi

# Install Kubiya CLI if not already installed
if [ ! -f {CLI_PATH} ]; then
    echo "Installing Kubiya CLI..."
    mkdir -p /usr/local/bin
    curl -L {CLI_URL} -o {CLI_PATH}.tmp
    
    # Verify download
    if [ ! -f {CLI_PATH}.tmp ]; then
        echo "Download failed - file not found"
        exit 1
    fi
    
    echo "Download complete. File size:"
    ls -lh {CLI_PATH}.tmp
    
    # Make executable
    chmod +x {CLI_PATH}.tmp
    
    # Test binary
    if ./{CLI_PATH}.tmp --help >/dev/null 2>&1; then
        echo "Binary test successful"
        mv {CLI_PATH}.tmp {CLI_PATH}
    else
        echo "Binary test failed"
        file {CLI_PATH}.tmp
        exit 1
    fi
fi

# Verify CLI exists and is executable
if [ ! -x {CLI_PATH} ]; then
    echo "CLI not found or not executable at {CLI_PATH}"
    ls -la {CLI_PATH} || true
    exit 1
fi

# Ensure KUBIYA_API_KEY is set
if [ -z "$KUBIYA_API_KEY" ]; then
    echo "❌ Error: KUBIYA_API_KEY environment variable is required, on a Kubiya-managed environment, this is automatically set"
    exit 1
fi

# Set non-interactive mode
export KUBIYA_NON_INTERACTIVE=true

# Create temporary directory for operations if needed
if echo "{cli_command}" | grep -q "TEMP_DIR"; then
    TEMP_DIR=$(mktemp -d)
    
    cleanup() {{
        rm -rf "$TEMP_DIR"
    }}
    trap cleanup EXIT
    
    # Helper function for content files
    create_content_file() {{
        local content="$1"
        local file="$TEMP_DIR/content.md"
        echo "$content" > "$file"
        echo "$file"
    }}
fi

echo "Running command..."
# Execute command with full path
{cli_command.replace('kubiya ', f'{CLI_PATH} ')}
'''

        super().__init__(
            name=name,
            description=description,
            icon_url=KUBIYA_ICON,
            type="docker",
            image="alpine:latest",
            content=enhanced_command,
            args=args or [],
            secrets=["KUBIYA_API_KEY"],
            mermaid=mermaid,
        )

    @classmethod
    def register(cls, tool):
        """Register a tool with the Kubiya registry"""
        tool_registry.register("kubiya", tool)
        return tool

def create_tool(name, description, cli_command, args=None, mermaid=None):
    """Factory function to create and register a new Kubiya CLI tool"""
    tool = KubiyaCliBase(
        name=f"kubiya_{name}",
        description=description,
        cli_command=cli_command,
        args=args or [],
        mermaid=mermaid,
    )
    return KubiyaCliBase.register(tool)

__all__ = ['KubiyaCliBase', 'create_tool']