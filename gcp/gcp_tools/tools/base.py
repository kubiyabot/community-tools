from kubiya_sdk.tools import Tool
import json

GCP_ICON_URL = "https://cloud.google.com/_static/cloud/images/social-icon-google-cloud-1200-630.png"

class GCPTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Minimal bash script for credential handling
        bash_script = r"""
#!/bin/sh
set -e

# Enable verbose output
set -x

# Handle credentials
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "Setting up GCP credentials..."
    # Create a temporary file for credentials
    CREDS_FILE=$(mktemp)
    
    # Decode base64 credentials
    echo "$GOOGLE_APPLICATION_CREDENTIALS" | base64 -d > "$CREDS_FILE"
    
    # Install required packages
    echo "Installing required packages..."
    apk update && apk add --no-cache curl python3 bash gnupg
    
    # Install gcloud CLI
    echo "Installing gcloud CLI..."
    curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-latest-linux-x86_64.tar.gz
    mkdir -p /usr/local/gcloud
    tar -xzf google-cloud-cli-latest-linux-x86_64.tar.gz -C /usr/local/gcloud
    /usr/local/gcloud/google-cloud-sdk/install.sh --quiet
    export PATH=$PATH:/usr/local/gcloud/google-cloud-sdk/bin
    
    # Activate the service account
    echo "Activating service account..."
    gcloud auth activate-service-account --key-file="$CREDS_FILE"
    
    # Execute the command
    echo "Executing main script..."
    {
"""
        
        # Add the content to the bash script
        enhanced_content = bash_script + content + r"""
    } 
    echo "Script execution completed."
else
    echo "No credentials provided via GOOGLE_APPLICATION_CREDENTIALS"
    exit 1
fi
"""
        
        super().__init__(
            name=name,
            description=description,
            icon_url=GCP_ICON_URL,
            type="docker",
            image="alpine:latest",
            content=enhanced_content,
            args=args,
            env=["GITLAB_REPO_URL"],
            secrets=["GITLAB_TOKEN", "GOOGLE_APPLICATION_CREDENTIALS"],
            long_running=long_running,
            mermaid=mermaid_diagram
        )

def register_gcp_tool(tool):
    from kubiya_sdk.tools.registry import tool_registry
    tool_registry.register("gcp", tool)