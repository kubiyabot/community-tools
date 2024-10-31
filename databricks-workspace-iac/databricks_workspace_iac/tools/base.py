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

# Friendly message with emoji
echo -e "\\n🔧 Starting the setup for Databricks Workspace provisioning..."

# Check and install runtime dependencies silently
function check_dependencies {
    missing_deps=""
    for cmd in curl jq git bash; do
        if ! command -v "$cmd" > /dev/null 2>&1; then
            missing_deps="$missing_deps $cmd"
        fi
    done

    if [ -n "$missing_deps" ]; then
        echo -e "⚙️  This workflow requires additional dependencies which haven't been cached yet."
        echo -e "🚀 Installing missing dependencies: $missing_deps"
        if apk update > /dev/null 2>&1 && apk add --no-cache $missing_deps > /dev/null 2>&1; then
            echo -e "✅ Dependencies installed successfully!"
        else
            echo -e "❌ Failed to install dependencies: $missing_deps"
            exit 1
        fi
    else
        echo -e "✅ All dependencies are already installed!"
    fi
}

# Ensure dependencies are installed
check_dependencies

# Main script starts here
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
        long_running=True,
        with_files=None,
        image="hashicorp/terraform:latest",
        mermaid=None,
    ):
        # Remove any shebang lines from content to prevent multiple shebangs
        content_no_shebang = "\n".join(
            line for line in content.splitlines() if not line.startswith("#!")
        )

        # Prepend setup script to the content
        full_content = SETUP_SCRIPT + content_no_shebang

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
    def __init__(self, name, description, content, args, long_running=False, mermaid=None):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            env=AZURE_ENV,
            secrets=AZURE_SECRETS,
            long_running=long_running,
            mermaid=mermaid,
            # with_files=AZURE_FILES,
        )