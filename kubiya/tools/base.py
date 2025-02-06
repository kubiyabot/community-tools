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
set -ex

echo "Starting Kubiya CLI setup..."

# Create directories
mkdir -p /usr/local/bin

# Install required packages
echo "Installing required packages..."
apk update
apk add --no-cache curl jq gcompat || {{
    echo "Failed to install required packages"
    exit 1
}}

# Download CLI binary
echo "Downloading Kubiya CLI from {CLI_URL}..."
if ! curl -L -f {CLI_URL} -o {CLI_PATH}; then
    echo "Failed to download CLI binary"
    exit 1
fi

echo "Setting executable permissions..."
chmod +x {CLI_PATH}

# Create symbolic link for library compatibility
ln -sf /lib/ld-linux-x86-64.so.2 /lib64/ld-linux-x86-64.so.2 || true

# Verify CLI installation
echo "Verifying CLI installation..."
if ! {CLI_PATH} --help >/dev/null 2>&1; then
    echo "Failed to verify CLI installation"
    exit 1
fi

echo "Environment setup complete. Executing command..."
echo "Command to execute: {cli_command}"

# Execute command with API key
export KUBIYA_API_KEY="${{KUBIYA_API_KEY}}"
{CLI_PATH} {cli_command} || {{
    echo "Command failed with exit code $?"
    exit 1
}}
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