from kubiya_sdk.tools import Tool

GCP_ICON_URL = "https://cloud.google.com/_static/cloud/images/social-icon-google-cloud-1200-630.png"

class GCPTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Wrap the command to ensure errors are captured and output is verbose
        # This redirects stderr to stdout and sets debug flags
        enhanced_content = f"""
#!/bin/bash

# Handle credentials properly
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    # Create a temporary directory for credentials
    CREDS_DIR=$(mktemp -d)
    CREDS_FILE="$CREDS_DIR/credentials.json"
    
    # Try to decode if base64 encoded, otherwise use as-is
    if echo "$GOOGLE_APPLICATION_CREDENTIALS" | base64 -d > "$CREDS_FILE" 2>/dev/null; then
        echo "Credentials appear to be base64 encoded, decoded successfully"
    else
        echo "Credentials don't appear to be base64 encoded, using as raw JSON"
        echo "$GOOGLE_APPLICATION_CREDENTIALS" > "$CREDS_FILE"
    fi
    
    # Check if the file is valid JSON
    if jq . "$CREDS_FILE" >/dev/null 2>&1; then
        echo "Valid JSON credentials detected"
        # Set the environment variable to point to this file
        export GOOGLE_APPLICATION_CREDENTIALS="$CREDS_FILE"
        # Activate the service account
        echo "Activating service account..."
        gcloud auth activate-service-account --key-file="$CREDS_FILE"
        echo "Service account activated"
    else
        echo "Error: Invalid JSON credentials format"
        echo "First 10 lines of credentials file:"
        head -10 "$CREDS_FILE"
        exit 1
    fi
fi

# Execute the actual command
echo "Executing command..."
{content} 2>&1
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