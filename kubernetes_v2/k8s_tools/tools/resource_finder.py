from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

resource_finder_tool = KubernetesTool(
    name="resource_finder",
    description="Find Kubernetes resources across your cluster with powerful search capabilities",
    content='''
    #!/bin/sh
    # Source the resource finder script
    source /tmp/resource_finder.sh
    
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

# Register the tool
tool_registry.register("kubernetes", resource_finder_tool) 