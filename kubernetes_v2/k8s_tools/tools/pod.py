from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

# Common constants for all tools
MAX_OUTPUT_LINES = 100
MAX_LOGS_LINES = 1000
MAX_EVENTS = 25

pod_restart_tool = KubernetesTool(
    name="pod_restart",
    description="Advanced pod restart tool with state analysis and event correlation",
    content="""
    #!/bin/bash
    set -e

    # Constants for output limiting
    MAX_EVENTS=25
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

    # Create output file
    formatted_output=$(create_temp_file)

    {
        if [ -z "$namespace" ] || [ -z "$pod_name" ]; then
            echo "❌ Both namespace and pod_name are required"
            exit 1
        fi

        echo "🔄 Pod Restart Analysis"
        echo "===================="

        # Get pod details before restart
        echo "📊 Current Pod State:"
        echo "=================="
        
        # Use kubectl_with_truncation for pod details
        cmd="kubectl get pod $pod_name -n $namespace -o json"
        if ! eval "$cmd" > "$(create_temp_file)"; then
            echo "❌ Failed to get pod details"
            exit 1
        fi
        
        # Analyze container states with truncation
        kubectl get pod $pod_name -n $namespace -o json | \
        jq -r '.status.containerStatuses[] | {
            name: .name,
            ready: .ready,
            restartCount: .restartCount,
            state: .state,
            lastState: .lastState
        }' | jq -r '. |
        "Container: \(.name)\n" +
        "Ready: \(.ready)\n" +
        "Restart Count: \(.restartCount)\n" +
        "Current State: \(.state | to_entries[0].key)\n" +
        if .lastState then
            "Last State: \(.lastState | to_entries[0].key)\n" +
            if .lastState[.lastState | to_entries[0].key].reason then
                "Last State Reason: \(.lastState[.lastState | to_entries[0].key].reason)\n"
            else "" end
        else "" end' | truncate_output "$MAX_ITEMS" "$MAX_OUTPUT_WIDTH"

        # Get recent related events
        echo -e "\n📜 Recent Related Events:"
        echo "====================="
        kubectl get events -n $namespace --field-selector involvedObject.name=$pod_name \
            --sort-by='.lastTimestamp' | \
        tail -n $MAX_EVENTS | \
        awk '{
            if ($7 ~ /Warning/) emoji="⚠️";
            else if ($7 ~ /Normal/) emoji="ℹ️";
            else emoji="📝";
            print "  " emoji " " $0;
        }'

        # Perform the restart
        echo -e "\n🔄 Restarting Pod..."
        if kubectl delete pod $pod_name -n $namespace; then
            echo "✅ Pod deletion initiated successfully"
            
            # Wait for new pod
            echo -e "\n⏳ Waiting for new pod..."
            kubectl wait --for=condition=ready pod -l app=$pod_name -n $namespace --timeout=60s || \
                echo "⚠️  Pod not ready within timeout period"
        else
            echo "❌ Failed to restart pod"
            exit 1
        fi

        # Show new pod state
        echo -e "\n📊 New Pod State:"
        echo "==============="
        kubectl get pod $pod_name -n $namespace -o wide | \
        awk 'NR==1 {print $0} NR>1 {
            status=$3;
            emoji="❓";
            if (status == "Running") emoji="✅";
            else if (status == "Pending") emoji="⏳";
            else if (status == "Succeeded") emoji="🎉";
            else if (status == "Failed") emoji="❌";
            print emoji " " $0;
        }'
    } > "$formatted_output"

    # Show output with line limit
    head -n $MAX_TOTAL_OUTPUT "$formatted_output"
    
    # Show truncation message if needed
    if [ "$(wc -l < "$formatted_output")" -gt "$MAX_TOTAL_OUTPUT" ]; then
        echo "⚠️  Output truncated. Use specific filters or actions to see more details."
    fi
    """,
    args=[
        Arg(
            name="namespace",
            type="str",
            description="Kubernetes namespace",
            required=True,
        ),
        Arg(
            name="pod_name",
            type="str",
            description="Name of the pod to restart",
            required=True,
        ),
    ],
)

