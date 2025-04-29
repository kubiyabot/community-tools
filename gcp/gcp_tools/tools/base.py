from kubiya_sdk.tools import Tool
import json

GCP_ICON_URL = "https://cloud.google.com/_static/cloud/images/social-icon-google-cloud-1200-630.png"

class GCPTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Standard GCP tool using the Google Cloud SDK
        bash_script = r"""
#!/usr/bin/env bash
set -e

# Handle credentials
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    # Create a temporary file for credentials
    CREDS_FILE=$(mktemp)
    
    # Decode base64 credentials
    echo "$GOOGLE_APPLICATION_CREDENTIALS" | base64 -d > "$CREDS_FILE"
    
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
            image="google/cloud-sdk:slim",  # Using the slim version of the SDK
            content=enhanced_content,
            args=args,
            env=["GITLAB_REPO_URL"],
            secrets=["GITLAB_TOKEN", "GOOGLE_APPLICATION_CREDENTIALS"],
            long_running=long_running,
            mermaid=mermaid_diagram
        )

class TerraformTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Lightweight Terraform-based tool
        bash_script = r"""
#!/bin/sh
set -e

# Handle credentials
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    # Create a temporary file for credentials
    CREDS_FILE=$(mktemp)
    
    # Decode base64 credentials
    echo "$GOOGLE_APPLICATION_CREDENTIALS" | base64 -d > "$CREDS_FILE"
    
    # Install minimal dependencies
    apk update && apk add --no-cache python3 py3-pip curl jq bash
    
    # Use the credentials directly with Terraform
    export GOOGLE_CREDENTIALS=$(cat "$CREDS_FILE")
    export GOOGLE_PROJECT=$(cat "$CREDS_FILE" | jq -r '.project_id')
    
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