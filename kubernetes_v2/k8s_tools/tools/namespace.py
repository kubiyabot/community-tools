from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

namespace_tool = KubernetesTool(
    name="namespace_manager",
    description="Advanced namespace management tool with resource quotas, limits, and detailed analysis",
    content="""
    #!/bin/bash
    set -e

    # Constants for output limiting
    MAX_ITEMS_PER_PAGE=10
    MAX_OUTPUT_WIDTH=120
    MAX_TOTAL_OUTPUT=5000

    # Function to handle cleanup
    cleanup() {
        rm -f "${temp_files[@]}" 2>/dev/null
        exit "${1:-0}"
    }
    trap 'cleanup $?' EXIT INT TERM

    # Array to track temporary files
    declare -a temp_files
    temp_dir=$(mktemp -d)
    temp_files+=("$temp_dir")

    # Function to create temp file
    create_temp_file() {
        local tmp="${temp_dir}/$(uuidgen || date +%s.%N)"
        temp_files+=("$tmp")
        echo "$tmp"
    }

    # Function to paginate output
    paginate_output() {
        local input_file=$1
        local page=${2:-1}
        local page_size=${3:-$MAX_ITEMS_PER_PAGE}
        local total_lines=$(wc -l < "$input_file")
        local total_pages=$(( (total_lines + page_size - 1) / page_size ))

        # Validate page number
        if [ "$page" -lt 1 ]; then
            page=1
        elif [ "$page" -gt "$total_pages" ]; then
            page=$total_pages
        fi

        # Calculate start and end lines
        local start_line=$(( (page - 1) * page_size + 1 ))
        local end_line=$(( page * page_size ))

        # Show pagination info
        echo "📄 Page $page of $total_pages (Items $start_line-$end_line of $total_lines)"
        echo "------------------------------------------------"

        # Extract and show the page
        sed -n "${start_line},${end_line}p" "$input_file"

        # Show navigation help if more than one page
        if [ "$total_pages" -gt 1 ]; then
            echo -e "\n📌 Use --page N to view different pages"
        fi
    }

    # Create output file
    formatted_output=$(create_temp_file)

    {
        case "${action:-list}" in
            "list")
                echo "📋 Namespace List:"
                echo "================"
                
                # Get namespace information
                kubectl get namespaces -o json | \
                jq -r '.items[] | {
                    name: .metadata.name,
                    status: .status.phase,
                    age: .metadata.creationTimestamp,
                    labels: .metadata.labels,
                    annotations: .metadata.annotations
                }' | jq -r '. |
                "Namespace: \(.name)\n" +
                "Status: \(.status)\n" +
                "Age: \(.age)\n" +
                if .labels then
                    "Labels: \(.labels | to_entries | map("\(.key)=\(.value)") | join(", "))\n"
                else ""
                end +
                if .annotations then
                    "Annotations: \(.annotations | to_entries | map("\(.key)=\(.value)") | join(", "))"
                else ""
                end' | \
                awk '
                /^Namespace:/ {printf "\n📁 %s\n", substr($0, 11)}
                /^Status:/ {
                    status=$2;
                    emoji="❓";
                    if (status == "Active") emoji="✅";
                    else if (status == "Terminating") emoji="⏳";
                    printf "%s %s\n", emoji, $0;
                }
                /^Age:/ {printf "🕒 %s\n", $0}
                /^Labels:/ {printf "🏷️  %s\n", $0}
                /^Annotations:/ {printf "📝 %s\n", $0}
                ' > "$formatted_output"
                ;;
                
            "create")
                if [ -z "$name" ]; then
                    echo "❌ Namespace name is required for creation"
                    exit 1
                fi
                
                # Create namespace manifest
                ns_file=$(create_temp_file)
                cat > "$ns_file" <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: $name
EOF

                # Add labels if provided
                if [ -n "${labels:-}" ]; then
                    echo "  labels:" >> "$ns_file"
                    echo "$labels" | tr ',' '\n' | while IFS='=' read -r key value; do
                        echo "    $key: $value" >> "$ns_file"
                    done
                fi

                # Create the namespace
                if kubectl apply -f "$ns_file"; then
                    echo "✅ Namespace '$name' created successfully"
                else
                    echo "❌ Failed to create namespace"
                    exit 1
                fi
                ;;
                
            "delete")
                if [ -z "$name" ]; then
                    echo "❌ Namespace name is required for deletion"
                    exit 1
                fi
                
                # Check if namespace exists
                if ! kubectl get namespace "$name" >/dev/null 2>&1; then
                    echo "❌ Namespace '$name' not found"
                    exit 1
                fi
                
                # Delete the namespace
                if kubectl delete namespace "$name"; then
                    echo "✅ Namespace '$name' deleted successfully"
                else
                    echo "❌ Failed to delete namespace"
                    exit 1
                fi
                ;;
                
            "describe")
                if [ -z "$name" ]; then
                    echo "❌ Namespace name is required for describe action"
                    exit 1
                fi
                
                echo "🔍 Namespace Details:"
                echo "=================="
                
                # Get detailed namespace information
                kubectl get namespace "$name" -o json | \
                jq -r '{
                    name: .metadata.name,
                    status: .status.phase,
                    age: .metadata.creationTimestamp,
                    labels: .metadata.labels,
                    annotations: .metadata.annotations,
                    resource_quotas: .spec.resourceQuotas,
                    limit_ranges: .spec.limitRanges
                }' | jq -r '. |
                "Name: \(.name)\n" +
                "Status: \(.status)\n" +
                "Age: \(.age)\n" +
                if .labels then
                    "Labels: \(.labels | to_entries | map("\(.key)=\(.value)") | join(", "))\n"
                else ""
                end +
                if .annotations then
                    "Annotations: \(.annotations | to_entries | map("\(.key)=\(.value)") | join(", "))\n"
                else ""
                end' | \
                awk '
                /^Name:/ {printf "📁 %s\n", substr($0, 6)}
                /^Status:/ {
                    status=$2;
                    emoji="❓";
                    if (status == "Active") emoji="✅";
                    else if (status == "Terminating") emoji="⏳";
                    printf "%s %s\n", emoji, $0;
                }
                /^Age:/ {printf "🕒 %s\n", $0}
                /^Labels:/ {printf "🏷️  %s\n", $0}
                /^Annotations:/ {printf "📝 %s\n", $0}
                ' > "$formatted_output"

                # Get resource quotas
                echo -e "\n📊 Resource Quotas:"
                echo "================="
                kubectl get resourcequota -n "$name" -o wide 2>/dev/null | \
                awk 'NR==1 {print $0} NR>1 {print "  • " $0}' >> "$formatted_output"

                # Get limit ranges
                echo -e "\n📈 Limit Ranges:"
                echo "=============="
                kubectl get limitrange -n "$name" -o wide 2>/dev/null | \
                awk 'NR==1 {print $0} NR>1 {print "  • " $0}' >> "$formatted_output"

                # Get resource usage
                echo -e "\n📉 Resource Usage:"
                echo "==============="
                kubectl top pod -n "$name" --containers 2>/dev/null | \
                awk 'NR==1 {print $0} NR>1 {print "  • " $0}' >> "$formatted_output"
                ;;
                
            *)
                echo "❌ Invalid action specified"
                exit 1
                ;;
        esac
    } >> "$formatted_output"

    # Show output with line limit
    head -n $MAX_TOTAL_OUTPUT "$formatted_output"
    
    # Show truncation message if needed
    if [ "$(wc -l < "$formatted_output")" -gt "$MAX_TOTAL_OUTPUT" ]; then
        echo "⚠️  Output truncated. Use specific filters or actions to see more details."
    fi
    """,
    args=[
        Arg(
            name="action",
            type="str",
            description="Action to perform (list, create, delete, describe)",
            required=False,
        ),
        Arg(
            name="name",
            type="str",
            description="Name of the namespace (required for create, delete, describe actions)",
            required=False,
        ),
        Arg(
            name="labels",
            type="str",
            description="Labels to apply in key=value format, comma-separated (only for create action)",
            required=False,
        ),
        Arg(
            name="page",
            type="int",
            description="Page number for paginated output",
            required=False,
        ),
    ],
)

# Register tools
tool_registry.register("kubernetes", namespace_tool)