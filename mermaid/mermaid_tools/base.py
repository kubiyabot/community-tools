from kubiya_sdk.tools import Tool, Arg, FileSpec, ServiceSpec

MERMAID_ICON_URL = "https://seeklogo.com/images/M/mermaid-logo-31DD0B8905-seeklogo.com.png"

class MermaidTool(Tool):
    def __init__(self, name, description, args, secrets=None, env=None, with_files=None):
        if secrets is None:
            secrets = []
        if env is None:
            env = []
        if with_files is None:
            with_files = []

        # Find the script name from with_files
        script_files = [file_spec.destination for file_spec in with_files if file_spec.destination.endswith('.sh')]
        if not script_files:
            raise ValueError("No shell script provided in with_files.")
        script_path = script_files[0]

        # Build the content that installs dependencies and runs the shell script
        content = f"""#!/bin/sh
set -e

echo "🎨 Preparing to draw diagram..."

# Install required packages if not already installed
if ! command -v curl >/dev/null || ! command -v jq >/dev/null; then
    echo "📦 Installing required packages..."
    apk add curl jq >/dev/null 2>&1
fi

# Install slack-cli if not already installed
if [ ! -f "/usr/local/bin/slack" ]; then
    echo "📥 Connecting to Slack..."
    curl -s -L -o /usr/local/bin/slack \
        https://raw.githubusercontent.com/rockymadden/slack-cli/master/src/slack && \
        chmod +x /usr/local/bin/slack
fi

# Prepare script
mkdir -p /tmp/scripts
chmod +x {script_path}

exec {script_path}
"""

        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="alpine:3.14",
            content=content,
            args=args,
            icon_url=MERMAID_ICON_URL,
            secrets=secrets,
            env=env,
            with_files=with_files,
            with_services=[ServiceSpec(name="mermaidsvc",image="ghcr.io/kubiyabot/mermaid-server:v0.0.0",exposed_ports=[80])]
        )
