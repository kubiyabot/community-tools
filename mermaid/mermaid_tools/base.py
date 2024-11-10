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

        echo "🎨 Setting up environment..." 2>&1 | tee -a "$LOG_FILE"

        # Install minimal dependencies for Slack CLI
        apt-get update -qq && apt-get install -yqq --no-install-recommends curl jq >/dev/null 2>&1

        # Install slack-cli
        curl -s -L -o /usr/local/bin/slack \
            https://raw.githubusercontent.com/rockymadden/slack-cli/master/src/slack && \
            chmod +x /usr/local/bin/slack

        # Make script executable
        chmod +x {script_path}

        # Run the main script and capture output
        echo "Running main script..." 2>&1 | tee -a "$LOG_FILE"
        {script_path} 2>&1 | tee -a "$LOG_FILE" || {{
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
            image="minlag/mermaid-cli:latest",  # Using official Mermaid CLI image
            content=content,
            args=args,
            icon_url=MERMAID_ICON_URL,
            secrets=secrets,
            env=env,
            with_files=with_files,
        )