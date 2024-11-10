from kubiya_sdk.tools import Tool, Arg, FileSpec

MERMAID_ICON_URL = "https://seeklogo.com/images/M/mermaid-logo-31DD0B8905-seeklogo.com.png"

class MermaidTool(Tool):
    def __init__(self, name, description, args, secrets=None, env=None, with_files=None):
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

        # Find the script name from with_files
        script_files = [file_spec.destination for file_spec in with_files if file_spec.destination.endswith('.sh')]
        if not script_files:
            raise ValueError("No shell script provided in with_files.")
        script_path = script_files[0]

        # Build the content that installs dependencies and runs the shell script
        content = f"""
        #!/bin/bash
        set -e

        echo "🎨 Setting up environment..."

        # Ensure non-interactive installation
        export DEBIAN_FRONTEND=noninteractive

        # Install Chrome dependencies
        apt-get update -qq >/dev/null
        apt-get install -yqq --no-install-recommends \
            curl \
            chromium \
            libglib2.0-0 \
            libnss3 \
            libatk1.0-0 \
            libatk-bridge2.0-0 \
            libcups2 \
            libdrm2 \
            libxkbcommon0 \
            libxcomposite1 \
            libxdamage1 \
            libxfixes3 \
            libxrandr2 \
            libgbm1 \
            libasound2 \
            jq >/dev/null 2>&1

        # Install mermaid-cli
        npm install -g @mermaid-js/mermaid-cli@latest >/dev/null 2>&1

        # Install slack-cli
        curl -s -L -o /usr/local/bin/slack https://raw.githubusercontent.com/rockymadden/slack-cli/master/src/slack
        chmod +x /usr/local/bin/slack

        # Set Chrome path for Puppeteer
        export PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

        # Make script executable and run it
        chmod +x {script_path}
        exec {script_path}
        """

        # Clean up content by stripping leading/trailing whitespace
        content = '\n'.join(line.strip() for line in content.strip().splitlines())

        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="node:18-slim",
            content=content,
            args=args,
            icon_url=MERMAID_ICON_URL,
            secrets=secrets,
            env=env,
            with_files=with_files,
        )