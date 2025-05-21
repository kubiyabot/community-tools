from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

# Tool to list Helm releases deployed in the last N hours
helm_list_recent = KubernetesTool(
    name="list_helm_releases",
    description="Lists all Helm releases deployed in the specified time range",
    content="""
    #!/bin/bash
    set -e

    # Get the hours parameter
    hours=$hours
    
    echo "🔍 Listing Helm releases deployed in the last $hours hour(s)..."
    
    # Get current time in seconds since epoch
    current_time=$(date +%s)
    # Calculate time ago in seconds
    time_ago=$((current_time - (hours * 3600)))
    
    # Execute helm list command
    if output=$(helm list -A -o json); then
        echo "✅ Helm releases retrieved successfully:"
        
        # Parse JSON output and filter by last updated time using proper date format handling
        filtered_output=$(echo "$output" | jq -r --argjson time "$time_ago" '[.[] | select(.updated | try (strptime("%Y-%m-%d %H:%M:%S.%f %z %Z") | mktime) catch 0 > $time) | {name: .name, namespace: .namespace, revision: .revision, updated: .updated, status: .status, chart: .chart}]')
        
        echo "🔍 Filtered output:"
        echo "$filtered_output"
        # Check if the filtered result is an empty array
        if [ "$(echo "$filtered_output" | jq 'length')" -eq "0" ]; then
            echo "⚠️ No machines found deployed in the last $hours hour(s)"
        else
            # Print the filtered results
            echo "✅ Found the following resources:"
            echo "$filtered_output" | jq -r '.[]'
        fi
    else
        echo "❌ Failed to retrieve Helm releases"
        exit 1
    fi
    """,
    args=[
        Arg(
            name="hours",
            description="Number of hours to look back for Helm releases (1-5)",
            required=True,
            type="int",
            default="1"
        )
    ],
    image="dtzar/helm-kubectl:latest"  # Using an image with Helm installed
)

# Register the tool
tool_registry.register("kubernetes", helm_list_recent)
