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

        # Add mmdc to PATH
        export PATH="/home/mermaidcli/node_modules/.bin:$PATH"

        # Install minimal dependencies for Slack CLI
        apk add --no-cache curl jq >/dev/null 2>&1

        # Install slack-cli
        curl -s -L -o /usr/local/bin/slack \
            https://raw.githubusercontent.com/rockymadden/slack-cli/master/src/slack && \
            chmod +x /usr/local/bin/slack

        # Make script executable
        chmod +x {script_path}

        # Run the script
        exec {script_path}
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