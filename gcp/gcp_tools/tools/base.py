from kubiya_sdk.tools import Tool

GCP_ICON_URL = "https://cloud.google.com/_static/cloud/images/social-icon-google-cloud-1200-630.png"

class GCPTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Wrap the command to ensure errors are captured and output is verbose
        # This redirects stderr to stdout and sets debug flags
        enhanced_content = f"""
#!/bin/bash
set -e
export CLOUDSDK_CORE_VERBOSITY=debug

# Handle credentials properly
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    # Use base64 encoding/decoding to preserve the exact content
    echo "$GOOGLE_APPLICATION_CREDENTIALS" | base64 -d > /tmp/gcp_credentials.json 2>/dev/null || echo "$GOOGLE_APPLICATION_CREDENTIALS" > /tmp/gcp_credentials.json
    
    # Check if the file is valid JSON
    if jq . /tmp/gcp_credentials.json >/dev/null 2>&1; then
        # Set the environment variable to point to this file
        export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp_credentials.json
        # Activate the service account
        gcloud auth activate-service-account --key-file=/tmp/gcp_credentials.json
    else
        echo "Error: Invalid JSON credentials format"
        cat /tmp/gcp_credentials.json | head -10
    fi
fi

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