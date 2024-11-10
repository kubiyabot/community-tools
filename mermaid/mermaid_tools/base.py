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

        # Create log file for error tracking
        LOG_FILE=$(mktemp)
        exec 1> >(tee -a "$LOG_FILE")
        exec 2> >(tee -a "$LOG_FILE" >&2)

        echo "🎨 Setting up environment..."

        # Ensure non-interactive installation
        export DEBIAN_FRONTEND=noninteractive

        echo "Installing system dependencies..."
        if ! (apt-get update -qq && \
            apt-get install -yqq --no-install-recommends \
            curl chromium chromium-common chromium-sandbox \
            libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 \
            libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
            libxfixes3 libxrandr2 libgbm1 libasound2 jq) 2>&1; then
            echo "❌ Failed to install system dependencies. Full log:"
            cat "$LOG_FILE"
            exit 1
        fi

        echo "Installing mermaid-cli..."
        if ! npm install -g @mermaid-js/mermaid-cli@latest 2>&1; then
            echo "❌ Failed to install mermaid-cli. Full log:"
            cat "$LOG_FILE"
            exit 1
        fi

        echo "Installing slack-cli..."
        if ! (curl -s -L -o /usr/local/bin/slack \
            https://raw.githubusercontent.com/rockymadden/slack-cli/master/src/slack && \
            chmod +x /usr/local/bin/slack) 2>&1; then
            echo "❌ Failed to install slack-cli. Full log:"
            cat "$LOG_FILE"
            exit 1
        fi

        # Set Chrome path for Puppeteer
        export PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
        export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

        # Make script executable
        chmod +x {script_path}

        echo "Running main script..."
        if ! {script_path} 2>&1; then
            echo "❌ Script execution failed. Full log:"
            cat "$LOG_FILE"
            exit 1
        fi

        # Clean up
        rm -f "$LOG_FILE"
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