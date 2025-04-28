from kubiya_sdk.tools import Tool
import json

GCP_ICON_URL = "https://cloud.google.com/_static/cloud/images/social-icon-google-cloud-1200-630.png"

class GCPTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Enhanced bash script with more robust credential handling and debugging
        bash_script = r"""
#!/bin/bash
set -e

# Handle credentials - expecting base64-encoded JSON in GOOGLE_APPLICATION_CREDENTIALS
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    # Create a temporary file for credentials
    CREDS_FILE=$(mktemp)
    DEBUG_FILE=$(mktemp)
    
    # Debug: Check the length of the input string
    echo "DEBUG: Length of GOOGLE_APPLICATION_CREDENTIALS: ${#GOOGLE_APPLICATION_CREDENTIALS}" > "$DEBUG_FILE"
    
    # Debug: Show the first 20 characters of the input
    echo "DEBUG: First 20 chars: ${GOOGLE_APPLICATION_CREDENTIALS:0:20}" >> "$DEBUG_FILE"
    
    # Remove any whitespace from the base64 string that might cause decoding issues
    CLEAN_B64=$(echo "$GOOGLE_APPLICATION_CREDENTIALS" | tr -d '[:space:]')
    
    # Debug: Check the length after cleaning
    echo "DEBUG: Length after cleaning: ${#CLEAN_B64}" >> "$DEBUG_FILE"
    
    # Decode base64 credentials with careful error handling
    if ! echo "$CLEAN_B64" | base64 -d > "$CREDS_FILE" 2>>"$DEBUG_FILE"; then
        echo "Error: Failed to decode base64 credentials"
        echo "Please ensure GOOGLE_APPLICATION_CREDENTIALS contains valid base64-encoded data"
        echo "DEBUG INFO:" 
        cat "$DEBUG_FILE"
        rm -f "$CREDS_FILE" "$DEBUG_FILE"
        exit 1
    fi
    
    # Debug: Check the size of the decoded file
    echo "DEBUG: Decoded file size: $(wc -c < "$CREDS_FILE") bytes" >> "$DEBUG_FILE"
    
    # Print the full decoded JSON for debugging
    echo "FULL DECODED JSON:"
    cat "$CREDS_FILE"
    echo "END OF DECODED JSON"
    
    # Check if the file is empty
    if [ ! -s "$CREDS_FILE" ]; then
        echo "Error: Decoded credentials file is empty"
        echo "Please check that GOOGLE_APPLICATION_CREDENTIALS contains non-empty base64-encoded JSON"
        echo "DEBUG INFO:" 
        cat "$DEBUG_FILE"
        rm -f "$CREDS_FILE" "$DEBUG_FILE"
        exit 1
    fi
    
    # Try to ensure the file contains valid JSON by extracting content between { and }
    FIXED_CREDS_FILE=$(mktemp)
    if grep -o '{.*}' "$CREDS_FILE" > "$FIXED_CREDS_FILE" 2>/dev/null; then
        # Debug: Check if grep found anything
        echo "DEBUG: JSON extraction successful, size: $(wc -c < "$FIXED_CREDS_FILE") bytes" >> "$DEBUG_FILE"
        # Replace the original file with the fixed version
        mv "$FIXED_CREDS_FILE" "$CREDS_FILE"
    else
        echo "DEBUG: JSON extraction failed, no JSON object found" >> "$DEBUG_FILE"
        rm -f "$FIXED_CREDS_FILE"
    fi
    
    # Validate JSON format without printing contents
    if ! jq empty "$CREDS_FILE" 2>>"$DEBUG_FILE"; then
        echo "Error: Invalid JSON format in credentials after base64 decoding and fixing attempts"
        echo "Please check that GOOGLE_APPLICATION_CREDENTIALS contains valid base64-encoded JSON"
        echo "DEBUG INFO:" 
        cat "$DEBUG_FILE"
        rm -f "$CREDS_FILE" "$DEBUG_FILE"
        exit 1
    fi
    
    # Extract project ID for potential fallback
    PROJECT_ID=$(jq -r '.project_id // ""' "$CREDS_FILE" 2>/dev/null)
    
    # Debug: Show the extracted project ID
    echo "DEBUG: Extracted project ID: $PROJECT_ID" >> "$DEBUG_FILE"
    
    # Activate the service account with error handling
    if ! gcloud auth activate-service-account --key-file="$CREDS_FILE" 2>>"$DEBUG_FILE"; then
        echo "Authentication failed."
        echo "Please check that the service account has the necessary permissions."
        # Only show non-sensitive information
        echo "Project ID: $(jq -r '.project_id // "Not found"' "$CREDS_FILE" 2>/dev/null)"
        echo "Client email: $(jq -r '.client_email // "Not found"' "$CREDS_FILE" 2>/dev/null)"
        echo "DEBUG INFO:" 
        cat "$DEBUG_FILE"
        
        # Try a fallback authentication method if we have a project ID
        if [ -n "$PROJECT_ID" ]; then
            echo "Attempting fallback authentication using project ID: $PROJECT_ID"
            if gcloud config set project "$PROJECT_ID" 2>>"$DEBUG_FILE"; then
                echo "Project set successfully. Proceeding without service account authentication."
                # Some operations may still work with just the project set
            else
                echo "Failed to set project. Authentication failed completely."
                rm -f "$CREDS_FILE" "$DEBUG_FILE"
                exit 1
            fi
        else
            echo "No project ID found in credentials. Authentication failed completely."
            rm -f "$CREDS_FILE" "$DEBUG_FILE"
            exit 1
        fi
    else
        echo "Authentication completed successfully"
    fi
    
    # Clean up debug file
    rm -f "$DEBUG_FILE"
    
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