pod_logs_tool = KubernetesTool(
    name="pod_logs",
    description="Advanced pod log analyzer with line range support, output limiting, and smart log formatting",
    content="""
    #!/bin/bash
    set -e

    # Constants for output limiting
    MAX_LOG_LINES=1000
    MAX_LOG_SIZE="10MB"
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

    # Function to format log line with timestamp and level highlighting
    format_log_line() {
        awk -v width="$MAX_OUTPUT_WIDTH" '
        function colorize(line, level) {
            if (level == "ERROR") return "\033[31m" line "\033[0m"     # Red
            if (level == "WARN") return "\033[33m" line "\033[0m"      # Yellow
            if (level == "INFO") return "\033[32m" line "\033[0m"      # Green
            if (level == "DEBUG") return "\033[36m" line "\033[0m"     # Cyan
            return line
        }
        {
            # Extract timestamp if present
            timestamp = ""
            if ($0 ~ /^[0-9]{4}-[0-9]{2}-[0-9]{2}/) {
                timestamp = substr($0, 1, 19)
                msg = substr($0, 21)
            } else {
                msg = $0
            }

            # Detect log level
            level = "NONE"
            if (tolower($0) ~ /error/) level = "ERROR"
            else if (tolower($0) ~ /warn/) level = "WARN"
            else if (tolower($0) ~ /info/) level = "INFO"
            else if (tolower($0) ~ /debug/) level = "DEBUG"

            # Truncate long lines
            if (length(msg) > width) {
                msg = substr(msg, 1, width-3) "..."
            }

            # Format output
            if (timestamp != "") {
                printf "🕒 %s | %s\n", timestamp, colorize(msg, level)
            } else {
                print colorize(msg, level)
            }
        }'
    }

    # Create output file
    formatted_output=$(create_temp_file)
    logs_file=$(create_temp_file)

    {
        if [ -z "$namespace" ] || [ -z "$pod_name" ]; then
            echo "❌ Both namespace and pod_name are required"
            exit 1
        fi

        # Get pod status first
        if ! kubectl get pod "$pod_name" -n "$namespace" >/dev/null 2>&1; then
            echo "❌ Pod '$pod_name' not found in namespace '$namespace'"
            exit 1
        fi

        echo "📜 Pod Logs Analysis"
        echo "=================="

        # Build kubectl logs command
        cmd="kubectl logs $pod_name -n $namespace"
        [ -n "${container:-}" ] && cmd="$cmd -c $container"
        [ -n "${since:-}" ] && cmd="$cmd --since=$since"
        [ -n "${tail:-}" ] && cmd="$cmd --tail=$tail"
        [ -n "${previous:-}" ] && cmd="$cmd --previous"

        # Get logs
        if ! $cmd > "$logs_file" 2>/dev/null; then
            if [ -n "${previous:-}" ]; then
                echo "❌ No previous logs available for pod '$pod_name'"
            else
                echo "❌ Failed to get logs for pod '$pod_name'"
            fi
            exit 1
        fi

        # Process logs based on line range if specified
        if [ -n "${start_line:-}" ] && [ -n "${end_line:-}" ]; then
            echo "📍 Showing lines $start_line to $end_line:"
            echo "--------------------------------"
            sed -n "${start_line},${end_line}p" "$logs_file" | format_log_line
        else
            # Show all logs with formatting
            cat "$logs_file" | format_log_line
        fi

        # Show log statistics
        total_lines=$(wc -l < "$logs_file")
        log_size=$(ls -lh "$logs_file" | awk '{print $5}')
        
        echo -e "\n📊 Log Statistics:"
        echo "================"
        echo "  📝 Total Lines: $total_lines"
        echo "  💾 Log Size: $log_size"
        
        # Show log level distribution
        echo -e "\n📈 Log Level Distribution:"
        echo "======================="
        {
            echo "  ❌ Errors: $(grep -ci "error" "$logs_file")"
            echo "  ⚠️  Warnings: $(grep -ci "warn" "$logs_file")"
            echo "  ℹ️  Info: $(grep -ci "info" "$logs_file")"
            echo "  🔍 Debug: $(grep -ci "debug" "$logs_file")"
        } | column -t
    } > "$formatted_output"

    # Show output with line limit
    if [ -n "${max_lines:-}" ]; then
        head -n "$max_lines" "$formatted_output"
    else
        head -n $MAX_TOTAL_OUTPUT "$formatted_output"
    fi
    
    # Show truncation message if needed
    if [ "$(wc -l < "$formatted_output")" -gt "${max_lines:-$MAX_TOTAL_OUTPUT}" ]; then
        echo "⚠️  Output truncated. Use --max-lines to adjust output limit or specify line range with --start-line and --end-line."
    fi
    """,
    args=[
        Arg(
            name="namespace",
            type="str",
            description="Kubernetes namespace",
            required=True,
        ),
        Arg(
            name="pod_name",
            type="str",
            description="Name of the pod",
            required=True,
        ),
        Arg(
            name="container",
            type="str",
            description="Container name (if pod has multiple containers)",
            required=False,
        ),
        Arg(
            name="since",
            type="str",
            description="Show logs since timestamp (e.g. 1h, 5m) or RFC3339 timestamp",
            required=False,
        ),
        Arg(
            name="previous",
            type="bool",
            description="Show logs from previous container instance",
            required=False,
        ),
        Arg(
            name="tail",
            type="int",
            description="Number of lines to show from the end",
            required=False,
        ),
        Arg(
            name="start_line",
            type="int",
            description="Start line number (must be used with end_line)",
            required=False,
        ),
        Arg(
            name="end_line",
            type="int",
            description="End line number (must be used with start_line)",
            required=False,
        ),
        Arg(
            name="max_lines",
            type="int",
            description="Maximum number of lines to show",
            required=False,
        ),
    ],
)

