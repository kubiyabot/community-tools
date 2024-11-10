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
        # No need for SLACK_CHANNEL_ID or SLACK_THREAD_TS in env
        full_content = f"""\
#!/bin/sh
set -euo pipefail

# Install dependencies silently
if ! command -v mmdc > /dev/null 2>&1; then
    echo "Installing dependencies..."
    apk add --no-cache nodejs npm curl jq > /dev/null 2>&1
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
            image="alpine:3.14",
            content=full_content,
            args=args,
            icon_url=MERMAID_ICON_URL,
            secrets=secrets,
            env=env,
        ) 