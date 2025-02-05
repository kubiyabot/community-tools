from kubiya_sdk.tools import Arg
from kubiya_sdk.tools import FileSpec
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry
import os

def read_file_content(path):
    """Helper function to read file content"""
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not read file {path}: {e}")
        return None

resource_finder_tool = KubernetesTool(
    name="resource_finder",
    description="Find Kubernetes resources across your cluster with powerful search capabilities",
    content='''#!/bin/bash
set -e

# Source the resource finder script
. /tmp/resource_finder.sh

# Call the main function with provided arguments
pattern="{{.pattern}}"
namespace="{{.namespace}}"
kind="{{.resource_type}}"
label_selector="{{.label_selector}}"
show_labels="{{.show_labels}}"

# Execute the search
search_resources "$pattern" "$namespace" "$kind" "$label_selector" "$show_labels"
''',
    args=[
        Arg(
            name="pattern",
            type="str",
            description="Search pattern (case insensitive)",
            required=True
        ),
        Arg(
            name="namespace",
            type="str",
            description="Kubernetes namespace to search in (optional, searches all if not specified)",
            required=False
        ),
        Arg(
            name="resource_type",
            type="str",
            description="Specific resource type to search for (e.g., pod, deployment)",
            required=False
        ),
        Arg(
            name="label_selector",
            type="str",
            description="Filter by labels (e.g., 'app=nginx,env=prod')",
            required=False
        ),
        Arg(
            name="show_labels",
            type="bool",
            description="Show labels for matched resources",
            required=False
        ),
    ],
)

# Get the directory of the current file
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates_dir = os.path.join(current_dir, 'templates')

# Add the resource finder script to file specs
resource_finder_tool.with_files.append(
    FileSpec(
        content=read_file_content(os.path.join(templates_dir, 'resource_finder.sh')),
        destination="/tmp/resource_finder.sh"
    )
)

# Register the tool
tool_registry.register("kubernetes", resource_finder_tool) 