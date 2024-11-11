from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from docker_tools.base import DockerTool
import os

# Get the script content
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(os.path.dirname(current_dir), 'scripts')

with open(os.path.join(scripts_dir, 'image_builder.py'), 'r') as f:
    BUILD_SCRIPT = f.read()

build_image_tool = DockerTool(
    name="build-docker-image",
    description="Builds a Docker image using Dagger, supporting multi-platform builds and build arguments",
    content="""
#!/bin/bash
set -e

echo "🔨 Setting up build environment..."
pip install dagger-io > /dev/null 2>&1

echo "📦 Preparing build context..."
# Validate JSON inputs
if ! echo "$build_args" | jq . >/dev/null 2>&1; then
    echo "❌ Invalid build_args JSON format"
    exit 1
fi
if ! echo "$platforms" | jq . >/dev/null 2>&1; then
    echo "❌ Invalid platforms JSON format"
    exit 1
fi

# Function to format JSON output
format_output() {
    while IFS= read -r line; do
        if echo "$line" | jq . >/dev/null 2>&1; then
            # Parse JSON and add formatting
            local status=$(echo "$line" | jq -r '.status')
            local message=$(echo "$line" | jq -r '.message')
            local timestamp=$(echo "$line" | jq -r '.timestamp')
            
            case "$status" in
                "starting")
                    echo "🚀 $message"
                    ;;
                "progress")
                    echo "⏳ $message"
                    ;;
                "success")
                    echo "✅ $message"
                    # Print additional details
                    echo "$line" | jq -r '
                        if has("image_id") then "   Image ID: " + .image_id else empty end,
                        if has("registry_url") then "   Registry URL: " + .registry_url else empty end
                    ' | grep -v null
                    ;;
                "error")
                    echo "❌ Error: $message"
                    if echo "$line" | jq -e 'has("details")' >/dev/null; then
                        echo "   Details: $(echo "$line" | jq -r '.details')"
                    fi
                    ;;
            esac
        else
            echo "$line"
        fi
    done
}

# Prepare build arguments with progress indicators
BUILD_ARGS='{
    "context_path": "'$context_path'",
    "dockerfile": "'$dockerfile'",
    "target": "'$target'",
    "build_args": '$build_args',
    "platforms": '$platforms',
    "push": '$push',
    "registry": "'$registry'",
    "tag": "'$tag'"
}'

echo "🚀 Starting build process..."
python /tmp/scripts/image_builder.py "$BUILD_ARGS" 2>&1 | format_output
""",
    args=[
        Arg(
            name="context_path",
            type="str",
            description="Path to the build context",
            required=True
        ),
        Arg(
            name="dockerfile",
            type="str",
            description="Path to the Dockerfile",
            required=True
        ),
        Arg(
            name="target",
            type="str",
            description="Target build stage",
            required=False
        ),
        Arg(
            name="build_args",
            type="str",
            description="JSON string of build arguments",
            required=False,
            default="{}"
        ),
        Arg(
            name="platforms",
            type="str",
            description="JSON array of target platforms",
            required=False,
            default='["linux/amd64"]'
        ),
        Arg(
            name="push",
            type="bool",
            description="Push image to registry after build",
            required=False,
            default=False
        ),
        Arg(
            name="registry",
            type="str",
            description="Registry to push the image to",
            required=False
        ),
        Arg(
            name="tag",
            type="str",
            description="Tag for the built image",
            required=False,
            default="latest"
        )
    ],
    long_running=True,
    with_files=[
        FileSpec(
            destination="/tmp/scripts/image_builder.py",
            content=BUILD_SCRIPT
        )
    ],
    mermaid="""
    sequenceDiagram
        participant U as User
        participant D as Dagger
        participant B as BuildKit
        participant R as Registry

        U->>D: Build Request
        activate D
        D->>B: Initialize Build
        activate B
        B->>B: Process Dockerfile
        B->>B: Execute Build Stages
        B-->>D: Image Built
        deactivate B
        D-->>U: Image ID
        deactivate D
        
        opt Push to Registry
            U->>R: Push Image
            R-->>U: Push Complete
        end
    """
)

tool_registry.register("docker", build_image_tool) 