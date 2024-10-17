from kubiya_sdk.tools import Tool

MERMAID_ICON_URL = "https://mermaid.js.org/favicon.svg"
NODE_IMAGE = "node:23-slim"

class DiagrammingTool(Tool):
    def __init__(self, name, description, content, args, long_running=False):
        mermaid_setup = """
        #!/bin/bash
        set -e # Exit on error
        if ! command -v npm &> /dev/null; then
            echo "npm is not installed. Installing npm..."
            apt-get update
            apt-get install -y npm
        fi
        if ! command -v mmdc &> /dev/null; then
            echo "mmdc is not installed. Installing mmdc..."
            npm install @mermaid-js/mermaid-cli
        fi
        """
        # The default env and secrets are for the mermaid_render_and_share tool
        # Built in slack tools will use these to find the slack channel and thread
        default_env = ["SLACK_CHANNEL_ID", "SLACK_THREAD_TS"]
        # The default secrets are for the mermaid_render_and_share tool
        # Built in slack tools will use these to find the slack api token
        default_secrets = ["SLACK_API_TOKEN"]
        modified_content = mermaid_setup + "\n" + content
        super().__init__(
            name=name,
            description=description,
            icon_url=MERMAID_ICON_URL,
            type="docker",
            image=NODE_IMAGE,
            env=default_env,
            secrets=default_secrets,
            content=modified_content,
            args=args,
            long_running=long_running,
        )
