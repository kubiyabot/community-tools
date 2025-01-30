from kubiya_sdk.tools import Tool, Arg, FileSpec, ServiceSpec
from kubiya_sdk.tools.models import ImageProvider, Auth

MERMAID_ICON_URL = "https://seeklogo.com/images/M/mermaid-logo-31DD0B8905-seeklogo.com.png"

class MermaidTool(Tool):
    def __init__(self, name, description, args, secrets=None, env=None, with_files=None):
        if secrets is None:
            secrets = []
        if env is None:
            env = []
        if with_files is None:
            with_files = []
        secrets.extend(["JF_SECRET_PASS"])

        # Find the script name from with_files
        script_files = [file_spec.destination for file_spec in with_files if file_spec.destination.endswith('.sh')]
        if not script_files:
            raise ValueError("No shell script provided in with_files.")
        script_path = script_files[0]

        # Build the content that installs dependencies and runs the shell script
        content = f"""#!/bin/sh
set -e

echo "🎨 Setting up environment..."

# Install required packages
apk add curl jq >/dev/null 2>&1

# Install slack-cli
curl -s -L -o /usr/local/bin/slack \
    https://raw.githubusercontent.com/rockymadden/slack-cli/master/src/slack && \
    chmod +x /usr/local/bin/slack

# Prepare script
mkdir -p /tmp/scripts
chmod +x {script_path}

# Run script
exec {script_path}
"""

        # Define the Mermaid service
        mermaid_service = ServiceSpec(
            name="mermaid",
            image="trialc5eche.jfrog.io/test-docker/mermaid-server",
            exposed_ports=[80]
        )

        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="trialc5eche.jfrog.io/test-docker/mermaid-server",
            image_provider=ImageProvider(
                kind="jfrog",
                auth=[
                Auth(
                    name="username",
                    value="avi.rosenberg@kubiya.ai",
                ),
                Auth(
                    name="password",
                    value_from={
                        "secret": "JF_SECRET_PASS"
                    }
                )]
            ),
            content=content,
            args=args,
            icon_url=MERMAID_ICON_URL,
            secrets=secrets,
            env=env,
            with_files=with_files,
            with_services=[mermaid_service]
        )
