from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

service_tool = KubernetesTool(
    name="service_manager",
    description="Advanced service management tool with endpoint analysis and detailed service information",
    content="""
    #!/bin/bash
    set -e

    # Constants for output limiting
    MAX_ITEMS_PER_PAGE=10
    MAX_OUTPUT_WIDTH=120
    MAX_TOTAL_OUTPUT=5000
    MAX_ENDPOINTS=5

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

    # Set namespace flag
    namespace_flag=""
    [ -n "${namespace:-}" ] && namespace_flag="-n $namespace" || namespace_flag="--all-namespaces"

    {
        case "${action:-list}" in
            "list")
                echo "📋 Service List:"
                echo "=============="
                
                # Get service information
                kubectl get services $namespace_flag -o json | \
                jq -r '.items[] | {
                    name: .metadata.name,
                    namespace: .metadata.namespace,
                    type: .spec.type,
                    cluster_ip: .spec.clusterIP,
                    external_ip: (.status.loadBalancer.ingress // [] | map(.ip) | join(", ")),
                    ports: .spec.ports,
                    selector: .spec.selector,
                    age: .metadata.creationTimestamp
                }' | jq -r '. |
                "Service: \(.name)\n" +
                "Namespace: \(.namespace)\n" +
                "Type: \(.type)\n" +
                "Cluster IP: \(.cluster_ip)\n" +
                if .external_ip != "" then "External IP: \(.external_ip)\n" else "" end +
                "Ports:\n" + (.ports | map("  • \(.port):\(.targetPort) (\(.protocol))") | join("\n")) +
                "\nSelector: \(.selector | to_entries | map("\(.key)=\(.value)") | join(", "))\n" +
                "Age: \(.age)"' | \
                awk '
                /^Service:/ {printf "\n🔌 %s\n", substr($0, 10)}
                /^Namespace:/ {printf "📁 %s\n", $0}
                /^Type:/ {
                    type=$2;
                    emoji="❓";
                    if (type == "ClusterIP") emoji="🔒";
                    else if (type == "NodePort") emoji="🌐";
                    else if (type == "LoadBalancer") emoji="⚖️";
                    else if (type == "ExternalName") emoji="🔗";
                    printf "%s %s\n", emoji, $0;
                }
                /^Cluster IP:/ {printf "🌐 %s\n", $0}
                /^External IP:/ {printf "🌍 %s\n", $0}
                /^Ports:/ {print "🔌 Ports:"}
                /^  •/ {printf "  %s\n", $0}
                /^Selector:/ {printf "🎯 %s\n", $0}
                /^Age:/ {printf "🕒 %s\n", $0}
                ' > "$formatted_output"
                ;;
                
            "describe")
                if [ -z "$name" ] || [ -z "$namespace" ]; then
                    echo "❌ Both service name and namespace are required for describe action"
                    exit 1
                fi
                
                echo "🔍 Service Details:"
                echo "================"
                
                # Get detailed service information
                kubectl get service "$name" -n "$namespace" -o json | \
                jq -r '{
                    name: .metadata.name,
                    namespace: .metadata.namespace,
                    type: .spec.type,
                    cluster_ip: .spec.clusterIP,
                    external_ip: (.status.loadBalancer.ingress // [] | map(.ip) | join(", ")),
                    ports: .spec.ports,
                    selector: .spec.selector,
                    age: .metadata.creationTimestamp,
                    annotations: .metadata.annotations,
                    labels: .metadata.labels
                }' | jq -r '. |
                "Name: \(.name)\n" +
                "Namespace: \(.namespace)\n" +
                "Type: \(.type)\n" +
                "Cluster IP: \(.cluster_ip)\n" +
                if .external_ip != "" then "External IP: \(.external_ip)\n" else "" end +
                "Ports:\n" + (.ports | map("  • \(.port):\(.targetPort) (\(.protocol))") | join("\n")) +
                "\nSelector: \(.selector | to_entries | map("\(.key)=\(.value)") | join(", "))\n" +
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
                /^Name:/ {printf "🔌 %s\n", substr($0, 6)}
                /^Namespace:/ {printf "📁 %s\n", $0}
                /^Type:/ {
                    type=$2;
                    emoji="❓";
                    if (type == "ClusterIP") emoji="🔒";
                    else if (type == "NodePort") emoji="🌐";
                    else if (type == "LoadBalancer") emoji="⚖️";
                    else if (type == "ExternalName") emoji="🔗";
                    printf "%s %s\n", emoji, $0;
                }
                /^Cluster IP:/ {printf "🌐 %s\n", $0}
                /^External IP:/ {printf "🌍 %s\n", $0}
                /^Ports:/ {print "🔌 Ports:"}
                /^  •/ {printf "  %s\n", $0}
                /^Selector:/ {printf "🎯 %s\n", $0}
                /^Age:/ {printf "🕒 %s\n", $0}
                /^Labels:/ {printf "🏷️  %s\n", $0}
                /^Annotations:/ {printf "📝 %s\n", $0}
                ' > "$formatted_output"

                # Get endpoints
                echo -e "\n🎯 Endpoints:"
                echo "==========="
                kubectl get endpoints "$name" -n "$namespace" -o json | \
                jq -r '.subsets[] | 
                "Ready Endpoints:" as $title |
                (.addresses // [] | map(.ip) | join(", ")) as $ready |
                "Not Ready Endpoints:" as $not_title |
                (.notReadyAddresses // [] | map(.ip) | join(", ")) as $not_ready |
                if $ready != "" then "\($title)\n\($ready)" else "" end +
                if $not_ready != "" then "\n\($not_title)\n\($not_ready)" else "" end' | \
                awk '
                /^Ready Endpoints:/ {printf "✅ %s\n", $0}
                /^Not Ready Endpoints:/ {printf "❌ %s\n", $0}
                /^[0-9]/ {print "  • " $0}
                ' >> "$formatted_output"

                # Get events
                echo -e "\n📜 Recent Events:"
                echo "=============="
                kubectl get events -n "$namespace" --field-selector involvedObject.name="$name",involvedObject.kind=Service \
                    --sort-by='.lastTimestamp' | \
                tail -n 10 | \
                awk '{
                    if ($7 ~ /Warning/) emoji="⚠️";
                    else if ($7 ~ /Normal/) emoji="ℹ️";
                    else emoji="📝";
                    print "  " emoji " " $0;
                }' >> "$formatted_output"
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
            description="Action to perform (list, describe)",
            required=False,
        ),
        Arg(
            name="namespace",
            type="str",
            description="Kubernetes namespace. If omitted, uses all namespaces for list action",
            required=False,
        ),
        Arg(
            name="name",
            type="str",
            description="Name of the service (required for describe action)",
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
tool_registry.register("kubernetes", service_tool)
