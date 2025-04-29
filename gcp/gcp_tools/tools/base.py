from kubiya_sdk.tools import Tool
import json

GCP_ICON_URL = "https://cloud.google.com/_static/cloud/images/social-icon-google-cloud-1200-630.png"

class GCPTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Minimal ash script for credential handling
        bash_script = r"""
#!/bin/sh
set -e

# Handle credentials
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    # Create a temporary file for credentials
    CREDS_FILE=$(mktemp)
    
    # Decode base64 credentials
    echo "$GOOGLE_APPLICATION_CREDENTIALS" | base64 -d > "$CREDS_FILE"
    
    # Install minimal gcloud CLI components
    echo "Installing minimal gcloud CLI components..."
    apk update && apk add --no-cache python3 curl bash
    
    # Install a minimal version of the gcloud CLI
    curl -sSL https://sdk.cloud.google.com > /tmp/gcli && 
    bash /tmp/gcli --disable-prompts --install-dir=/usr/local --only-core
    export PATH=$PATH:/usr/local/google-cloud-sdk/bin
    
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
            image="alpine:3.18",  # Using a specific Alpine version for stability
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