from kubiya_sdk.tools import Tool
import json

GCP_ICON_URL = "https://cloud.google.com/_static/cloud/images/social-icon-google-cloud-1200-630.png"

class GCPTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Minimal bash script for credential handling
        bash_script = r"""
#!/usr/bin/env bash
set -e

# Handle credentials
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    # Create a temporary file for credentials
    CREDS_FILE=$(mktemp)
    
    # Decode base64 credentials
    echo "$GOOGLE_APPLICATION_CREDENTIALS" | base64 -d > "$CREDS_FILE"
    
    # Install gcloud CLI
    echo "Installing minimal gcloud CLI..."
    apt-get update -qq && apt-get install -y -qq curl python3 apt-transport-https ca-certificates gnupg > /dev/null 2>&1
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
    apt-get update -qq && apt-get install -y -qq google-cloud-cli > /dev/null 2>&1
    
    # Activate the service account
    gcloud auth activate-service-account --key-file="$CREDS_FILE"
    
    # Execute the command
    {
"""
        
        # Add the content to the bash script
        enhanced_content = bash_script + content + r"""
    } 
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
            image="debian:bullseye-slim",  # Much smaller base image
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