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
    
    # Activate the service account without unnecessary components
    # Skip component update check to speed up startup
    export CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK=true
    # Skip diagnostics to speed up commands
    export CLOUDSDK_CORE_DISABLE_PROMPTS=1
    export CLOUDSDK_CORE_DISABLE_USAGE_REPORTING=true
    # Skip Python warnings
    export PYTHONWARNINGS=ignore
    
    # Faster authentication
    gcloud auth activate-service-account --key-file="$CREDS_FILE" --quiet
    
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
            image="google/cloud-sdk:alpine",  # Using the Alpine version for faster startup
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
    
    # Install minimal dependencies silently
    echo "Installing dependencies..."
    apk update --quiet > /dev/null 2>&1 && apk add --quiet --no-cache python3 py3-pip curl jq bash > /dev/null 2>&1
    
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