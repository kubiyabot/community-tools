from kubiya_sdk.tools import Tool, Arg

MERMAID_ICON_URL = "https://seeklogo.com/images/M/mermaid-logo-31DD0B8905-seeklogo.com.png"

class MermaidTool(Tool):
    def __init__(self, name, description, content, args, secrets=None, env=None):
        if secrets is None:
            secrets = []
        if env is None:
            env = []
        # Add SLACK_API_TOKEN as a secret
        secrets.extend(["SLACK_API_TOKEN"])

        # Prepend the dependency installation to the content
        full_content = f"""\
#!/bin/sh
set -eu

# Install dependencies silently
if ! command -v mmdc > /dev/null 2>&1; then
    echo "Installing dependencies..."
    apt-get update > /dev/null 2>&1
    apt-get install -y curl jq > /dev/null 2>&1
    npm install -g @mermaid-js/mermaid-cli > /dev/null 2>&1
    curl -s -L -o /usr/local/bin/slack "https://raw.githubusercontent.com/rockymadden/slack-cli/master/src/slack"
    chmod +x /usr/local/bin/slack
fi

{content.strip()}
"""

        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="node:16-slim",
            content=full_content,
            args=args,
            icon_url=MERMAID_ICON_URL,
            secrets=secrets,
            env=env,
        )