pod_network_topology_tool = KubernetesTool(
    name="pod_network_topology",
    description="Advanced pod network topology analyzer with detailed connectivity information",
    content="""
    #!/bin/bash
    set -e

    # Constants for output limiting
    MAX_ITEMS_PER_PAGE=10
    MAX_OUTPUT_WIDTH=120
    MAX_TOTAL_OUTPUT=5000
    MAX_CONNECTIONS=50

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
        echo "🌐 Pod Network Topology Analysis"
        echo "==========================="

        # Get pod information
        pod_file=$(create_temp_file)
        kubectl get pods $namespace_flag -o json > "$pod_file"

        # Analyze network policies
        echo "🔒 Network Policies:"
        echo "================="
        kubectl get networkpolicies $namespace_flag -o json | \
        jq -r '.items[] | {
            name: .metadata.name,
            namespace: .metadata.namespace,
            pod_selector: .spec.podSelector,
            ingress: .spec.ingress,
            egress: .spec.egress,
            policy_types: .spec.policyTypes
        }' | jq -r '. |
        "Policy: \(.name)\n" +
        "Namespace: \(.namespace)\n" +
        "Pod Selector: \(.pod_selector | tostring)\n" +
        "Policy Types: \(.policy_types | join(", "))\n" +
        "\nIngress Rules:" +
        if .ingress then
            (.ingress | map(
                "\n  • From:" +
                (if .[].from then
                    (.[].from | map(
                        if .namespaceSelector then "\n    - Namespace: \(.namespaceSelector)"
                        elif .podSelector then "\n    - Pod: \(.podSelector)"
                        elif .ipBlock then "\n    - IP Block: \(.ipBlock)"
                        else "\n    - Any"
                        end
                    ) | join(""))
                else "\n    - Any"
                end)
            ) | join("\n"))
        else "\n  None"
        end +
        "\n\nEgress Rules:" +
        if .egress then
            (.egress | map(
                "\n  • To:" +
                (if .[].to then
                    (.[].to | map(
                        if .namespaceSelector then "\n    - Namespace: \(.namespaceSelector)"
                        elif .podSelector then "\n    - Pod: \(.podSelector)"
                        elif .ipBlock then "\n    - IP Block: \(.ipBlock)"
                        else "\n    - Any"
                        end
                    ) | join(""))
                else "\n    - Any"
                end)
            ) | join("\n"))
        else "\n  None"
        end' | \
        awk '
        /^Policy:/ {printf "\n🛡️  %s\n", substr($0, 9)}
        /^Namespace:/ {printf "📁 %s\n", $0}
        /^Pod Selector:/ {printf "🎯 %s\n", $0}
        /^Policy Types:/ {printf "📋 %s\n", $0}
        /^Ingress Rules:/ {print "📥 Ingress Rules:"}
        /^Egress Rules:/ {print "📤 Egress Rules:"}
        /^  • From:/ {printf "  ⬅️  From:\n"}
        /^  • To:/ {printf "  ➡️  To:\n"}
        /^    -/ {printf "    %s\n", $0}
        ' > "$formatted_output"

        # Analyze service connections
        echo -e "\n🔌 Service Connections:"
        echo "===================="
        kubectl get services $namespace_flag -o json | \
        jq -r '.items[] | select(.spec.selector) | {
            name: .metadata.name,
            namespace: .metadata.namespace,
            selector: .spec.selector,
            ports: .spec.ports
        }' | jq -r '. |
        "Service: \(.name)\n" +
        "Namespace: \(.namespace)\n" +
        "Selector: \(.selector | to_entries | map("\(.key)=\(.value)") | join(", "))\n" +
        "Ports: \(.ports | map("\(.port):\(.targetPort) (\(.protocol))") | join(", ")))"' | \
        awk '
        /^Service:/ {printf "\n🔌 %s\n", substr($0, 10)}
        /^Namespace:/ {printf "📁 %s\n", $0}
        /^Selector:/ {printf "🎯 %s\n", $0}
        /^Ports:/ {printf "🔌 %s\n", $0}
        ' >> "$formatted_output"

        # Show pod-to-pod connections based on labels
        echo -e "\n🔗 Pod-to-Pod Connections:"
        echo "======================="
        jq -r '.items[] | select(.metadata.labels) | {
            name: .metadata.name,
            namespace: .metadata.namespace,
            labels: .metadata.labels,
            ip: .status.podIP
        }' "$pod_file" | \
        jq -r '. |
        "Pod: \(.name)\n" +
        "Namespace: \(.namespace)\n" +
        "IP: \(.ip)\n" +
        "Labels: \(.labels | to_entries | map("\(.key)=\(.value)") | join(", "))"' | \
        awk '
        /^Pod:/ {printf "\n📦 %s\n", substr($0, 6)}
        /^Namespace:/ {printf "📁 %s\n", $0}
        /^IP:/ {printf "🌐 %s\n", $0}
        /^Labels:/ {printf "🏷️  %s\n", $0}
        ' >> "$formatted_output"

        # Calculate statistics
        total_policies=$(kubectl get networkpolicies $namespace_flag -o json | jq '.items | length')
        total_services=$(kubectl get services $namespace_flag -o json | jq '.items | length')
        total_pods=$(jq '.items | length' "$pod_file")
        
        echo -e "\n📊 Network Statistics:"
        echo "==================="
        echo "  🛡️  Network Policies: $total_policies"
        echo "  🔌 Services: $total_services"
        echo "  📦 Pods: $total_pods"
    } >> "$formatted_output"

    # Show output with line limit
    head -n $MAX_TOTAL_OUTPUT "$formatted_output"
    
    # Show truncation message if needed
    if [ "$(wc -l < "$formatted_output")" -gt "$MAX_TOTAL_OUTPUT" ]; then
        echo "⚠️  Output truncated. Use --page to view more details."
    fi
    """,
    args=[
        Arg(
            name="namespace",
            type="str",
            description="Kubernetes namespace. If omitted, analyzes all namespaces",
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
for tool in [pod_restart_tool, pod_logs_tool, pod_network_topology_tool]:
    tool_registry.register("kubernetes", tool)