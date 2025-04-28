from kubiya_sdk.tools import Tool
import json

GCP_ICON_URL = "https://cloud.google.com/_static/cloud/images/social-icon-google-cloud-1200-630.png"

class GCPTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Enhanced bash script with base64-encoded credential handling
        bash_script = r"""
#!/bin/bash
set -e

# Handle credentials - expecting base64-encoded JSON in GOOGLE_APPLICATION_CREDENTIALS
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    # Create a temporary file for credentials
    CREDS_FILE=$(mktemp)
    
    # Write the base64 string to a file first to avoid any shell interpretation issues
    B64_FILE=$(mktemp)
    echo "$GOOGLE_APPLICATION_CREDENTIALS" > "$B64_FILE"
    
    # Decode base64 credentials using the file as input
    if ! base64 -d "$B64_FILE" > "$CREDS_FILE" 2>/dev/null; then
        echo "Error: Failed to decode base64 credentials"
        echo "Please ensure GOOGLE_APPLICATION_CREDENTIALS contains valid base64-encoded data"
        rm -f "$B64_FILE" "$CREDS_FILE"
        exit 1
    fi
    
    # Clean up the base64 file as we don't need it anymore
    rm -f "$B64_FILE"
    
    # Check if the file is empty
    if [ ! -s "$CREDS_FILE" ]; then
        echo "Error: Decoded credentials file is empty"
        echo "Please check that GOOGLE_APPLICATION_CREDENTIALS contains non-empty base64-encoded JSON"
        rm -f "$CREDS_FILE"
        exit 1
    fi
    
    # Validate JSON format without printing contents
    if ! jq empty "$CREDS_FILE" 2>/dev/null; then
        echo "Error: Invalid JSON format in credentials after base64 decoding"
        echo "Please check that GOOGLE_APPLICATION_CREDENTIALS contains valid base64-encoded JSON"
        
        # Show file size for debugging
        echo "Decoded file size: $(wc -c < "$CREDS_FILE") bytes"
        
        # Show beginning and end of file for debugging
        echo "First 50 characters:"
        head -c 50 "$CREDS_FILE" | hexdump -C
        echo "Last 50 characters:"
        tail -c 50 "$CREDS_FILE" | hexdump -C
        
        rm -f "$CREDS_FILE"
        exit 1
    fi
    
    # Activate the service account with error handling
    if ! gcloud auth activate-service-account --key-file="$CREDS_FILE" 2>/dev/null; then
        echo "Authentication failed."
        echo "Please check that the service account has the necessary permissions."
        # Only show non-sensitive information
        echo "Project ID: $(jq -r '.project_id // "Not found"' "$CREDS_FILE" 2>/dev/null)"
        echo "Client email: $(jq -r '.client_email // "Not found"' "$CREDS_FILE" 2>/dev/null)"
        rm -f "$CREDS_FILE"
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