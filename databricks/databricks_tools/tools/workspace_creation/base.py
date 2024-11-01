from kubiya_sdk.tools.models import Tool
from .constants import (
    AWS_SECRETS,
    AZURE_SECRETS,
    DATABRICKS_ICON_URL,
    AWS_FILES,
    AWS_ENV,
    AZURE_ENV,
)

# Updated SETUP_SCRIPT with silent installation and engaging messages
SETUP_SCRIPT = """#!/bin/bash
set -euo pipefail

# Share context with the user on what's happening
echo -e "\\n🔧 Starting the setup for Databricks Workspace provisioning..."
echo -e "🔍 Performing pre-flight checks..."

# Check and install runtime dependencies silently
function check_dependencies {
    missing_deps=""
    for cmd in curl jq git bash; do
        if ! command -v "$cmd" > /dev/null 2>&1; then
            missing_deps="$missing_deps $cmd"
        fi
    done

    if [ -n "$missing_deps" ]; then
        if apk update > /dev/null 2>&1 && apk add --no-cache $missing_deps > /dev/null 2>&1; then
            echo -e "✅ Pre-flight checks passed!"
        else
            echo -e "❌ Failed to install dependencies: $missing_deps"
            exit 1
        fi
    else
        echo -e "✅ Ready to proceed!"
    fi
}

# Ensure dependencies are installed
check_dependencies

echo -e "🚀 Buckle up! Your Databricks workspace is being crafted with care... ✨\nThis may take a few minutes, but great things are worth waiting for! 🌟"

# Main script starts here
echo -e "🚀 Initiating Databricks workspace creation sequence..."
"""

class DatabricksTerraformTool(Tool):
    def __init__(
        self,
        name,
        description,
        content,
        args,
        env,
        secrets,
        long_running=False,
        with_files=None,
        image="hashicorp/terraform:latest",
        mermaid=None,
    ):

        # Prepend setup script to the content
        full_content = SETUP_SCRIPT + content

        super().__init__(
            name=name,
            description=description,
            icon_url=DATABRICKS_ICON_URL,
            type="docker",
            image=image,
            content=full_content,
            args=args,
            env=env,
            secrets=secrets,
            long_running=long_running,
            with_files=with_files,
            mermaid=mermaid,
        )

class DatabricksAWSTerraformTool(DatabricksTerraformTool):
    def __init__(self, name, description, content, args, long_running=False, mermaid=None):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            long_running=long_running,
            with_files=AWS_FILES,
            env=AWS_ENV,
            secrets=AWS_SECRETS,
            mermaid=mermaid,
        )

class DatabricksAzureTerraformTool(DatabricksTerraformTool):
    def __init__(self, name, description, content, args, long_running=False, mermaid=None, with_files=None):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            env=AZURE_ENV,
            secrets=AZURE_SECRETS,
            with_files=with_files,
            long_running=long_running,
            mermaid=mermaid,
        )