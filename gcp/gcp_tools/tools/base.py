from kubiya_sdk.tools import Tool
import json

GCP_ICON_URL = "https://cloud.google.com/_static/cloud/images/social-icon-google-cloud-1200-630.png"

class GCPTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Enhanced bash script with better credential handling
        bash_script = r"""
#!/bin/bash
set -e

# Handle credentials
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    # Create a temporary file for credentials
    CREDS_FILE=$(mktemp)
    
    # Write credentials to file, ensuring proper JSON format
    printf "%s" "$GOOGLE_APPLICATION_CREDENTIALS" > "$CREDS_FILE"
    
    # Validate JSON format
    if ! jq empty "$CREDS_FILE" 2>/dev/null; then
        echo "Error: Invalid JSON format in credentials"
        cat "$CREDS_FILE" | head -n 5
        exit 1
    fi
    
    # Set the environment variable to point to this file
    export GOOGLE_APPLICATION_CREDENTIALS="$CREDS_FILE"
    
    # Activate the service account with error handling
    if ! gcloud auth activate-service-account --key-file="$CREDS_FILE" 2>&1; then
        echo "Authentication failed. Checking credential file format..."
        # Print first few lines of file for debugging (without sensitive data)
        echo "Credential file structure:"
        jq 'keys' "$CREDS_FILE" 2>/dev/null || echo "Not valid JSON"
        exit 1
    fi
    
    echo "Authentication completed successfully"
else
    echo "No credentials provided via GOOGLE_APPLICATION_CREDENTIALS"
    exit 1
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