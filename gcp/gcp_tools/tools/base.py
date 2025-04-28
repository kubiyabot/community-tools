from kubiya_sdk.tools import Tool

GCP_ICON_URL = "https://cloud.google.com/_static/cloud/images/social-icon-google-cloud-1200-630.png"

class GCPTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Wrap the command to ensure errors are captured and output is verbose
        # This redirects stderr to stdout and sets debug flags
        
        # Use a raw string (r prefix) to avoid Python's string escaping issues
        bash_script = r"""
#!/bin/bash
set -e

# Handle credentials properly
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    # Create a temporary directory for credentials
    CREDS_DIR=$(mktemp -d)
    CREDS_FILE="$CREDS_DIR/credentials.json"
    
    echo "Processing credentials..."
    
    # Debug: Show credential length and format
    CRED_LENGTH=$(echo "$GOOGLE_APPLICATION_CREDENTIALS" | wc -c)
    echo "Credential string length: $CRED_LENGTH bytes"
    
    # Check if it starts with a curly brace (likely JSON)
    if echo "$GOOGLE_APPLICATION_CREDENTIALS" | grep -q "^{"; then
        echo "Credentials appear to be in JSON format"
    else
        echo "Warning: Credentials don't appear to be in JSON format"
        echo "First 10 characters: $(echo "$GOOGLE_APPLICATION_CREDENTIALS" | head -c 10)..."
    fi
    
    # Clean up any potential special characters or line breaks
    echo "Cleaning credentials format..."
    # Write credentials to file without using echo (to avoid shell interpretation issues)
    printf "%s" "$GOOGLE_APPLICATION_CREDENTIALS" > "$CREDS_FILE"
    
    # Check if the file is valid JSON
    if jq -e . "$CREDS_FILE" >/dev/null 2>&1; then
        echo "Valid JSON credentials detected"
        # Set the environment variable to point to this file
        export GOOGLE_APPLICATION_CREDENTIALS="$CREDS_FILE"
        # Activate the service account
        echo "Activating service account..."
        gcloud auth activate-service-account --key-file="$CREDS_FILE" 2>&1
        if [ $? -eq 0 ]; then
            echo "Service account activated successfully"
            # Extract and display non-sensitive information
            PROJECT_ID=$(jq -r '.project_id' "$CREDS_FILE" 2>/dev/null || echo "unknown")
            CLIENT_EMAIL=$(jq -r '.client_email' "$CREDS_FILE" 2>/dev/null || echo "unknown")
            echo "Using service account: $CLIENT_EMAIL for project: $PROJECT_ID"
        else
            echo "Error activating service account"
            # Show available fields in the credentials file
            echo "Available credential fields:"
            jq 'keys' "$CREDS_FILE" 2>/dev/null || echo "Could not parse credentials"
            exit 1
        fi
    else
        echo "Error: Invalid JSON credentials format"
        # Check file size
        FILE_SIZE=$(wc -c < "$CREDS_FILE")
        echo "Credential file size: $FILE_SIZE bytes"
        
        # Check if file starts with JSON opening brace
        if [[ $(head -c 1 "$CREDS_FILE") == "{" ]]; then
            echo "File starts with JSON opening brace"
        else
            echo "File does not start with JSON opening brace"
            echo "First 20 bytes (hex):"
            hexdump -C -n 20 "$CREDS_FILE"
        fi
        
        echo "---"
        echo "Hint: Credentials should be a complete, valid JSON object."
        exit 1
    fi
else
    echo "Warning: No credentials provided via GOOGLE_APPLICATION_CREDENTIALS"
fi

# Execute the actual command
echo "Executing command..."
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