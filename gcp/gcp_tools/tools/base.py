from kubiya_sdk.tools import Tool
import json

GCP_ICON_URL = "https://cloud.google.com/_static/cloud/images/social-icon-google-cloud-1200-630.png"

class GCPTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Enhanced bash script with better credential handling
        bash_script = r"""
#!/bin/bash
set -e

# Handle credentials - expecting JSON content in GOOGLE_APPLICATION_CREDENTIALS
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    # Create a temporary file for credentials
    CREDS_FILE=$(mktemp)
    
    # Write credentials to file, ensuring proper JSON format
    printf "%s" "$GOOGLE_APPLICATION_CREDENTIALS" > "$CREDS_FILE"
    
    # Validate JSON format without printing contents
    if ! jq empty "$CREDS_FILE" 2>/dev/null; then
        echo "Error: Invalid JSON format in credentials"
        echo "Please check that GOOGLE_APPLICATION_CREDENTIALS contains valid JSON"
        rm -f "$CREDS_FILE"  # Clean up the file
        exit 1
    fi
    
    # Set the environment variable to point to this file
    export GOOGLE_APPLICATION_CREDENTIALS="$CREDS_FILE"
    
    # Activate the service account with error handling
    if ! gcloud auth activate-service-account --key-file="$CREDS_FILE" 2>/dev/null; then
        echo "Authentication failed."
        echo "Please check that the service account has the necessary permissions."
        # Only show non-sensitive information
        echo "Project ID: $(jq -r '.project_id // "Not found"' "$CREDS_FILE" 2>/dev/null)"
        echo "Client email: $(jq -r '.client_email // "Not found"' "$CREDS_FILE" 2>/dev/null)"
        rm -f "$CREDS_FILE"  # Clean up the file
        exit 1
    fi
    
    echo "Authentication completed successfully"
    
    # Execute the command (we'll clean up the file afterward)
    {
"""
        
        # Add the content to the bash script
        enhanced_content = bash_script + content + r"""
    } 
    
    # Clean up after command execution
    rm -f "$CREDS_FILE"
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