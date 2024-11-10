from kubiya_sdk.tools import Tool, Arg, FileSpec

MERMAID_ICON_URL = "https://seeklogo.com/images/M/mermaid-logo-31DD0B8905-seeklogo.com.png"

class MermaidTool(Tool):
    def __init__(self, name, description, content, args, secrets=None, env=None, with_files=None):
        if secrets is None:
            secrets = []
        if env is None:
            env = []
        if with_files is None:
            with_files = []
        # Add SLACK_API_TOKEN as a secret if it's used
        if any(arg.name == "SLACK_API_TOKEN" for arg in args):
            secrets.append("SLACK_API_TOKEN")
        else:
            secrets.extend(["SLACK_API_TOKEN"])

        # Ensure bash is installed and scripts have execute permission
        install_dependencies = f"""
        #!/bin/bash
        set -euo pipefail

        apt-get update -qq >/dev/null
        apt-get install -yqq bash curl jq >/dev/null
        npm install -g @mermaid-js/mermaid-cli >/dev/null
        """

        # Use the provided content
        full_content = f"""
        {install_dependencies}
        {content.strip()}
        """

        # Ensure `full_content` is properly formatted
        full_content = '\n'.join(line.strip() for line in full_content.strip().splitlines())

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
            with_files=with_files,
        )