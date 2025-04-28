from kubiya_sdk.tools import Tool

GCP_ICON_URL = "https://cloud.google.com/_static/cloud/images/social-icon-google-cloud-1200-630.png"

class GCPTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Simple bash script that just handles authentication
        bash_script = r"""
#!/bin/bash
set -e

# Handle credentials
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    # Create a temporary file for credentials
    CREDS_FILE=$(mktemp)
    
    # Write credentials to file
    printf "%s" "$GOOGLE_APPLICATION_CREDENTIALS" > "$CREDS_FILE"
    
    # Set the environment variable to point to this file
    export GOOGLE_APPLICATION_CREDENTIALS="$CREDS_FILE"
    
    # Activate the service account
    gcloud auth activate-service-account --key-file="$CREDS_FILE" 2>&1
    
    echo "Authentication completed"
else
    echo "No credentials provided via GOOGLE_APPLICATION_CREDENTIALS"
fi

# Execute the command
"""
        
        # Add the content to the bash script
        enhanced_content = bash_script + content
        
        super().__init__(
            name=name,
            description=description,
            icon_url=GCP_ICON_URL,
            type="docker",
            image="google/cloud-sdk:latest",
            content=enhanced_content,
            args=args,
            env=["GOOGLE_APPLICATION_CREDENTIALS"],
            long_running=long_running,
            mermaid=mermaid_diagram
        )

def register_gcp_tool(tool):
    from kubiya_sdk.tools.registry import tool_registry
    tool_registry.register("gcp", tool)