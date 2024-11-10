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
        #!/bin/sh
        set -e

        # Create log file for error tracking
        LOG_FILE=$(mktemp)

        echo "🎨 Setting up environment..." 2>&1 | tee -a "$LOG_FILE"

        # Install system dependencies
        apk add --no-cache \
            chromium \
            curl \
            jq \
            bash \
            >/dev/null 2>&1

        # Set up environment variables
        export CHROME_BIN="/usr/bin/chromium-browser"
        export PUPPETEER_SKIP_DOWNLOAD="true"

        # Create necessary directories
        mkdir -p /data /tmp/scripts

        # Install mermaid-cli globally
        cd /tmp
        npm install @mermaid-js/mermaid-cli >/dev/null 2>&1
        ln -s /tmp/node_modules/.bin/mmdc /usr/local/bin/mmdc

        # Install slack-cli
        curl -s -L -o /usr/local/bin/slack \
            https://raw.githubusercontent.com/rockymadden/slack-cli/master/src/slack && \
            chmod +x /usr/local/bin/slack

        # Make script executable
        chmod +x {script_path}

        # Create puppeteer config
        cat > /puppeteer-config.json << 'EOF'
        {{
            "args": ["--no-sandbox", "--disable-gpu"]
        }}
EOF

        # Verify mmdc installation
        if ! which mmdc >/dev/null 2>&1; then
            echo "❌ mmdc not found in PATH. Error log:" 2>&1
            cat "$LOG_FILE"
            exit 1
        fi

        # Run the main script and capture output
        echo "Running main script..." 2>&1 | tee -a "$LOG_FILE"
        cd /data  # Change to /data directory as expected by mermaid-cli
        bash {script_path} 2>&1 | tee -a "$LOG_FILE" || {{
            echo "❌ Script execution failed. Error log:" 2>&1
            cat "$LOG_FILE"
            exit 1
        }}

        # Clean up
        rm -f "$LOG_FILE"
        """

        # Clean up content by stripping leading/trailing whitespace
        content = '\n'.join(line.strip() for line in content.strip().splitlines())

        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="node:18-alpine",  # Using Node.js Alpine image
            content=content,
            args=args,
            icon_url=MERMAID_ICON_URL,
            secrets=secrets,
            env=env,
            with_files=with_files,
        )