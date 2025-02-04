from kubiya_sdk.tools.models import Tool, Arg
from pydantic import HttpUrl
from typing import Optional

AUDI_LOGO_URL = HttpUrl(
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ3jLdiRIffyVvYjJSgZqFzc73YJSfqcRbR6Q&s"
)

COMMON_ENVS = [
    "OPENSHIFT_URL",
    "OPENSHIFT_USERNAME",
]

COMMON_SECRETS = [
    "OPENSHIFT_PASSWORD",
]


class BaseOCTool(Tool):
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        args: list[Arg] = [],
        env: list[str] = [],
        secrets: list[str] = [],
        long_running=False,
    ):
        for common_env in COMMON_ENVS:
            if common_env not in env:
                env.append(common_env)
        for common_secret in COMMON_SECRETS:
            if common_secret not in secrets:
                secrets.append(common_secret)
        
        content = f"""
set -e

# Function to handle command output and remove ANSI color codes
handle_output() {{
    sed 's/\\x1b\\[[0-9;]*[a-zA-Z]//g' | tr -d '\\r' | sed 's/</\\</g' | sed 's/>/\\>/g'
}}

# Login with username/password
if ! oc login "$OPENSHIFT_URL" \\
    --username="$OPENSHIFT_USERNAME" \\
    --password="$OPENSHIFT_PASSWORD" \\
    --insecure-skip-tls-verify=true \\
    2>/dev/null; then
    echo "Failed to login to OpenShift cluster - check your credentials and URL" | handle_output
    exit 1
fi

# Execute the actual command with output handling
{{
{content}
}} 2>&1 | handle_output
"""

        super().__init__(
            name=name,
            description=description,
            icon_url=AUDI_LOGO_URL,
            type="docker",
            image="openshift/origin-cli:latest",
            content=content,
            args=args,
            env=env,
            secrets=secrets,
            long_running=long_running,
        )
