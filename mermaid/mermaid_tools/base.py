from kubiya_sdk.tools import Tool, Arg

MERMAID_ICON_URL = "https://seeklogo.com/images/M/mermaid-logo-31DD0B8905-seeklogo.com.png"

class MermaidTool(Tool):
    def __init__(
        self, name, description, content, args, secrets=None, env=None
    ):
        if secrets is None:
            secrets = []
        if env is None:
            env = []

        # Add SLACK_API_TOKEN as a secret
        secrets.extend(["SLACK_API_TOKEN"])

        # Prepare the script content without shebang
        script_content = f"""
set -euo pipefail

# Install dependencies silently
if ! command -v mmdc &>/dev/null; then
    echo "Installing dependencies..."
    apt-get update >/dev/null 2>&1
    apt-get install -y bash curl jq >/dev/null 2>&1
    npm install -g @mermaid-js/mermaid-cli >/dev/null 2>&1
fi

{content.strip()}
"""

        # Escape any single quotes in the script content
        escaped_script_content = script_content.replace("'", "'\"'\"'")

        # Build the full command to execute the script with bash
        full_command = f"/bin/bash -c '{escaped_script_content}'"

        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="node:16-slim",
            command=full_command,
            args=args,
            icon_url=MERMAID_ICON_URL,
            secrets=secrets,
            env=env,
        )