from kubiya_sdk.tools.models import Tool
from .constants import AWS_SECRETS, AZURE_SECRETS, DATABRICKS_ICON_URL, AWS_FILES, AWS_ENV, AZURE_ENV, COMMON_SECRETS

SETUP_SCRIPT = """
# Install runtime dependencies
apk update && apk add --no-cache curl jq git bash

# Function to check and install dependencies
check_dependencies() {
    local missing_deps=()
    for cmd in curl jq git bash; do
        if ! command -v $cmd &> /dev/null; then
            missing_deps+=($cmd)
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo "Missing required dependencies: ${missing_deps[*]}"
        echo "Installing missing dependencies..."
        apk update && apk add --no-cache "${missing_deps[@]}"
    fi
}

# Ensure dependencies are installed
check_dependencies

# Main script starts here
"""

class DatabricksTerraformTool(Tool):
    def __init__(self, name, description, content, args, env, secrets, long_running=True, with_files=None, image="hashicorp/terraform:latest", mermaid=None):
        # Prepend setup script to the content
        full_content = SETUP_SCRIPT + content
        
        super().__init__(
            name=name,
            description=description,
            icon_url=DATABRICKS_ICON_URL,
            type="docker",
            image="hashicorp/terraform:latest",
            content=full_content,
            args=args,
            env=env,
            secrets=secrets,
            long_running=long_running,
            with_files=with_files,
            mermaid=mermaid
        )

class DatabricksAWSTerraformTool(DatabricksTerraformTool):
    def __init__(self, name, description, content, args, long_running=True, mermaid=None):
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
    def __init__(self, name, description, content, args, long_running=True, mermaid=None):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            env=AZURE_ENV,
            secrets=AZURE_SECRETS,
            long_running=long_running,
            mermaid=mermaid,
            #with_files=AZURE_FILES, ## Kubiya does not support native integration with Azure yet, it is possible to use environment variables / secrets to pass in the execution environment. (eg. Team mate settings)
        )