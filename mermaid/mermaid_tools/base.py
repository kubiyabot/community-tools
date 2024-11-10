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

        # Find the script name from with_files
        script_files = [file_spec.destination for file_spec in with_files if file_spec.destination.endswith('.sh')]
        if not script_files:
            raise ValueError("No shell script provided in with_files.")
        script_path = script_files[0]

        # Build the content that installs dependencies and runs the shell script
        content = f"""
        #!/bin/sh
        set -e

        echo "🎨 Setting up..."

        # Install Chrome and set environment variables
        apk add --no-cache chromium curl jq >/dev/null 2>&1
        export PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
        export PATH="/home/mermaidcli/node_modules/.bin:$PATH"

        # Create puppeteer config
        cat > /puppeteer-config.json << 'EOF'
{{
    "executablePath": "/usr/bin/chromium",
    "args": [
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--disable-setuid-sandbox"
    ]
}}
EOF

        # Install slack-cli
        curl -s -L -o /usr/local/bin/slack \
            https://raw.githubusercontent.com/rockymadden/slack-cli/master/src/slack && \
            chmod +x /usr/local/bin/slack

        # Create directories and set permissions
        mkdir -p /tmp/scripts /data
        chown -R mermaidcli:mermaidcli /data /tmp/scripts
        chmod 755 /tmp/scripts

        # Make script executable
        chmod 755 {script_path}
        chown mermaidcli:mermaidcli {script_path}

        # Switch to mermaidcli user and run the script
        cd /data
        exec su mermaidcli -c "{script_path}"
        """

        # Clean up content by stripping leading/trailing whitespace
        content = '\n'.join(line.strip() for line in content.strip().splitlines())

        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="minlag/mermaid-cli:latest",
            content=content,
            args=args,
            icon_url=MERMAID_ICON_URL,
            secrets=secrets,
            env=env,
            with_files=with_files,
        )